from __future__ import annotations

from typing import Any, Dict, List
import pandas as pd
from datetime import datetime, timedelta
from ..repositories.products_repo import get_discount_rules
from ..db_orm import get_session
from ..models import Product, SalesLine, SalesTransaction, ExpiryRecord, WasteRecord
from ..logger import logger
from sqlalchemy import func, case, cast, Date
from sqlalchemy.orm import aliased


class DiscountReportService:
    """Generate historical discount and sales reports."""

    @staticmethod
    def get_discount_applied_records(shop_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """Fetch records of products sold with discounts."""
        session = get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            results = session.query(
                Product.id,
                Product.sku,
                Product.name,
                Product.selling_price,
                SalesLine.quantity,
                SalesLine.unit_price,
                SalesLine.line_revenue,
                ExpiryRecord.days_left,
                func.round(
                    ((Product.selling_price - SalesLine.unit_price) / Product.selling_price) * 100, 2
                ).label('discount_applied_pct'),
                cast(SalesTransaction.transaction_dt, Date).label('sale_date')
            ).join(
                Product, SalesLine.product_id == Product.id
            ).join(
                SalesTransaction, SalesLine.transaction_id == SalesTransaction.id
            ).outerjoin(
                ExpiryRecord, SalesLine.product_id == ExpiryRecord.product_id
            ).filter(
                SalesTransaction.shop_id == shop_id,
                SalesTransaction.transaction_dt >= cutoff_date,
                SalesLine.unit_price < Product.selling_price
            ).order_by(
                SalesTransaction.transaction_dt.desc()
            ).all()
            
            return [
                {
                    'id': r.id,
                    'sku': r.sku,
                    'name': r.name,
                    'selling_price': r.selling_price,
                    'quantity': r.quantity,
                    'unit_price': r.unit_price,
                    'line_revenue': r.line_revenue,
                    'days_left': r.days_left,
                    'discount_applied_pct': r.discount_applied_pct,
                    'sale_date': r.sale_date
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"get_discount_applied_records error: {e}")
            return []
        finally:
            session.close()

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
        session = get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get expiry stats
            expiry_stats = session.query(
                func.count(func.distinct(ExpiryRecord.id)).label('total_expiry_batches'),
                func.sum(case((ExpiryRecord.days_left <= 0, 1), else_=0)).label('expired_batches'),
                func.sum(ExpiryRecord.quantity_remaining).label('total_remaining_qty')
            ).join(
                Product, ExpiryRecord.product_id == Product.id
            ).filter(
                Product.shop_id == shop_id,
                ExpiryRecord.created_at >= cutoff_date
            ).first()

            # Get waste stats
            waste_stats = session.query(
                func.count(WasteRecord.id).label('total_waste_events'),
                func.sum(WasteRecord.quantity_wasted).label('total_wasted_qty'),
                func.count(func.distinct(WasteRecord.product_id)).label('unique_products_wasted')
            ).join(
                Product, WasteRecord.product_id == Product.id
            ).filter(
                Product.shop_id == shop_id,
                WasteRecord.recorded_at >= cutoff_date
            ).first()

            return {
                "expiry": {
                    "total_batches": expiry_stats.total_expiry_batches or 0,
                    "expired_batches": expiry_stats.expired_batches or 0,
                    "remaining_qty": expiry_stats.total_remaining_qty or 0,
                },
                "waste": {
                    "total_events": waste_stats.total_waste_events or 0,
                    "total_wasted_qty": waste_stats.total_wasted_qty or 0,
                    "unique_products": waste_stats.unique_products_wasted or 0,
                },
            }

        except Exception as e:
            logger.error(f"get_expiring_vs_wasted error: {e}")
            return {}
        finally:
            session.close()
