from Retailsights.db_orm import get_session
from Retailsights.models import MarkdownSale
from datetime import datetime


def record_markdown(shop_id, discounted_price, quantity_sold=1, sold_at=None):
    session = get_session()
    try:
        m = MarkdownSale(shop_id=shop_id, discounted_price=discounted_price, quantity_sold=quantity_sold, sold_at=sold_at or datetime.utcnow())
        session.add(m)
        session.commit()
        session.refresh(m)
        return m
    finally:
        session.close()


def recent_markdowns(shop_id, days=None):
    session = get_session()
    try:
        q = session.query(MarkdownSale).filter(MarkdownSale.shop_id == shop_id)
        return q.order_by(MarkdownSale.sold_at.desc()).limit(100).all()
    finally:
        session.close()
