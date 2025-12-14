"""
Dynamic Pricing Engine
Time-based, demand-based, and AI-powered pricing optimization.
"""
from __future__ import annotations

from datetime import datetime, time
from typing import Any, Dict, List, Optional
from ..db import get_connection
from ..logger import logger


class DynamicPricingService:
    """Advanced pricing engine with multiple strategies."""
    
    # Time-of-day multipliers (deeper discounts in evening)
    TIME_MULTIPLIERS = {
        (6, 11): 1.0,   # Morning: 6am-11am - No extra discount
        (11, 15): 1.0,  # Lunch: 11am-3pm - No extra discount
        (15, 18): 1.15, # Afternoon: 3pm-6pm - 15% extra discount
        (18, 21): 1.30, # Evening: 6pm-9pm - 30% extra discount
        (21, 24): 1.50, # Night: 9pm-midnight - 50% extra discount
        (0, 6): 1.50,   # Late night: midnight-6am - 50% extra discount
    }
    
    @staticmethod
    def get_time_based_multiplier(current_time: Optional[datetime] = None) -> float:
        """Get discount multiplier based on time of day."""
        if current_time is None:
            current_time = datetime.now()
        
        hour = current_time.hour
        
        for (start_hour, end_hour), multiplier in DynamicPricingService.TIME_MULTIPLIERS.items():
            if start_hour <= hour < end_hour:
                return multiplier
        
        return 1.0
    
    @staticmethod
    def calculate_dynamic_discount(
        product_id: int,
        base_discount_percent: float,
        days_left: int,
        current_stock: int,
        include_time_factor: bool = True,
        include_velocity_factor: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate optimized discount considering multiple factors:
        - Base discount from rules
        - Time of day
        - Sales velocity
        - Stock level urgency
        """
        
        discount_percent = base_discount_percent
        factors_applied = []
        
        # Factor 1: Time of day
        if include_time_factor:
            time_multiplier = DynamicPricingService.get_time_based_multiplier()
            if time_multiplier > 1.0:
                additional_discount = (time_multiplier - 1.0) * base_discount_percent
                discount_percent += additional_discount
                factors_applied.append({
                    "factor": "time_of_day",
                    "multiplier": time_multiplier,
                    "additional_discount": round(additional_discount, 1),
                    "reason": f"Evening/night premium ({time_multiplier}x)"
                })
        
        # Factor 2: Urgency based on days left
        if days_left <= 1:
            urgency_boost = 20  # Critical urgency
            discount_percent += urgency_boost
            factors_applied.append({
                "factor": "urgency",
                "additional_discount": urgency_boost,
                "reason": "Expires today or tomorrow - critical urgency"
            })
        elif days_left <= 3:
            urgency_boost = 10
            discount_percent += urgency_boost
            factors_applied.append({
                "factor": "urgency",
                "additional_discount": urgency_boost,
                "reason": "Expires in 3 days - high urgency"
            })
        
        # Factor 3: Stock level urgency
        if current_stock > 20:
            stock_boost = 10
            discount_percent += stock_boost
            factors_applied.append({
                "factor": "stock_level",
                "additional_discount": stock_boost,
                "reason": f"High stock ({current_stock} units) - needs clearance"
            })
        elif current_stock > 10:
            stock_boost = 5
            discount_percent += stock_boost
            factors_applied.append({
                "factor": "stock_level",
                "additional_discount": stock_boost,
                "reason": f"Moderate stock ({current_stock} units)"
            })
        
        # Factor 4: Sales velocity (if enabled)
        if include_velocity_factor:
            velocity_data = DynamicPricingService.get_product_velocity(product_id)
            if velocity_data:
                units_per_day = velocity_data.get('avg_units_per_day', 0)
                days_to_sell = current_stock / units_per_day if units_per_day > 0 else 999
                
                if days_to_sell > days_left * 1.5:
                    # Won't sell in time at current rate
                    velocity_boost = 15
                    discount_percent += velocity_boost
                    factors_applied.append({
                        "factor": "slow_velocity",
                        "additional_discount": velocity_boost,
                        "reason": f"Slow sales: {days_to_sell:.1f} days to sell vs {days_left} until expiry"
                    })
        
        # Cap at reasonable maximum (90%)
        discount_percent = min(90, discount_percent)
        
        return {
            "final_discount_percent": round(discount_percent, 1),
            "base_discount": base_discount_percent,
            "total_boost": round(discount_percent - base_discount_percent, 1),
            "factors_applied": factors_applied,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_product_velocity(product_id: int, days: int = 14) -> Optional[Dict[str, Any]]:
        """Calculate sales velocity for a product."""
        conn = get_connection()
        try:
            query = """
                SELECT 
                    COUNT(DISTINCT s.id) as transaction_count,
                    SUM(sl.quantity) as total_units_sold,
                    DATEDIFF(NOW(), MIN(s.created_at)) as days_tracked,
                    MAX(s.created_at) as last_sale_date
                FROM sales_lines sl
                JOIN sales s ON sl.sale_id = s.id
                WHERE sl.product_id = %s
                  AND s.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            cur = conn.cursor(dictionary=True)
            cur.execute(query, (product_id, days))
            result = cur.fetchone()
            
            if result and result['total_units_sold']:
                days_tracked = max(1, result['days_tracked'] or days)
                return {
                    "avg_units_per_day": result['total_units_sold'] / days_tracked,
                    "total_units": result['total_units_sold'],
                    "days_tracked": days_tracked,
                    "last_sale": result['last_sale_date']
                }
            return None
        except Exception as e:
            logger.error(f"get_product_velocity error: {e}")
            return None
        finally:
            conn.close()
    
    @staticmethod
    def get_optimal_discount_schedule(
        product_id: int,
        days_until_expiry: int,
        current_price: float,
        target_sellthrough: float = 0.9
    ) -> List[Dict[str, Any]]:
        """
        Generate a schedule of increasing discounts over time.
        Returns suggested discounts for each day until expiry.
        """
        schedule = []
        
        # Start with conservative discount, increase daily
        base_discount = 10 if days_until_expiry > 7 else 20
        
        for day in range(days_until_expiry + 1):
            days_remaining = days_until_expiry - day
            
            # Progressive discount increase
            if days_remaining > 7:
                discount = base_discount
            elif days_remaining > 5:
                discount = base_discount + 10
            elif days_remaining > 3:
                discount = base_discount + 20
            elif days_remaining > 1:
                discount = base_discount + 35
            else:
                discount = base_discount + 50
            
            discount = min(90, discount)
            discounted_price = current_price * (1 - discount / 100)
            
            schedule.append({
                "day": day + 1,
                "days_remaining": days_remaining,
                "discount_percent": discount,
                "price": round(discounted_price, 2),
                "action": "Apply discount" if day == 0 else f"Wait {day} more day(s)"
            })
        
        return schedule
    
    @staticmethod
    def suggest_bundle_pricing(shop_id: int, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Suggest product bundles with special pricing."""
        conn = get_connection()
        try:
            # Find products expiring soon that could be bundled
            category_filter = "AND p.category = %s" if category else ""
            params = [shop_id]
            if category:
                params.append(category)
            
            query = f"""
                SELECT 
                    p.id,
                    p.sku,
                    p.name,
                    p.category,
                    p.default_price,
                    e.expiry_date,
                    e.days_left,
                    e.quantity_remaining
                FROM products p
                JOIN expiry_records e ON p.id = e.product_id
                WHERE p.shop_id = %s
                  AND e.status = 'active'
                  AND e.days_left BETWEEN 3 AND 10
                  AND e.quantity_remaining >= 2
                  {category_filter}
                ORDER BY e.days_left ASC, e.quantity_remaining DESC
                LIMIT 20
            """
            
            cur = conn.cursor(dictionary=True)
            cur.execute(query, params)
            products = cur.fetchall()
            
            # Group by category for bundle suggestions
            bundles = []
            category_groups = {}
            
            for product in products:
                cat = product['category'] or 'Other'
                if cat not in category_groups:
                    category_groups[cat] = []
                category_groups[cat].append(product)
            
            # Create bundles
            for cat, prods in category_groups.items():
                if len(prods) >= 2:
                    # Take 2-3 products per bundle
                    bundle_size = min(3, len(prods))
                    bundle_products = prods[:bundle_size]
                    
                    total_price = sum(p['default_price'] for p in bundle_products)
                    bundle_discount = 40  # 40% off bundle
                    bundle_price = total_price * (1 - bundle_discount / 100)
                    
                    bundles.append({
                        "bundle_name": f"{cat} Clearance Bundle",
                        "products": [{"sku": p['sku'], "name": p['name'], "days_left": p['days_left']} 
                                   for p in bundle_products],
                        "total_regular_price": round(total_price, 2),
                        "bundle_price": round(bundle_price, 2),
                        "discount_percent": bundle_discount,
                        "savings": round(total_price - bundle_price, 2)
                    })
            
            return bundles[:5]  # Return top 5 bundles
            
        except Exception as e:
            logger.error(f"suggest_bundle_pricing error: {e}")
            return []
        finally:
            conn.close()
    
    @staticmethod
    def get_competitor_pricing_suggestions() -> List[Dict[str, Any]]:
        """Placeholder for competitor price monitoring integration."""
        # In production, this would integrate with APIs like:
        # - Price comparison websites
        # - Competitor websites scraping
        # - Industry price feeds
        
        return [
            {
                "feature": "competitor_monitoring",
                "status": "not_implemented",
                "suggestion": "Integrate with price monitoring APIs",
                "example_providers": [
                    "Prisync",
                    "Competera",
                    "Price2Spy"
                ]
            }
        ]
