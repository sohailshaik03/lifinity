from Retailsights.db_orm import get_session
from Retailsights.models import WasteRecord
from datetime import datetime


def record_waste(product_id, quantity, recorded_at=None):
    session = get_session()
    try:
        wr = WasteRecord(product_id=product_id, quantity_wasted=quantity, recorded_at=recorded_at or datetime.utcnow())
        session.add(wr)
        session.commit()
        session.refresh(wr)
        return wr
    finally:
        session.close()


def get_waste_for_product(product_id, since=None):
    session = get_session()
    try:
        q = session.query(WasteRecord).filter(WasteRecord.product_id == product_id)
        if since:
            q = q.filter(WasteRecord.recorded_at >= since)
        return q.all()
    finally:
        session.close()
