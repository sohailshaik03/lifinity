from __future__ import annotations

from services.celery_app import celery_app
from repositories.alerts_repo import (
    create_alert_notification,
    mark_alert_sent,
    get_pending_alerts,
    get_alert_settings,
)
from services.notification_service import EmailService, SMSService, AlertTemplates
from repositories.products_repo import get_expiring_products
from logger import logger
from datetime import datetime


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_pending_alerts(self):
    """Task: process and send all pending alerts (email/SMS)."""
    try:
        alerts = get_pending_alerts(limit=50)
        logger.info(f"Processing {len(alerts)} pending alerts")

        for alert in alerts:
            try:
                if alert.get("recipient_email"):
                    EmailService.send_email(
                        to_email=alert["recipient_email"],
                        subject="RetailSight Alert",
                        html_body=alert.get("message", ""),
                    )

                if alert.get("recipient_phone"):
                    SMSService.send_sms(
                        phone_number=alert["recipient_phone"],
                        body=f"RetailSight: {alert.get('message', '')[:160]}",
                    )

                mark_alert_sent(alert["id"], delivery_status="sent")
                logger.info(f"Alert {alert['id']} sent")

            except Exception as e:
                logger.error(f"Failed to send alert {alert['id']}: {e}")
                mark_alert_sent(alert["id"], delivery_status="failed")

    except Exception as e:
        logger.exception("send_pending_alerts task failed")
        raise


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def check_and_alert_expiring_products(self, shop_id: int):
    """Task: check for expiring products and create alerts."""
    try:
        settings = get_alert_settings(shop_id)
        if not settings or not (settings.get("email_enabled") or settings.get("sms_enabled")):
            logger.info(f"Alerts disabled for shop {shop_id}")
            return

        threshold = settings.get("alert_days_threshold", 7)
        expiring = get_expiring_products(shop_id, days_threshold=threshold)

        alert_emails = settings.get("alert_emails", "").split(",") if settings.get("alert_emails") else []
        alert_phones = settings.get("alert_phones", "").split(",") if settings.get("alert_phones") else []

        for prod in expiring:
            product_name = prod.get("name", "Unknown")
            sku = prod.get("sku", "")
            days_left = prod.get("days_left", 0)
            qty = prod.get("quantity_remaining", 0)

            html_body = AlertTemplates.expiry_warning_email(product_name, sku, days_left, qty)
            sms_body = AlertTemplates.expiry_warning_sms(product_name, days_left)

            for email in alert_emails:
                email = email.strip()
                if email:
                    create_alert_notification(
                        shop_id=shop_id,
                        product_id=prod.get("id"),
                        alert_type="expiry_warning",
                        message=html_body,
                        recipient_email=email,
                        sent=False,
                    )

            for phone in alert_phones:
                phone = phone.strip()
                if phone:
                    create_alert_notification(
                        shop_id=shop_id,
                        product_id=prod.get("id"),
                        alert_type="expiry_warning",
                        message=sms_body,
                        recipient_phone=phone,
                        sent=False,
                    )

        logger.info(f"Created {len(expiring)} alerts for shop {shop_id}")

    except Exception as e:
        logger.exception(f"check_and_alert_expiring_products failed for shop {shop_id}")
        raise
