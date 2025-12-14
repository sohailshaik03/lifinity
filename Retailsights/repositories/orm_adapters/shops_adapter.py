from Retailsights.db_orm import get_session
from Retailsights.models import Shop


def get_all_shops():
    session = get_session()
    try:
        return session.query(Shop).all()
    finally:
        session.close()


def create_shop(name, address=None, city=None, country=None, owner_user_id=None):
    session = get_session()
    try:
        shop = Shop(name=name, address=address, city=city, country=country, owner_user_id=owner_user_id)
        session.add(shop)
        session.commit()
        session.refresh(shop)
        return shop
    finally:
        session.close()
