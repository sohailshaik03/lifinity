from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..db import get_connection
from ..logger import logger


def create_export(
    shop_id: int,
    user_id: int,
    filename: str,
    task_id: str | None = None,
    status: str = "pending",
) -> Optional[int]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO report_exports (shop_id, user_id, filename, task_id, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (shop_id, user_id, filename, task_id, status),
        )
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        logger.error(f"create_export error: {e}")
        conn.rollback()
        return None
    finally:
        cur.close()
        conn.close()


def update_export(export_id: int, **kwargs) -> bool:
    if not kwargs:
        return True
    conn = get_connection()
    cur = conn.cursor()
    try:
        updates = []
        values = []
        for k, v in kwargs.items():
            updates.append(f"{k} = %s")
            values.append(v)
        values.append(export_id)
        sql = f"UPDATE report_exports SET {', '.join(updates)} WHERE id = %s"
        cur.execute(sql, tuple(values))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"update_export error: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def get_exports_for_shop(shop_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        result = conn.execute(
            text("""
            SELECT id, shop_id, user_id, filename, provider, url, status, task_id, created_at, completed_at
            FROM report_exports
            WHERE shop_id = :shop_id
            ORDER BY created_at DESC
            """),
            {"shop_id": shop_id}
        )
        rows = [dict(row._mapping) for row in result]
        return rows if rows else []
    except Exception as e:
        logger.error(f"get_exports_for_shop error: {e}")
        return []
    finally:
        conn.close()


def get_export_by_task_id(task_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            """
            SELECT id, shop_id, user_id, filename, provider, url, status, task_id, created_at, completed_at
            FROM report_exports
            WHERE task_id = %s
            LIMIT 1
            """,
            (task_id,),
        )
        return cur.fetchone()
    except Exception as e:
        logger.error(f"get_export_by_task_id error: {e}")
        return None
    finally:
        cur.close()
        conn.close()
