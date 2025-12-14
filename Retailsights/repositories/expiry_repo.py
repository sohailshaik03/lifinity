# repositories/expiry_repo.py
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List

from ..db_orm import get_session
from ..models import ExpiryRecord, WasteRecord, Product
from ..logger import log


def get_expiring_batches(shop_id: int, days_ahead: int = 3) -> List[Dict[str, Any]]:
    """Return batches expiring within N days for a shop using ORM."""
    today = date.today()
    cutoff = today + timedelta(days=days_ahead)

    session = get_session()
    try:
        rows = (
            session.query(ExpiryRecord, Product)
            .join(Product, ExpiryRecord.product_id == Product.id)
            .filter(Product.shop_id == shop_id)
            .filter(ExpiryRecord.expiry_date != None)
            .filter(ExpiryRecord.expiry_date >= today)
            .filter(ExpiryRecord.expiry_date <= cutoff)
            .filter(ExpiryRecord.status.in_(("active", "reduced")))
            .order_by(ExpiryRecord.expiry_date.asc())
            .all()
        )
        result: List[Dict[str, Any]] = []
        for er, p in rows:
            result.append({
                "id": er.id,
                "product_id": er.product_id,
                "product_name": p.name,
                "batch_number": er.batch_number,
                "expiry_date": er.expiry_date,
                "quantity_remaining": er.quantity_remaining,
                "status": er.status,
            })
        return result
    except Exception as e:
        log.exception("Failed to load expiring batches: %s", e)
        raise
    finally:
        session.close()


def get_recent_waste_events(shop_id: int, days_back: int = 30) -> List[Dict[str, Any]]:
    """Return waste events for a shop for the last N days using ORM."""
    cutoff = date.today() - timedelta(days=days_back)
    session = get_session()
    try:
        rows = (
            session.query(WasteRecord, Product)
            .join(Product, WasteRecord.product_id == Product.id)
            .filter(Product.shop_id == shop_id)
            .filter(WasteRecord.recorded_at != None)
            .filter(WasteRecord.recorded_at >= cutoff)
            .order_by(WasteRecord.recorded_at.desc())
            .all()
        )
        result: List[Dict[str, Any]] = []
        for w, p in rows:
            result.append({
                "id": w.id,
                "product_id": w.product_id,
                "product_name": p.name,
                "quantity_wasted": w.quantity_wasted,
                "reason": w.reason,
                "recorded_at": w.recorded_at,
            })
        return result
    except Exception as e:
        log.exception("Failed to load waste events: %s", e)
        raise
    finally:
        session.close()
