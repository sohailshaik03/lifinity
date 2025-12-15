from __future__ import annotations

from typing import Any, Dict, List, Optional
from sqlalchemy import text
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
    try:
        result = conn.execute(
            text("""
            INSERT INTO alert_notifications (shop_id, product_id, alert_type, message,
                                            recipient_email, recipient_phone, sent)
            VALUES (:shop_id, :product_id, :alert_type, :message, :recipient_email, :recipient_phone, :sent)
            """),
            {"shop_id": shop_id, "product_id": product_id, "alert_type": alert_type, "message": message, 
             "recipient_email": recipient_email, "recipient_phone": recipient_phone, "sent": 1 if sent else 0}
        )
        conn.commit()
        return result.lastrowid
    except Exception as e:
        logger.error(f"create_alert_notification error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_pending_alerts(limit: int = 100) -> List[Dict[str, Any]]:
    """Get unsent alerts for processing by workers."""
    conn = get_connection()
    try:
        result = conn.execute(
            text("""
            SELECT * FROM alert_notifications
            WHERE sent = 0
            ORDER BY created_at ASC
            LIMIT :limit
            """),
            {"limit": limit}
        )
        return [dict(row._mapping) for row in result.fetchall()] or []
    except Exception as e:
        logger.error(f"get_pending_alerts error: {e}")
        return []
    finally:
        conn.close()


def mark_alert_sent(alert_id: int, delivery_status: str = "sent") -> bool:
    """Mark alert as sent."""
    conn = get_connection()
    try:
        conn.execute(
            text("""
            UPDATE alert_notifications
            SET sent = 1, delivery_status = :delivery_status, sent_at = NOW()
            WHERE id = :alert_id
            """),
            {"delivery_status": delivery_status, "alert_id": alert_id}
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"mark_alert_sent error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_alerts_for_shop(shop_id: int, days: int = 30) -> List[Dict[str, Any]]:
    """Get recent alerts for a shop."""
    conn = get_connection()
    try:
        result = conn.execute(
            text("""
            SELECT a.*, p.name as product_name, p.sku
            FROM alert_notifications a
            JOIN products p ON a.product_id = p.id
            WHERE a.shop_id = :shop_id AND a.created_at >= NOW() - INTERVAL ':days days'
            ORDER BY a.created_at DESC
            """),
            {"shop_id": shop_id, "days": days}
        )
        return [dict(row._mapping) for row in result.fetchall()] or []
    except Exception as e:
        logger.error(f"get_alerts_for_shop error: {e}")
        return []
    finally:
        conn.close()


def get_alert_settings(shop_id: int) -> Optional[Dict[str, Any]]:
    """Get alert configuration for a shop."""
    conn = get_connection()
    try:
        result = conn.execute(
            text("SELECT * FROM alert_settings WHERE shop_id = :shop_id"),
            {"shop_id": shop_id}
        )
        row = result.fetchone()
        return dict(row._mapping) if row else None
    except Exception as e:
        logger.error(f"get_alert_settings error: {e}")
        return None
    finally:
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
    try:
        conn.execute(
            text("""
            INSERT INTO alert_settings
            (shop_id, email_enabled, sms_enabled, alert_days_threshold, alert_emails, alert_phones)
            VALUES (:shop_id, :email_enabled, :sms_enabled, :alert_days_threshold, :alert_emails, :alert_phones)
            ON DUPLICATE KEY UPDATE
            email_enabled = VALUES(email_enabled),
            sms_enabled = VALUES(sms_enabled),
            alert_days_threshold = VALUES(alert_days_threshold),
            alert_emails = VALUES(alert_emails),
            alert_phones = VALUES(alert_phones)
            """),
            {"shop_id": shop_id, "email_enabled": 1 if email_enabled else 0, "sms_enabled": 1 if sms_enabled else 0,
             "alert_days_threshold": alert_days_threshold, "alert_emails": alert_emails, "alert_phones": alert_phones}
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"save_alert_settings error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
