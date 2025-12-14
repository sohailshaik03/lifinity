from __future__ import annotations

from typing import Any, Dict, List
import pandas as pd
from datetime import datetime, timedelta
from ..repositories.products_repo import get_discount_rules
from ..db import get_connection
from ..logger import logger


class DiscountReportService:
    """Generate historical discount and sales reports."""

    @staticmethod
    def get_discount_applied_records(shop_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Fetch records of products sold with discounts."""
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(
                """
                SELECT
                    p.id, p.sku, p.name, p.selling_price,
                    sl.quantity, sl.unit_price, sl.line_revenue,
                    er.days_left,
                    ROUND(((p.selling_price - sl.unit_price) / p.selling_price) * 100, 2) as discount_applied_pct,
                    DATE(st.transaction_dt) as sale_date
                FROM sales_lines sl
                JOIN products p ON sl.product_id = p.id
                JOIN sales_transactions st ON sl.transaction_id = st.id
                LEFT JOIN expiry_records er ON sl.product_id = er.product_id
                WHERE st.shop_id = %s
                    AND st.transaction_dt >= NOW() - INTERVAL '%s days'
                    AND sl.unit_price < p.selling_price
                ORDER BY st.transaction_dt DESC
                """,
                (shop_id, days),
            )
            return cur.fetchall() or []
        except Exception as e:
            logger.error(f"get_discount_applied_records error: {e}")
            return []
        finally:
            cur.close()
            conn.close()

    @staticmethod
    def calculate_discount_impact(discount_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate impact of discounts: revenue forgone, units moved, etc."""
        if not discount_records:
            return {
                "total_units_discounted": 0,
                "total_revenue_forgone": 0.0,
                "avg_discount_pct": 0.0,
                "total_revenue_at_full_price": 0.0,
            }

        df = pd.DataFrame(discount_records)

        total_units = int(df["quantity"].sum())
        total_revenue = float(df["line_revenue"].sum())
        full_price_revenue = float((df["quantity"] * df["selling_price"]).sum())
        revenue_forgone = full_price_revenue - total_revenue
        avg_discount = float(df["discount_applied_pct"].mean()) if len(df) > 0 else 0.0

        return {
            "total_units_discounted": total_units,
            "total_revenue_forgone": round(revenue_forgone, 2),
            "avg_discount_pct": round(avg_discount, 2),
            "total_revenue_at_full_price": round(full_price_revenue, 2),
            "total_revenue_actual": total_revenue,
        }

    @staticmethod
    def get_discount_by_rule(shop_id: int, days: int = 30) -> Dict[str, Any]:
        """Get discount impact broken down by discount rule."""
        records = DiscountReportService.get_discount_applied_records(shop_id, days=days)

        if not records:
            return {}

        df = pd.DataFrame(records)
        rules = get_discount_rules(shop_id)

        # Map each record to a rule based on days_left and discount_applied_pct
        impact_by_rule = {}

        for rule in rules:
            rule_name = rule.get("name", f"Rule {rule['id']}")
            matching = df[
                (df["days_left"] >= rule["days_left_min"]) & (df["days_left"] <= rule["days_left_max"])
            ]
            if not matching.empty:
                impact_by_rule[rule_name] = {
                    "units": int(matching["quantity"].sum()),
                    "revenue_forgone": round((matching["quantity"] * matching["selling_price"]).sum() - matching["line_revenue"].sum(), 2),
                    "avg_discount_pct": round(matching["discount_applied_pct"].mean(), 2),
                }

        return impact_by_rule

    @staticmethod
    def get_expiring_vs_wasted(shop_id: int, days: int = 30) -> Dict[str, Any]:
        """Compare expiring product counts vs wasted counts."""
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(
                """
                SELECT
                    COUNT(DISTINCT er.id) as total_expiry_batches,
                    SUM(CASE WHEN er.days_left <= 0 THEN 1 ELSE 0 END) as expired_batches,
                    SUM(er.quantity_remaining) as total_remaining_qty
                FROM expiry_records er
                JOIN products p ON er.product_id = p.id
                WHERE p.shop_id = %s AND er.created_at >= NOW() - INTERVAL '%s days'
                """,
                (shop_id, days),
            )
            expiry_stats = cur.fetchone() or {}

            cur.execute(
                """
                SELECT
                    COUNT(*) as total_waste_events,
                    SUM(quantity_wasted) as total_wasted_qty,
                    COUNT(DISTINCT product_id) as unique_products_wasted
                FROM waste_records wr
                JOIN products p ON wr.product_id = p.id
                WHERE p.shop_id = %s AND wr.recorded_at >= NOW() - INTERVAL '%s days'
                """,
                (shop_id, days),
            )
            waste_stats = cur.fetchone() or {}

            return {
                "expiry": {
                    "total_batches": expiry_stats.get("total_expiry_batches", 0),
                    "expired_batches": expiry_stats.get("expired_batches", 0),
                    "remaining_qty": expiry_stats.get("total_remaining_qty", 0),
                },
                "waste": {
                    "total_events": waste_stats.get("total_waste_events", 0),
                    "total_wasted_qty": waste_stats.get("total_wasted_qty", 0),
                    "unique_products": waste_stats.get("unique_products_wasted", 0),
                },
            }

        except Exception as e:
            logger.error(f"get_expiring_vs_wasted error: {e}")
            return {}
        finally:
            cur.close()
            conn.close()
