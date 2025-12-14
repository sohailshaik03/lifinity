"""
Customer-Facing API
RESTful API for customer apps, loyalty programs, and third-party integrations.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from ..db import get_connection
from ..logger import logger
import hashlib
import secrets


class CustomerAPIService:
    """API endpoints for customer-facing applications."""
    
    @staticmethod
    def generate_api_key(customer_id: int) -> str:
        """Generate secure API key for customer authentication."""
        timestamp = str(datetime.now().timestamp())
        random = secrets.token_hex(16)
        data = f"{customer_id}:{timestamp}:{random}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def get_yellow_sticker_products(
        shop_id: int,
        category: Optional[str] = None,
        min_discount: int = 0,
        max_price: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        PUBLIC API: Get list of current yellow sticker deals.
        For customer app to show available discounted products.
        """
        conn = get_connection()
        try:
            category_filter = "AND p.category = %s" if category else ""
            price_filter = "AND (p.default_price * (1 - dr.discount_percent / 100)) <= %s" if max_price else ""
            
            params = [shop_id]
            if category:
                params.append(category)
            if max_price:
                params.append(max_price)
            
            query = f"""
                SELECT 
                    p.sku,
                    p.name,
                    p.category,
                    p.default_price as original_price,
                    dr.discount_percent,
                    (p.default_price * (1 - dr.discount_percent / 100)) as discounted_price,
                    (p.default_price * dr.discount_percent / 100) as savings,
                    e.expiry_date,
                    e.days_left,
                    e.quantity_remaining as available_stock
                FROM products p
                JOIN expiry_records e ON p.id = e.product_id
                JOIN discount_rules dr ON (
                    e.days_left BETWEEN dr.days_left_min AND dr.days_left_max
                    AND e.quantity_remaining >= dr.qty_min
                    AND dr.shop_id = p.shop_id
                )
                WHERE p.shop_id = %s
                  AND e.status = 'active'
                  AND e.quantity_remaining > 0
                  AND dr.discount_percent >= %s
                  {category_filter}
                  {price_filter}
                ORDER BY dr.discount_percent DESC, e.days_left ASC
                LIMIT 50
            """
            params.insert(1, min_discount)
            
            cur = conn.cursor(dictionary=True)
            cur.execute(query, params)
            products = cur.fetchall()
            
            # Add store location info
            cur.execute("SELECT name, location FROM shops WHERE id = %s", (shop_id,))
            shop_info = cur.fetchone()
            
            return {
                "store": shop_info,
                "products": products,
                "count": len(products),
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"get_yellow_sticker_products error: {e}")
            return {"store": None, "products": [], "count": 0}
        finally:
            conn.close()
    
    @staticmethod
    def get_nearby_stores_with_discounts(
        latitude: float,
        longitude: float,
        radius_km: float = 5.0
    ) -> List[Dict[str, Any]]:
        """
        PUBLIC API: Find nearby stores with yellow sticker items.
        For customer app: "Yellow Sticker Finder" feature.
        
        NOTE: Requires shops table to have lat/long columns.
        This is a stub implementation.
        """
        # In production, use Haversine formula or PostGIS
        conn = get_connection()
        try:
            query = """
                SELECT 
                    s.id,
                    s.name,
                    s.location,
                    COUNT(DISTINCT p.id) as discounted_items,
                    MIN(dr.discount_percent) as min_discount,
                    MAX(dr.discount_percent) as max_discount
                FROM shops s
                JOIN products p ON s.id = p.shop_id
                JOIN expiry_records e ON p.id = e.product_id
                JOIN discount_rules dr ON (
                    e.days_left BETWEEN dr.days_left_min AND dr.days_left_max
                    AND dr.shop_id = s.id
                )
                WHERE e.status = 'active'
                  AND e.quantity_remaining > 0
                GROUP BY s.id, s.name, s.location
                HAVING discounted_items > 0
                ORDER BY discounted_items DESC
                LIMIT 10
            """
            
            cur = conn.cursor(dictionary=True)
            cur.execute(query)
            stores = cur.fetchall()
            
            return {
                "stores": stores,
                "search_location": {"lat": latitude, "lon": longitude},
                "radius_km": radius_km,
                "note": "Distance calculation requires lat/long columns in shops table"
            }
            
        except Exception as e:
            logger.error(f"get_nearby_stores_with_discounts error: {e}")
            return {"stores": []}
        finally:
            conn.close()
    
    @staticmethod
    def create_price_alert(
        customer_id: int,
        product_sku: str,
        shop_id: int,
        target_discount: int
    ) -> Dict[str, Any]:
        """
        Create price alert for customer.
        Notify when product reaches target discount.
        """
        conn = get_connection()
        try:
            query = """
                INSERT INTO customer_price_alerts 
                (customer_id, product_sku, shop_id, target_discount_percent, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """
            cur = conn.cursor()
            cur.execute(query, (customer_id, product_sku, shop_id, target_discount))
            conn.commit()
            
            return {
                "success": True,
                "alert_id": cur.lastrowid,
                "message": f"Alert set for {product_sku} at {target_discount}% discount"
            }
        except Exception as e:
            logger.error(f"create_price_alert error: {e}")
            conn.rollback()
            return {"success": False, "message": str(e)}
        finally:
            conn.close()
    
    @staticmethod
    def get_customer_savings_report(customer_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Calculate total savings for customer from yellow sticker purchases.
        Gamification/sustainability metrics.
        """
        conn = get_connection()
        try:
            # This assumes customer_id is tracked in sales
            query = """
                SELECT 
                    COUNT(DISTINCT ms.id) as purchase_count,
                    SUM(ms.quantity_sold) as items_saved_from_waste,
                    SUM(ms.discount_amount * ms.quantity_sold) as total_savings_pounds,
                    AVG(ms.discount_percent) as avg_discount_percent,
                    SUM(ms.discounted_price * ms.quantity_sold) as total_spent
                FROM markdown_sales ms
                WHERE ms.sold_by = %s
                  AND ms.sold_at >= NOW() - INTERVAL '%s days'
            """
            
            cur = conn.cursor(dictionary=True)
            cur.execute(query, (customer_id, days))
            result = cur.fetchone()
            
            # Calculate environmental impact
            # Assume 2.5 kg CO2 per kg food waste
            items_saved = result['items_saved_from_waste'] or 0
            co2_saved_kg = items_saved * 0.5 * 2.5  # 0.5 kg avg per item
            
            return {
                "customer_id": customer_id,
                "period_days": days,
                "purchases": result['purchase_count'] or 0,
                "items_saved_from_waste": items_saved,
                "total_savings": result['total_savings_pounds'] or 0.0,
                "avg_discount": result['avg_discount_percent'] or 0.0,
                "total_spent": result['total_spent'] or 0.0,
                "environmental_impact": {
                    "co2_saved_kg": round(co2_saved_kg, 2),
                    "message": f"You saved {co2_saved_kg:.1f}kg CO2 by preventing food waste!"
                }
            }
            
        except Exception as e:
            logger.error(f"get_customer_savings_report error: {e}")
            return {}
        finally:
            conn.close()
    
    @staticmethod
    def reserve_yellow_sticker_item(
        customer_id: int,
        product_sku: str,
        shop_id: int,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """
        Reserve discounted item for pickup (30-minute hold).
        Click & collect for yellow stickers.
        """
        conn = get_connection()
        try:
            # Check availability
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT 
                    p.id,
                    p.name,
                    e.quantity_remaining,
                    (p.default_price * (1 - dr.discount_percent / 100)) as price
                FROM products p
                JOIN expiry_records e ON p.id = e.product_id
                JOIN discount_rules dr ON (
                    e.days_left BETWEEN dr.days_left_min AND dr.days_left_max
                    AND dr.shop_id = p.shop_id
                )
                WHERE p.sku = %s 
                  AND p.shop_id = %s
                  AND e.status = 'active'
                  AND e.quantity_remaining >= %s
                LIMIT 1
            """, (product_sku, shop_id, quantity))
            
            product = cur.fetchone()
            
            if not product:
                return {"success": False, "message": "Product not available or insufficient stock"}
            
            # Create reservation
            expiry_time = datetime.now() + timedelta(minutes=30)
            cur.execute("""
                INSERT INTO customer_reservations
                (customer_id, product_id, shop_id, quantity, reserved_until, status)
                VALUES (%s, %s, %s, %s, %s, 'active')
            """, (customer_id, product['id'], shop_id, quantity, expiry_time))
            
            conn.commit()
            
            return {
                "success": True,
                "reservation_id": cur.lastrowid,
                "product_name": product['name'],
                "quantity": quantity,
                "price": product['price'] * quantity,
                "reserved_until": expiry_time.isoformat(),
                "message": f"Reserved for 30 minutes. Please collect before {expiry_time.strftime('%H:%M')}"
            }
            
        except Exception as e:
            logger.error(f"reserve_yellow_sticker_item error: {e}")
            conn.rollback()
            return {"success": False, "message": str(e)}
        finally:
            conn.close()
