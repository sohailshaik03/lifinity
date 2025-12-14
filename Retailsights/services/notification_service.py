from __future__ import annotations

import os
from typing import Dict, Any, Optional
from logger import logger


class EmailService:
    """Email service wrapper (SendGrid integration)."""

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_body: str,
    ) -> Dict[str, Any]:
        """Send email via SendGrid."""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            api_key = os.getenv("SENDGRID_API_KEY")
            from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@retailsight.local")

            if not api_key:
                logger.warning("SENDGRID_API_KEY not set — using stub mode")
                return {"status": "stub", "message": f"Email to {to_email} (stub mode)"}

            message = Mail(from_email=from_email, to_emails=to_email, subject=subject, html_content=html_body)
            sg = SendGridAPIClient(api_key)
            response = sg.send(message)

            logger.info(f"Email sent to {to_email}: status {response.status_code}")
            return {"status": "sent", "code": response.status_code}

        except Exception as e:
            logger.error(f"Email send error: {e}")
            return {"status": "error", "error": str(e)}


class SMSService:
    """SMS service wrapper (Twilio integration)."""

    @staticmethod
    def send_sms(phone_number: str, body: str) -> Dict[str, Any]:
        """Send SMS via Twilio."""
        try:
            from twilio.rest import Client

            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            from_number = os.getenv("TWILIO_FROM_NUMBER")

            if not (account_sid and auth_token and from_number):
                logger.warning("Twilio credentials not set — using stub mode")
                return {"status": "stub", "message": f"SMS to {phone_number} (stub mode)"}

            client = Client(account_sid, auth_token)
            message = client.messages.create(body=body, from_=from_number, to=phone_number)

            logger.info(f"SMS sent to {phone_number}: SID {message.sid}")
            return {"status": "sent", "sid": message.sid}

        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return {"status": "error", "error": str(e)}


class AlertTemplates:
    """Email/SMS templates for alerts."""

    @staticmethod
    def expiry_warning_email(product_name: str, sku: str, days_left: int, quantity: int) -> str:
        """HTML email template for expiry warning."""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #d9534f;">⏰ Product Expiring Soon</h2>
                <p>The following product is expiring soon:</p>
                <table style="border-collapse: collapse; width: 100%;">
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>Product</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{product_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>SKU</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{sku}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>Days Left</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd;" style="color: #d9534f;"><b>{days_left} days</b></td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>Quantity</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{quantity} units</td>
                    </tr>
                </table>
                <p style="margin-top: 20px; color: #666;">Please take action in RetailSight admin.</p>
            </body>
        </html>
        """

    @staticmethod
    def expiry_warning_sms(product_name: str, days_left: int) -> str:
        """SMS template for expiry warning."""
        return f"{product_name} expires in {days_left} days. Check RetailSight admin."

    @staticmethod
    def waste_alert_email(product_name: str, quantity_wasted: int, reason: str) -> str:
        """HTML email template for waste alert."""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #f0ad4e;">🗑️ Waste Recorded</h2>
                <p>Waste has been recorded:</p>
                <table style="border-collapse: collapse; width: 100%;">
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>Product</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{product_name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>Quantity Wasted</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{quantity_wasted} units</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 8px; border: 1px solid #ddd;"><b>Reason</b></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{reason}</td>
                    </tr>
                </table>
            </body>
        </html>
        """
