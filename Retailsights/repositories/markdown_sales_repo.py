from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from Retailsights.db_orm import get_session
from sqlalchemy import func
from Retailsights.models import MarkdownSale
from logger import logger


def record_markdown_sale(
    shop_id: int,
    product_id: Optional[int],
    sku: Optional[str],
    quantity_sold: int,
    original_price: Optional[float],
    discounted_price: float,
    discount_percent: Optional[float],
    discount_amount: Optional[float],
    rule_id: Optional[int] = None,
    rule_name: Optional[str] = None,
    expiry_record_id: Optional[int] = None,
    sold_by: Optional[int] = None,
) -> Optional[int]:
    """Insert a markdown sale record. Returns inserted id or None.

    Note: the ORM model stores a simplified subset of fields. Extra
    values passed in are accepted but only the modeled fields are persisted.
    """
    session = get_session()
    try:
        ms = MarkdownSale(
            shop_id=shop_id,
            quantity_sold=quantity_sold,
            discounted_price=discounted_price,
        )
        session.add(ms)
        session.commit()
        return ms.id
    except Exception as e:
        logger.error(f"record_markdown_sale error: {e}")
        session.rollback()
        return None
    finally:
        session.close()


def get_markdown_sales(shop_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch recent markdown sales for a shop."""
    session = get_session()
    try:
        rows = (
            session.query(MarkdownSale)
            .filter(MarkdownSale.shop_id == shop_id)
            .order_by(MarkdownSale.sold_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "quantity_sold": r.quantity_sold,
                "discounted_price": r.discounted_price,
                "sold_at": r.sold_at,
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"get_markdown_sales error: {e}")
        return []
    finally:
        session.close()


def get_markdown_sales_summary(shop_id: int, days: int = 7) -> Dict[str, Any]:
    """Get summary stats for markdown sales in the last N days."""
    session = get_session()
    try:
        start_dt = datetime.utcnow() - timedelta(days=days)
        total_sales = (
            session.query(MarkdownSale)
            .filter(MarkdownSale.shop_id == shop_id)
            .filter(MarkdownSale.sold_at >= start_dt)
            .count()
        )
        total_quantity = (
            session.query(func.coalesce(func.sum(MarkdownSale.quantity_sold), 0))
            .filter(MarkdownSale.shop_id == shop_id)
            .filter(MarkdownSale.sold_at >= start_dt)
            .scalar()
        )
        total_revenue = (
            session.query(func.coalesce(func.sum(MarkdownSale.discounted_price * MarkdownSale.quantity_sold), 0.0))
            .filter(MarkdownSale.shop_id == shop_id)
            .filter(MarkdownSale.sold_at >= start_dt)
            .scalar()
        )
        # discount_amount not modeled; set to 0.0 to keep compatibility
        total_discount_given = 0.0
        return {
            "total_sales": total_sales,
            "total_quantity": int(total_quantity or 0),
            "total_discount_given": float(total_discount_given),
            "total_revenue": float(total_revenue or 0.0),
        }
    except Exception as e:
        logger.error(f"get_markdown_sales_summary error: {e}")
        return {}
    finally:
        session.close()
