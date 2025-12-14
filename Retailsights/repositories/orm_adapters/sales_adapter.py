from Retailsights.db_orm import get_session
from Retailsights.models import SalesTransaction, SalesLine
from datetime import datetime


def create_transaction(shop_id, lines):
    """Create a transaction and its lines.

    `lines` is a list of dicts: [{"product_id": int, "quantity": float, "unit_price": float}, ...]
    """
    session = get_session()
    try:
        total = sum(l.get('quantity', 0) * l.get('unit_price', 0) for l in lines)
        tx = SalesTransaction(shop_id=shop_id, transaction_dt=datetime.utcnow(), total_amount=total)
        session.add(tx)
        session.flush()
        for l in lines:
            sl = SalesLine(transaction_id=tx.id, product_id=l['product_id'], quantity=l.get('quantity', 0), unit_price=l.get('unit_price', 0))
            session.add(sl)
        session.commit()
        session.refresh(tx)
        return tx
    finally:
        session.close()


def get_transactions_for_shop(shop_id, limit=100):
    session = get_session()
    try:
        return session.query(SalesTransaction).filter(SalesTransaction.shop_id == shop_id).order_by(SalesTransaction.transaction_dt.desc()).limit(limit).all()
    finally:
        session.close()
