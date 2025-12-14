from __future__ import annotations

from typing import Any, Dict, List, Optional
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
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO scan_history (
              shop_id, product_id, code, code_type, source,
              discount_applied, discount_percent, original_price, discounted_price, message
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                shop_id,
                product_id,
                code,
                code_type,
                source,
                1 if discount_applied else 0,
                discount_percent,
                original_price,
                discounted_price,
                message,
            ),
        )
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        logger.error(f"record_scan_event error: {e}")
        conn.rollback()
        return None
    finally:
        cur.close()
        conn.close()


def get_recent_scans(shop_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch recent scan events for a shop."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            """
            SELECT id, code, code_type, source, discount_applied, discount_percent,
                   original_price, discounted_price, message, scanned_at, product_id
            FROM scan_history
            WHERE shop_id = %s
            ORDER BY scanned_at DESC
            LIMIT %s
            """,
            (shop_id, limit),
        )
        return cur.fetchall() or []
    except Exception as e:
        logger.error(f"get_recent_scans error: {e}")
        return []
    finally:
        cur.close()
        conn.close()
