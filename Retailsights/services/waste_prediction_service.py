"""
AI-Powered Waste Prediction Service
Predicts future waste based on historical patterns, seasonal trends, and external factors.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from ..db import get_connection
from ..logger import logger

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available. Waste prediction will use simple models.")


class WastePredictionService:
    """ML-powered waste prediction and prevention recommendations."""
    
    @staticmethod
    def get_historical_waste_data(shop_id: int, days: int = 90) -> pd.DataFrame:
        """Fetch historical waste data with enriched features."""
        conn = get_connection()
        try:
            query = """
                SELECT 
                    w.created_at,
                    w.product_id,
                    w.quantity_wasted,
                    w.reason,
                    p.sku,
                    p.name as product_name,
                    p.category,
                    p.cost_price,
                    p.default_price as selling_price,
                    e.expiry_date,
                    e.days_left,
                    e.quantity_remaining,
                    DAYOFWEEK(w.created_at) as day_of_week,
                    WEEK(w.created_at) as week_of_year,
                    MONTH(w.created_at) as month
                FROM waste_records w
                JOIN products p ON w.product_id = p.id
                LEFT JOIN expiry_records e ON w.expiry_record_id = e.id
                WHERE p.shop_id = %s 
                  AND w.created_at >= NOW() - INTERVAL '%s days'
                ORDER BY w.created_at DESC
            """
            df = pd.read_sql(query, conn, params=(shop_id, days))
            return df
        except Exception as e:
            logger.error(f"get_historical_waste_data error: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    @staticmethod
    def get_sales_velocity_data(shop_id: int, days: int = 30) -> pd.DataFrame:
        """Get product sales velocity to predict stock that won't sell."""
        conn = get_connection()
        try:
            query = """
                SELECT 
                    p.id as product_id,
                    p.sku,
                    p.name,
                    p.category,
                    COUNT(DISTINCT s.id) as transaction_count,
                    SUM(sl.quantity) as total_units_sold,
                    AVG(sl.quantity) as avg_units_per_transaction,
                    MAX(s.created_at) as last_sale_date,
                    DATEDIFF(NOW(), MAX(s.created_at)) as days_since_last_sale
                FROM products p
                LEFT JOIN sales_lines sl ON p.id = sl.product_id
                LEFT JOIN sales s ON sl.sale_id = s.id
                WHERE p.shop_id = %s
                  AND (s.created_at IS NULL OR s.created_at >= NOW() - INTERVAL '%s days')
                GROUP BY p.id, p.sku, p.name, p.category
            """
            df = pd.read_sql(query, conn, params=(shop_id, days))
            return df
        except Exception as e:
            logger.error(f"get_sales_velocity_data error: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    @staticmethod
    def predict_waste_next_week(shop_id: int) -> Dict[str, Any]:
        """Predict waste for the next 7 days using ML models."""
        
        # Get historical data
        waste_df = WastePredictionService.get_historical_waste_data(shop_id, days=180)
        
        if waste_df.empty or len(waste_df) < 30:
            return {
                "prediction_available": False,
                "message": "Insufficient historical data (need 30+ waste records)",
                "predicted_waste_units": 0,
                "predicted_waste_cost": 0.0,
                "confidence": 0.0
            }
        
        # Aggregate by day
        daily_waste = waste_df.groupby(waste_df['created_at'].dt.date).agg({
            'quantity_wasted': 'sum',
            'cost_price': 'sum'
        }).reset_index()
        daily_waste.columns = ['date', 'units', 'cost']
        
        if SKLEARN_AVAILABLE and len(daily_waste) >= 30:
            # Use ML model
            return WastePredictionService._ml_prediction(daily_waste)
        else:
            # Use simple moving average
            return WastePredictionService._simple_prediction(daily_waste)
    
    @staticmethod
    def _ml_prediction(daily_waste: pd.DataFrame) -> Dict[str, Any]:
        """ML-based prediction using Random Forest."""
        try:
            # Feature engineering
            daily_waste['date'] = pd.to_datetime(daily_waste['date'])
            daily_waste = daily_waste.sort_values('date')
            
            # Create features
            daily_waste['day_of_week'] = daily_waste['date'].dt.dayofweek
            daily_waste['week_of_year'] = daily_waste['date'].dt.isocalendar().week
            daily_waste['month'] = daily_waste['date'].dt.month
            daily_waste['day_of_month'] = daily_waste['date'].dt.day
            
            # Lagged features
            daily_waste['units_lag_1'] = daily_waste['units'].shift(1)
            daily_waste['units_lag_7'] = daily_waste['units'].shift(7)
            daily_waste['units_ma_7'] = daily_waste['units'].rolling(window=7, min_periods=1).mean()
            
            # Drop NaN
            daily_waste = daily_waste.dropna()
            
            if len(daily_waste) < 20:
                return WastePredictionService._simple_prediction(daily_waste)
            
            # Prepare features
            feature_cols = ['day_of_week', 'week_of_year', 'month', 'day_of_month', 
                          'units_lag_1', 'units_lag_7', 'units_ma_7']
            X = daily_waste[feature_cols]
            y = daily_waste['units']
            
            # Train model
            model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
            model.fit(X, y)
            
            # Predict next 7 days
            last_date = daily_waste['date'].max()
            predictions = []
            
            for i in range(1, 8):
                future_date = last_date + timedelta(days=i)
                features = {
                    'day_of_week': future_date.dayofweek,
                    'week_of_year': future_date.isocalendar().week,
                    'month': future_date.month,
                    'day_of_month': future_date.day,
                    'units_lag_1': daily_waste['units'].iloc[-1] if i == 1 else predictions[-1],
                    'units_lag_7': daily_waste['units'].iloc[-7] if len(daily_waste) >= 7 else daily_waste['units'].mean(),
                    'units_ma_7': daily_waste['units'].tail(7).mean()
                }
                X_pred = pd.DataFrame([features])
                pred = model.predict(X_pred)[0]
                predictions.append(max(0, pred))  # No negative waste
            
            total_predicted_units = sum(predictions)
            avg_cost_per_unit = daily_waste['cost'].sum() / daily_waste['units'].sum() if daily_waste['units'].sum() > 0 else 0
            predicted_cost = total_predicted_units * avg_cost_per_unit
            
            # Calculate confidence (based on model R² score)
            from sklearn.metrics import r2_score
            y_pred = model.predict(X)
            confidence = max(0, min(100, r2_score(y, y_pred) * 100))
            
            return {
                "prediction_available": True,
                "method": "Random Forest ML",
                "predicted_waste_units": round(total_predicted_units, 1),
                "predicted_waste_cost": round(predicted_cost, 2),
                "confidence": round(confidence, 1),
                "daily_predictions": [round(p, 1) for p in predictions],
                "feature_importance": dict(zip(feature_cols, model.feature_importances_.tolist()))
            }
            
        except Exception as e:
            logger.error(f"ML prediction error: {e}")
            return WastePredictionService._simple_prediction(daily_waste)
    
    @staticmethod
    def _simple_prediction(daily_waste: pd.DataFrame) -> Dict[str, Any]:
        """Simple moving average prediction."""
        recent_units = daily_waste['units'].tail(14).mean()
        recent_cost = daily_waste['cost'].tail(14).mean()
        
        predicted_units = recent_units * 7
        predicted_cost = recent_cost * 7
        
        return {
            "prediction_available": True,
            "method": "14-day moving average",
            "predicted_waste_units": round(predicted_units, 1),
            "predicted_waste_cost": round(predicted_cost, 2),
            "confidence": 60.0,
            "daily_predictions": [round(recent_units, 1)] * 7
        }
    
    @staticmethod
    def get_high_risk_products(shop_id: int, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Identify products with high waste risk (>30% waste rate)."""
        conn = get_connection()
        try:
            query = """
                SELECT 
                    p.id,
                    p.sku,
                    p.name,
                    p.category,
                    COUNT(DISTINCT e.id) as total_batches,
                    SUM(CASE WHEN e.status = 'inactive' AND e.quantity_remaining > 0 THEN 1 ELSE 0 END) as wasted_batches,
                    SUM(w.quantity_wasted) as total_wasted_units,
                    SUM(e.quantity_remaining + COALESCE(w.quantity_wasted, 0)) as total_units_received,
                    (SUM(COALESCE(w.quantity_wasted, 0)) / NULLIF(SUM(e.quantity_remaining + COALESCE(w.quantity_wasted, 0)), 0)) as waste_rate,
                    SUM(w.quantity_wasted * p.cost_price) as total_waste_cost,
                    AVG(e.days_left) as avg_shelf_life
                FROM products p
                JOIN expiry_records e ON p.id = e.product_id
                LEFT JOIN waste_records w ON e.id = w.expiry_record_id
                WHERE p.shop_id = %s
                  AND e.created_at >= NOW() - INTERVAL '90 days'
                GROUP BY p.id, p.sku, p.name, p.category, p.cost_price
                HAVING waste_rate > %s
                ORDER BY waste_rate DESC, total_waste_cost DESC
                LIMIT 20
            """
            df = pd.read_sql(query, conn, params=(shop_id, threshold))
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"get_high_risk_products error: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def get_prevention_recommendations(shop_id: int) -> List[Dict[str, Any]]:
        """Generate actionable recommendations to reduce waste."""
        recommendations = []
        
        # Get high-risk products
        high_risk = WastePredictionService.get_high_risk_products(shop_id)
        
        if high_risk:
            for product in high_risk[:5]:
                waste_rate = product.get('waste_rate', 0) * 100
                rec = {
                    "priority": "HIGH" if waste_rate > 50 else "MEDIUM",
                    "product_sku": product['sku'],
                    "product_name": product['name'],
                    "issue": f"{waste_rate:.1f}% waste rate",
                    "recommendations": []
                }
                
                # Specific recommendations based on waste rate
                if waste_rate > 50:
                    rec["recommendations"].append("⚠️ CRITICAL: Reduce order quantity by 50%")
                    rec["recommendations"].append("Apply discount at 14+ days before expiry")
                elif waste_rate > 30:
                    rec["recommendations"].append("⚠️ Reduce order quantity by 30%")
                    rec["recommendations"].append("Apply discount at 10+ days before expiry")
                
                # Shelf life recommendations
                avg_shelf_life = product.get('avg_shelf_life', 0)
                if avg_shelf_life < 7:
                    rec["recommendations"].append("Short shelf life: Order smaller batches more frequently")
                
                recommendations.append(rec)
        
        # Check for slow-moving products
        velocity_df = WastePredictionService.get_sales_velocity_data(shop_id, days=30)
        if not velocity_df.empty:
            slow_movers = velocity_df[velocity_df['days_since_last_sale'] > 14].head(5)
            for _, product in slow_movers.iterrows():
                rec = {
                    "priority": "MEDIUM",
                    "product_sku": product['sku'],
                    "product_name": product['name'],
                    "issue": f"No sales in {product['days_since_last_sale']} days",
                    "recommendations": [
                        "Consider discontinuing this product",
                        "Run promotional campaign to clear stock",
                        "Bundle with faster-moving items"
                    ]
                }
                recommendations.append(rec)
        
        return recommendations[:10]  # Top 10 recommendations
    
    @staticmethod
    def get_waste_by_category(shop_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Analyze waste patterns by product category."""
        conn = get_connection()
        try:
            query = """
                SELECT 
                    p.category,
                    COUNT(DISTINCT w.id) as waste_events,
                    SUM(w.quantity_wasted) as total_units_wasted,
                    SUM(w.quantity_wasted * p.cost_price) as total_waste_cost,
                    AVG(e.days_left) as avg_days_left_when_wasted
                FROM waste_records w
                JOIN products p ON w.product_id = p.id
                LEFT JOIN expiry_records e ON w.expiry_record_id = e.id
                WHERE p.shop_id = %s
                  AND w.created_at >= NOW() - INTERVAL '%s days'
                GROUP BY p.category
                ORDER BY total_waste_cost DESC
            """
            df = pd.read_sql(query, conn, params=(shop_id, days))
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"get_waste_by_category error: {e}")
            return []
        finally:
            conn.close()
