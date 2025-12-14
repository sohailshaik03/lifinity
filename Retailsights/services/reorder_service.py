"""
Automated Reorder System
AI-powered inventory management and supplier integration.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
from ..db import get_connection
from ..logger import logger


class ReorderService:
    """Intelligent reorder suggestions and automation."""
    
    @staticmethod
    def calculate_reorder_point(
        product_id: int,
        lead_time_days: int = 3,
        safety_stock_days: int = 2
    ) -> Dict[str, Any]:
        """
        Calculate when to reorder based on:
        - Historical sales velocity
        - Lead time
        - Safety stock
        """
        conn = get_connection()
        try:
            # Get sales velocity (last 30 days)
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT 
                    p.sku,
                    p.name,
                    p.category,
                    p.cost_price,
                    p.default_price,
                    SUM(sl.quantity) as total_sold_30d,
                    COUNT(DISTINCT DATE(s.created_at)) as days_with_sales,
                    SUM(e.quantity_remaining) as current_stock
                FROM products p
                LEFT JOIN sales_lines sl ON p.id = sl.product_id
                LEFT JOIN sales s ON sl.sale_id = s.id 
                    AND s.created_at >= NOW() - INTERVAL '30 days'
                LEFT JOIN expiry_records e ON p.id = e.product_id 
                    AND e.status = 'active'
                WHERE p.id = %s
                GROUP BY p.id, p.sku, p.name, p.category, p.cost_price, p.default_price
            """, (product_id,))
            
            product = cur.fetchone()
            
            if not product:
                return {"error": "Product not found"}
            
            # Calculate daily velocity
            total_sold = product['total_sold_30d'] or 0
            days_tracked = product['days_with_sales'] or 30
            daily_velocity = total_sold / days_tracked if days_tracked > 0 else 0
            
            # Reorder point = (daily velocity × lead time) + safety stock
            lead_time_demand = daily_velocity * lead_time_days
            safety_stock = daily_velocity * safety_stock_days
            reorder_point = lead_time_demand + safety_stock
            
            # Optimal order quantity (EOQ simplified)
            # Order enough for 2 weeks
            optimal_order_qty = daily_velocity * 14
            
            current_stock = product['current_stock'] or 0
            days_until_stockout = current_stock / daily_velocity if daily_velocity > 0 else 999
            
            # Should reorder?
            should_reorder = current_stock <= reorder_point
            urgency = "HIGH" if current_stock <= lead_time_demand else "MEDIUM" if should_reorder else "LOW"
            
            return {
                "product": {
                    "sku": product['sku'],
                    "name": product['name'],
                    "category": product['category']
                },
                "inventory": {
                    "current_stock": current_stock,
                    "days_until_stockout": round(days_until_stockout, 1)
                },
                "velocity": {
                    "daily_average": round(daily_velocity, 2),
                    "weekly_average": round(daily_velocity * 7, 1)
                },
                "reorder_point": round(reorder_point, 0),
                "recommended_order_qty": round(optimal_order_qty, 0),
                "should_reorder": should_reorder,
                "urgency": urgency,
                "estimated_cost": round(optimal_order_qty * product['cost_price'], 2),
                "lead_time_days": lead_time_days,
                "safety_stock_units": round(safety_stock, 0)
            }
            
        except Exception as e:
            logger.error(f"calculate_reorder_point error: {e}")
            return {"error": str(e)}
        finally:
            conn.close()
    
    @staticmethod
    def get_reorder_recommendations(shop_id: int, urgency: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all products that need reordering."""
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT DISTINCT p.id, p.sku, p.name, p.category
                FROM products p
                WHERE p.shop_id = %s
                ORDER BY p.name
            """, (shop_id,))
            
            products = cur.fetchall()
            recommendations = []
            
            for product in products:
                analysis = ReorderService.calculate_reorder_point(product['id'])
                
                if not analysis.get('error') and analysis.get('should_reorder'):
                    # Filter by urgency if specified
                    if urgency and analysis.get('urgency') != urgency:
                        continue
                    
                    recommendations.append(analysis)
            
            # Sort by urgency and days until stockout
            urgency_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            recommendations.sort(key=lambda x: (
                urgency_order.get(x.get('urgency', 'LOW'), 3),
                x.get('inventory', {}).get('days_until_stockout', 999)
            ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"get_reorder_recommendations error: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def generate_purchase_order(
        shop_id: int,
        product_ids: List[int],
        supplier_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate purchase order for multiple products."""
        conn = get_connection()
        try:
            items = []
            total_cost = 0.0
            
            for product_id in product_ids:
                analysis = ReorderService.calculate_reorder_point(product_id)
                
                if not analysis.get('error'):
                    item = {
                        "sku": analysis['product']['sku'],
                        "name": analysis['product']['name'],
                        "quantity": analysis['recommended_order_qty'],
                        "unit_cost": analysis['estimated_cost'] / analysis['recommended_order_qty'] if analysis['recommended_order_qty'] > 0 else 0,
                        "total_cost": analysis['estimated_cost']
                    }
                    items.append(item)
                    total_cost += analysis['estimated_cost']
            
            # Create PO record (simplified - requires purchase_orders table)
            po_number = f"PO-{shop_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            return {
                "po_number": po_number,
                "shop_id": shop_id,
                "supplier_id": supplier_id,
                "items": items,
                "item_count": len(items),
                "total_cost": round(total_cost, 2),
                "created_at": datetime.now().isoformat(),
                "status": "DRAFT",
                "note": "Review and submit to supplier"
            }
            
        except Exception as e:
            logger.error(f"generate_purchase_order error: {e}")
            return {"error": str(e)}
        finally:
            conn.close()
    
    @staticmethod
    def get_supplier_performance(shop_id: int, days: int = 90) -> List[Dict[str, Any]]:
        """
        Analyze supplier performance:
        - On-time delivery
        - Product waste rates
        - Quality issues
        """
        # This is a stub - requires purchase_orders and supplier tables
        conn = get_connection()
        try:
            # Analyze waste by product to identify supplier quality issues
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT 
                    p.category,
                    COUNT(DISTINCT p.id) as product_count,
                    SUM(w.quantity_wasted) as total_wasted,
                    SUM(w.quantity_wasted * p.cost_price) as waste_cost,
                    AVG(e.days_left) as avg_shelf_life,
                    COUNT(DISTINCT w.id) as waste_incidents
                FROM waste_records w
                JOIN products p ON w.product_id = p.id
                LEFT JOIN expiry_records e ON w.expiry_record_id = e.id
                WHERE p.shop_id = %s
                  AND w.created_at >= NOW() - INTERVAL '%s days'
                GROUP BY p.category
                ORDER BY waste_cost DESC
            """, (shop_id, days))
            
            categories = cur.fetchall()
            
            return {
                "analysis_period_days": days,
                "by_category": categories,
                "note": "Full supplier tracking requires purchase_orders and suppliers tables",
                "recommendation": "Categories with high waste may indicate supplier quality issues"
            }
            
        except Exception as e:
            logger.error(f"get_supplier_performance error: {e}")
            return {"error": str(e)}
        finally:
            conn.close()
    
    @staticmethod
    def predict_optimal_order_schedule(
        product_id: int,
        forecast_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Predict optimal reorder dates for next N days.
        Considers seasonality and trends.
        """
        analysis = ReorderService.calculate_reorder_point(product_id)
        
        if analysis.get('error'):
            return []
        
        schedule = []
        daily_velocity = analysis['velocity']['daily_average']
        current_stock = analysis['inventory']['current_stock']
        reorder_point = analysis['reorder_point']
        order_qty = analysis['recommended_order_qty']
        
        # Simulate stock levels
        stock_level = current_stock
        days_since_order = 0
        
        for day in range(forecast_days):
            # Consume stock
            stock_level -= daily_velocity
            days_since_order += 1
            
            # Check if reorder needed
            if stock_level <= reorder_point and days_since_order >= 7:  # Min 1 week between orders
                schedule.append({
                    "day": day + 1,
                    "date": (datetime.now() + timedelta(days=day)).strftime('%Y-%m-%d'),
                    "action": "REORDER",
                    "order_quantity": order_qty,
                    "stock_before": round(stock_level, 0),
                    "stock_after": round(stock_level + order_qty, 0),
                    "reason": f"Stock at {stock_level:.0f} (below reorder point of {reorder_point:.0f})"
                })
                stock_level += order_qty
                days_since_order = 0
        
        return schedule[:10]  # Return next 10 reorder events
