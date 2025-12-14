from __future__ import annotations

from typing import Any, Dict, List, Optional
from ..db import get_connection
from ..logger import logger


def create_alert_notification(
    shop_id: int,
    product_id: int,
    alert_type: str,
    message: str,
    recipient_email: str | None = None,
    recipient_phone: str | None = None,
    sent: bool = False,
) -> Optional[int]:
    """Create an alert notification record."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO alert_notifications (shop_id, product_id, alert_type, message,
                                            recipient_email, recipient_phone, sent)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (shop_id, product_id, alert_type, message, recipient_email, recipient_phone, 1 if sent else 0),
        )
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        logger.error(f"create_alert_notification error: {e}")
        conn.rollback()
        return None
    finally:
        cur.close()
        conn.close()


def get_pending_alerts(limit: int = 100) -> List[Dict[str, Any]]:
    """Get unsent alerts for processing by workers."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            """
            SELECT * FROM alert_notifications
            WHERE sent = 0
            ORDER BY created_at ASC
            LIMIT %s
            """,
            (limit,),
        )
        return cur.fetchall() or []
    except Exception as e:
        logger.error(f"get_pending_alerts error: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def mark_alert_sent(alert_id: int, delivery_status: str = "sent") -> bool:
    """Mark alert as sent."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE alert_notifications
            SET sent = 1, delivery_status = %s, sent_at = NOW()
            WHERE id = %s
            """,
            (delivery_status, alert_id),
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"mark_alert_sent error: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def get_alerts_for_shop(shop_id: int, days: int = 30) -> List[Dict[str, Any]]:
    """Get recent alerts for a shop."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            """
            SELECT a.*, p.name as product_name, p.sku
            FROM alert_notifications a
            JOIN products p ON a.product_id = p.id
            WHERE a.shop_id = %s AND a.created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            ORDER BY a.created_at DESC
            """,
            (shop_id, days),
        )
        return cur.fetchall() or []
    except Exception as e:
        logger.error(f"get_alerts_for_shop error: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def get_alert_settings(shop_id: int) -> Optional[Dict[str, Any]]:
    """Get alert configuration for a shop."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT * FROM alert_settings WHERE shop_id = %s",
            (shop_id,),
        )
        return cur.fetchone()
    except Exception as e:
        logger.error(f"get_alert_settings error: {e}")
        return None
    finally:
        cur.close()
        conn.close()


def save_alert_settings(
    shop_id: int,
    email_enabled: bool = True,
    sms_enabled: bool = False,
    alert_days_threshold: int = 7,
    alert_emails: str | None = None,
    alert_phones: str | None = None,
) -> bool:
    """Save or update alert settings for a shop."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO alert_settings
            (shop_id, email_enabled, sms_enabled, alert_days_threshold, alert_emails, alert_phones)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            email_enabled = VALUES(email_enabled),
            sms_enabled = VALUES(sms_enabled),
            alert_days_threshold = VALUES(alert_days_threshold),
            alert_emails = VALUES(alert_emails),
            alert_phones = VALUES(alert_phones)
            """,
            (shop_id, 1 if email_enabled else 0, 1 if sms_enabled else 0, alert_days_threshold, alert_emails, alert_phones),
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"save_alert_settings error: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()
