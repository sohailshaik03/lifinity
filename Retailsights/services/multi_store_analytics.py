"""
Multi-Store Analytics Service
Compare performance across stores, identify best practices, and detect anomalies.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd
from datetime import datetime, timedelta
from ..db import get_connection
from ..logger import logger


class MultiStoreAnalytics:
    """Enterprise-level multi-store comparison and analytics."""
    
    @staticmethod
    def get_all_stores_overview() -> List[Dict[str, Any]]:
        """Get high-level KPIs for all stores."""
        conn = get_connection()
        try:
            query = """
                SELECT 
                    s.id,
                    s.name as store_name,
                    CONCAT(COALESCE(s.city, ''), ', ', COALESCE(s.country, '')) as location,
                    COUNT(DISTINCT p.id) as total_products,
                    COALESCE(staff_count.total_staff, 0) as staff_count,
                    COALESCE(revenue.total_revenue_7d, 0) as revenue_last_7_days,
                    COALESCE(waste.total_waste_units_30d, 0) as waste_units_last_30_days,
                    COALESCE(waste.total_waste_cost_30d, 0) as waste_cost_last_30_days,
                    COALESCE(markdown.markdown_count_7d, 0) as markdown_sales_7d,
                    COALESCE(markdown.markdown_revenue_7d, 0) as markdown_revenue_7d,
                    s.created_at as store_opened_date
                FROM shops s
                LEFT JOIN products p ON s.id = p.shop_id
                LEFT JOIN (
                    SELECT shop_id, COUNT(DISTINCT user_id) as total_staff
                    FROM user_shops
                    GROUP BY shop_id
                ) staff_count ON s.id = staff_count.shop_id
                LEFT JOIN (
                    SELECT 
                        p.shop_id,
                        SUM(sl.quantity * sl.unit_price) as total_revenue_7d
                    FROM sales_lines sl
                    JOIN sales_transactions sa ON sl.transaction_id = sa.id
                    JOIN products p ON sl.product_id = p.id
                    WHERE sa.transaction_dt >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    GROUP BY p.shop_id
                ) revenue ON s.id = revenue.shop_id
                LEFT JOIN (
                    SELECT 
                        p.shop_id,
                        SUM(w.quantity_wasted) as total_waste_units_30d,
                        SUM(w.quantity_wasted * COALESCE(p.default_cost, 0)) as total_waste_cost_30d
                    FROM waste_records w
                    JOIN products p ON w.product_id = p.id
                    WHERE w.recorded_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                    GROUP BY p.shop_id
                ) waste ON s.id = waste.shop_id
                LEFT JOIN (
                    SELECT 
                        shop_id,
                        COUNT(*) as markdown_count_7d,
                        SUM(discounted_price * quantity_sold) as markdown_revenue_7d
                    FROM markdown_sales
                    WHERE sold_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                    GROUP BY shop_id
                ) markdown ON s.id = markdown.shop_id
                GROUP BY s.id, s.name, s.city, s.country, s.created_at, 
                         staff_count.total_staff,
                         revenue.total_revenue_7d, waste.total_waste_units_30d, waste.total_waste_cost_30d,
                         markdown.markdown_count_7d, markdown.markdown_revenue_7d
                ORDER BY revenue_last_7_days DESC
            """
            df = pd.read_sql(query, conn)
            
            # Calculate derived metrics
            for idx, row in df.iterrows():
                revenue = row['revenue_last_7_days']
                waste_cost = row['waste_cost_last_30_days']
                
                # Waste as % of revenue (annualized for comparison)
                revenue_30d = revenue * 4.3  # Approximate monthly
                df.loc[idx, 'waste_as_pct_revenue'] = (waste_cost / revenue_30d * 100) if revenue_30d > 0 else 0
                
                # Efficiency score (0-100)
                efficiency = 100
                if revenue > 0:
                    efficiency -= min(50, (waste_cost / revenue_30d) * 1000)  # Waste penalty
                df.loc[idx, 'efficiency_score'] = max(0, efficiency)
            
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"get_all_stores_overview error: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def compare_stores(store_ids: List[int], days: int = 30) -> Dict[str, Any]:
        """Deep comparison between specific stores."""
        conn = get_connection()
        try:
            placeholders = ','.join(['%s'] * len(store_ids))
            query = f"""
                SELECT 
                    s.id as store_id,
                    s.name as store_name,
                    COUNT(DISTINCT p.id) as product_count,
                    COUNT(DISTINCT sa.id) as transaction_count,
                    SUM(sl.quantity * sl.unit_price) as total_revenue,
                    AVG(sl.quantity * sl.unit_price) as avg_transaction_value,
                    SUM(sl.quantity) as units_sold,
                    COUNT(DISTINCT DATE(sa.created_at)) as days_with_sales,
                    SUM(w.quantity_wasted) as units_wasted,
                    SUM(w.quantity_wasted * p.cost_price) as waste_cost
                FROM shops s
                LEFT JOIN products p ON s.id = p.shop_id
                LEFT JOIN sales_lines sl ON p.id = sl.product_id
                LEFT JOIN sales_transactions sa ON sl.transaction_id = sa.id AND sa.transaction_dt >= DATE_SUB(NOW(), INTERVAL %s DAY)
                LEFT JOIN waste_records w ON p.id = w.product_id AND w.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                WHERE s.id IN ({placeholders})
                GROUP BY s.id, s.name
            """
            params = [days, days] + store_ids
            df = pd.read_sql(query, conn, params=params)
            
            # Calculate additional metrics
            df['daily_revenue'] = df['total_revenue'] / days
            df['waste_rate_pct'] = (df['units_wasted'] / (df['units_sold'] + df['units_wasted']) * 100).fillna(0)
            df['revenue_per_product'] = (df['total_revenue'] / df['product_count']).fillna(0)
            
            comparison = {
                "stores": df.to_dict('records'),
                "summary": {
                    "best_revenue": df.loc[df['total_revenue'].idxmax()].to_dict() if len(df) > 0 else {},
                    "lowest_waste": df.loc[df['waste_rate_pct'].idxmin()].to_dict() if len(df) > 0 else {},
                    "highest_efficiency": df.loc[df['revenue_per_product'].idxmax()].to_dict() if len(df) > 0 else {}
                }
            }
            
            return comparison
        except Exception as e:
            logger.error(f"compare_stores error: {e}")
            return {"stores": [], "summary": {}}
        finally:
            conn.close()
    
    @staticmethod
    def get_regional_performance(days: int = 30) -> List[Dict[str, Any]]:
        """Aggregate performance by region/location."""
        conn = get_connection()
        try:
            query = """
                SELECT 
                    COALESCE(s.city, 'Unknown') as region,
                    COUNT(DISTINCT s.id) as store_count,
                    SUM(revenue.total_revenue) as total_revenue,
                    AVG(revenue.total_revenue) as avg_revenue_per_store,
                    SUM(waste.waste_cost) as total_waste_cost,
                    AVG(waste.waste_cost) as avg_waste_per_store
                FROM shops s
                LEFT JOIN (
                    SELECT 
                        p.shop_id,
                        SUM(sl.quantity * sl.unit_price) as total_revenue
                    FROM sales_lines sl
                    JOIN sales_transactions sa ON sl.transaction_id = sa.id
                    JOIN products p ON sl.product_id = p.id
                    WHERE sa.transaction_dt >= DATE_SUB(NOW(), INTERVAL %s DAY)
                    GROUP BY p.shop_id
                ) revenue ON s.id = revenue.shop_id
                LEFT JOIN (
                    SELECT 
                        p.shop_id,
                        SUM(w.quantity_wasted * p.cost_price) as waste_cost
                    FROM waste_records w
                    JOIN products p ON w.product_id = p.id
                    WHERE w.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                    GROUP BY p.shop_id
                ) waste ON s.id = waste.shop_id
                WHERE s.city IS NOT NULL AND s.city != ''
                GROUP BY s.city
                ORDER BY total_revenue DESC
            """
            df = pd.read_sql(query, conn, params=(days, days))
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"get_regional_performance error: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def detect_anomalies(shop_id: int) -> List[Dict[str, Any]]:
        """Detect unusual patterns that need attention."""
        anomalies = []
        conn = get_connection()
        
        try:
            # Check for sudden revenue drop
            query = """
                SELECT 
                    DATE(sa.transaction_dt) as date,
                    SUM(sl.quantity * sl.unit_price) as daily_revenue
                FROM sales_transactions sa
                JOIN sales_lines sl ON sa.id = sl.transaction_id
                JOIN products p ON sl.product_id = p.id
                WHERE p.shop_id = %s
                  AND sa.transaction_dt >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                GROUP BY DATE(sa.transaction_dt)
                ORDER BY date DESC
            """
            df = pd.read_sql(query, conn, params=(shop_id,))
            
            if len(df) >= 7:
                recent_avg = df.head(3)['daily_revenue'].mean()
                historical_avg = df.tail(14)['daily_revenue'].mean()
                
                if recent_avg < historical_avg * 0.7:  # 30% drop
                    anomalies.append({
                        "type": "REVENUE_DROP",
                        "severity": "HIGH",
                        "message": f"Revenue dropped 30%+ in last 3 days (£{recent_avg:.2f} vs £{historical_avg:.2f})",
                        "recommendation": "Check: staffing issues, competitor activity, or system downtime"
                    })
            
            # Check for unusual waste spike
            query = """
                SELECT 
                    DATE(created_at) as date,
                    SUM(quantity_wasted) as daily_waste,
                    COUNT(*) as waste_events
                FROM waste_records w
                JOIN products p ON w.product_id = p.id
                WHERE p.shop_id = %s
                  AND w.created_at >= DATE_SUB(NOW(), INTERVAL 14 DAY)
                GROUP BY DATE(created_at)
            """
            df_waste = pd.read_sql(query, conn, params=(shop_id,))
            
            if len(df_waste) >= 7:
                recent_waste = df_waste.head(2)['daily_waste'].mean()
                historical_waste = df_waste.tail(7)['daily_waste'].mean()
                
                if recent_waste > historical_waste * 1.5:  # 50% increase
                    anomalies.append({
                        "type": "WASTE_SPIKE",
                        "severity": "MEDIUM",
                        "message": f"Waste increased 50%+ in last 2 days ({recent_waste:.0f} vs {historical_waste:.0f} units)",
                        "recommendation": "Check: refrigeration, supplier quality, or overstocking"
                    })
            
            # Check for products with zero sales in 14+ days
            query = """
                SELECT 
                    p.sku,
                    p.name,
                    MAX(sa.created_at) as last_sale,
                    DATEDIFF(NOW(), MAX(sa.created_at)) as days_no_sale,
                    SUM(e.quantity_remaining) as current_stock
                FROM products p
                LEFT JOIN sales_lines sl ON p.id = sl.product_id
                LEFT JOIN sales sa ON sl.sale_id = sa.id
                LEFT JOIN expiry_records e ON p.id = e.product_id AND e.status = 'active'
                WHERE p.shop_id = %s
                GROUP BY p.id, p.sku, p.name
                HAVING days_no_sale > 14 AND current_stock > 0
                ORDER BY days_no_sale DESC
                LIMIT 5
            """
            df_dead = pd.read_sql(query, conn, params=(shop_id,))
            
            if len(df_dead) > 0:
                anomalies.append({
                    "type": "DEAD_STOCK",
                    "severity": "MEDIUM",
                    "message": f"{len(df_dead)} products with no sales in 14+ days",
                    "products": df_dead['sku'].tolist()[:3],
                    "recommendation": "Apply heavy discount or remove from inventory"
                })
            
        except Exception as e:
            logger.error(f"detect_anomalies error: {e}")
        finally:
            conn.close()
        
        return anomalies
    
    @staticmethod
    def get_staff_performance(shop_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Track staff performance metrics."""
        conn = get_connection()
        try:
            query = """
                SELECT 
                    u.id as user_id,
                    u.username,
                    u.role,
                    COUNT(DISTINCT ms.id) as markdown_sales_count,
                    SUM(ms.quantity_sold) as total_markdown_units,
                    SUM(ms.discount_amount * ms.quantity_sold) as total_discount_given,
                    SUM(ms.discounted_price * ms.quantity_sold) as markdown_revenue,
                    COUNT(DISTINCT w.id) as waste_logged_count,
                    SUM(w.quantity_wasted) as total_waste_logged
                FROM users u
                LEFT JOIN markdown_sales ms ON u.id = ms.sold_by 
                    AND ms.sold_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                LEFT JOIN waste_records w ON u.id = w.recorded_by 
                    AND w.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                WHERE u.shop_id = %s
                GROUP BY u.id, u.username, u.role
                HAVING markdown_sales_count > 0 OR waste_logged_count > 0
                ORDER BY markdown_revenue DESC
            """
            df = pd.read_sql(query, conn, params=(days, days, shop_id))
            
            # Calculate efficiency score
            for idx, row in df.iterrows():
                score = 100
                # Positive: markdown sales (converting waste to revenue)
                score += min(30, row['markdown_sales_count'] * 0.5)
                # Negative: waste logged (but good they're logging it)
                score -= min(20, row['waste_logged_count'] * 0.3)
                df.loc[idx, 'performance_score'] = round(min(130, max(50, score)), 1)
            
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"get_staff_performance error: {e}")
            return []
        finally:
            conn.close()
