from Retailsights.db_orm import get_session
from Retailsights.models import ExpiryRecord
from datetime import datetime


def record_expiry(product_id, quantity, expired_at=None):
    session = get_session()
    try:
        e = ExpiryRecord(product_id=product_id, quantity=quantity, expired_at=expired_at or datetime.utcnow())
        session.add(e)
        session.commit()
        session.refresh(e)
        return e
    finally:
        session.close()


def get_expiry_for_product(product_id, since=None):
    session = get_session()
    try:
        q = session.query(ExpiryRecord).filter(ExpiryRecord.product_id == product_id)
        if since:
            q = q.filter(ExpiryRecord.expired_at >= since)
        return q.all()
    finally:
        session.close()
