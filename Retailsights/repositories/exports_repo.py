from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import text
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
    try:
        result = conn.execute(
            text("""
            INSERT INTO report_exports (shop_id, user_id, filename, task_id, status)
            VALUES (:shop_id, :user_id, :filename, :task_id, :status)
            """),
            {"shop_id": shop_id, "user_id": user_id, "filename": filename, "task_id": task_id, "status": status}
        )
        conn.commit()
        return result.lastrowid
    except Exception as e:
        logger.error(f"create_export error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def update_export(export_id: int, **kwargs) -> bool:
    if not kwargs:
        return True
    conn = get_connection()
    try:
        updates = []
        params = {"export_id": export_id}
        for k, v in kwargs.items():
            updates.append(f"{k} = :{k}")
            params[k] = v
        sql = f"UPDATE report_exports SET {', '.join(updates)} WHERE id = :export_id"
        conn.execute(text(sql), params)
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"update_export error: {e}")
        conn.rollback()
        return False
    finally:
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
    try:
        result = conn.execute(
            text("""
            SELECT id, shop_id, user_id, filename, provider, url, status, task_id, created_at, completed_at
            FROM report_exports
            WHERE task_id = :task_id
            LIMIT 1
            """),
            {"task_id": task_id}
        )
        row = result.fetchone()
        return dict(row._mapping) if row else None
    except Exception as e:
        logger.error(f"get_export_by_task_id error: {e}")
        return None
    finally:
        cur.close()
        conn.close()
