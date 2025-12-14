from Retailsights.db_orm import get_session
from Retailsights.models import Product


def get_products_by_shop(shop_id):
    session = get_session()
    try:
        return session.query(Product).filter(Product.shop_id == shop_id).all()
    finally:
        session.close()


def create_product(shop_id, name, sku=None, default_cost=0.0):
    session = get_session()
    try:
        p = Product(shop_id=shop_id, name=name, sku=sku, default_cost=default_cost)
        session.add(p)
        session.commit()
        session.refresh(p)
        return p
    finally:
        session.close()
