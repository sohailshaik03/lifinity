from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy import text
from ..db import get_connection
from ..logger import logger


def record_scan_event(
    shop_id: int,
    code: str,
    code_type: str,
    source: str,
    product_id: Optional[int] = None,
    discount_applied: bool = False,
    discount_percent: float = 0.0,
    original_price: Optional[float] = None,
    discounted_price: Optional[float] = None,
    message: str | None = None,
) -> Optional[int]:
    """Insert a scan history record. Returns inserted id or None."""
    conn = get_connection()
    try:
        result = conn.execute(
            text("""
            INSERT INTO scan_history (
              shop_id, product_id, code, code_type, source,
              discount_applied, discount_percent, original_price, discounted_price, message
            ) VALUES (:shop_id, :product_id, :code, :code_type, :source, :discount_applied, :discount_percent, :original_price, :discounted_price, :message)
            """),
            {
                "shop_id": shop_id,
                "product_id": product_id,
                "code": code,
                "code_type": code_type,
                "source": source,
                "discount_applied": 1 if discount_applied else 0,
                "discount_percent": discount_percent,
                "original_price": original_price,
                "discounted_price": discounted_price,
                "message": message,
            }
        )
        conn.commit()
        return result.lastrowid
    except Exception as e:
        logger.error(f"record_scan_event error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_recent_scans(shop_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch recent scan events for a shop."""
    conn = get_connection()
    try:
        result = conn.execute(
            text("""
            SELECT id, code, code_type, source, discount_applied, discount_percent,
                   original_price, discounted_price, message, scanned_at, product_id
            FROM scan_history
            WHERE shop_id = :shop_id
            ORDER BY scanned_at DESC
            LIMIT :limit
            """),
            {"shop_id": shop_id, "limit": limit}
        )
        rows = [dict(row._mapping) for row in result]
        return rows if rows else []
    except Exception as e:
        logger.error(f"get_recent_scans error: {e}")
        return []
    finally:
        conn.close()
