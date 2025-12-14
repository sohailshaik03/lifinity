# repositories/shops_repo.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
import streamlit as st
from sqlalchemy import text

from ..db_orm import get_session
from ..logger import log
from ..models import Shop


class ShopsRepository:
    """Data access layer for shops using SQLAlchemy sessions."""

    @staticmethod
    @st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
    def get_all_shops() -> List[Dict[str, Any]]:
        session = get_session()
        try:
            shops = session.query(Shop).order_by(Shop.name).all()
            result: List[Dict[str, Any]] = []
            for s in shops:
                result.append(
                    {
                        "id": s.id,
                        "name": s.name,
                        "address": s.address,
                        "city": s.city,
                        "country": s.country,
                        "created_at": s.created_at,
                    }
                )
            return result
        except Exception as e:
            log.exception("Failed to fetch shops: %s", e)
            return []
        finally:
            session.close()

    @staticmethod
    @st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
    def get_shop_by_id(shop_id: int) -> Optional[Dict[str, Any]]:
        session = get_session()
        try:
            s = session.get(Shop, shop_id)
            if not s:
                return None
            return {
                "id": s.id,
                "name": s.name,
                "address": s.address,
                "city": s.city,
                "country": s.country,
                "created_at": s.created_at,
            }
        except Exception as e:
            log.exception("Failed to fetch shop: %s", e)
            return None
        finally:
            session.close()

    @staticmethod
    def create_shop(
        name: str,
        address_line1: str = "",
        city: str = "",
        postcode: str = "",
        country: str = "",
    ) -> Optional[int]:
        session = get_session()
        try:
            address = address_line1
            shop = Shop(name=name, address=address, city=city, country=country)
            session.add(shop)
            session.commit()
            session.refresh(shop)
            log.info("Shop created: %s (ID: %s)", name, shop.id)
            # Clear cache after creating new shop
            st.cache_data.clear()
            return shop.id
        except Exception as e:
            session.rollback()
            log.exception("Failed to create shop: %s", e)
            return None
        finally:
            session.close()

    @staticmethod
    def update_shop(
        shop_id: int,
        name: str = None,
        address_line1: str = None,
        city: str = None,
        postcode: str = None,
        country: str = None,
    ) -> bool:
        session = get_session()
        try:
            shop = session.get(Shop, shop_id)
            if not shop:
                return False
            if name is not None:
                shop.name = name
            if address_line1 is not None:
                shop.address = address_line1
            if city is not None:
                shop.city = city
            if country is not None:
                shop.country = country
            session.commit()
            log.info("Shop updated: ID %s", shop_id)
            # Clear cache after updating shop
            st.cache_data.clear()
            return True
        except Exception as e:
            session.rollback()
            log.exception("Failed to update shop: %s", e)
            return False
        finally:
            session.close()

    @staticmethod
    def delete_shop(shop_id: int) -> bool:
        session = get_session()
        try:
            shop = session.get(Shop, shop_id)
            if not shop:
                return False
            session.delete(shop)
            session.commit()
            log.info("Shop deleted: ID %s", shop_id)
            return True
        except Exception as e:
            session.rollback()
            log.exception("Failed to delete shop: %s", e)
            return False
        finally:
            session.close()

    @st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
    @staticmethod
    def get_user_shops(user_id: int) -> List[Dict[str, Any]]:
        session = get_session()
        try:
            rows = (
                session.execute(
                    text("SELECT DISTINCT s.id, s.name, s.address, s.city, s.country, s.created_at FROM shops s JOIN user_shops us ON us.shop_id = s.id WHERE us.user_id = :uid ORDER BY s.name"),
                    {"uid": user_id},
                )
                .mappings()
                .all()
            )
            return [dict(r) for r in rows]
        except Exception as e:
            log.exception("Failed to fetch user shops: %s", e)
            return []
        finally:
            session.close()

    @staticmethod
    def assign_user_to_shop(user_id: int, shop_id: int) -> bool:
        session = get_session()
        try:
            session.execute(
                text("INSERT INTO user_shops (user_id, shop_id) VALUES (:uid, :sid) ON CONFLICT DO NOTHING"),
                {"uid": user_id, "sid": shop_id},
            )
            # Clear cache after user assignment
            st.cache_data.clear()
            session.commit()
            log.info("User %s assigned to shop %s", user_id, shop_id)
            return True
        except Exception as e:
            session.rollback()
            log.exception("Failed to assign user to shop: %s", e)
            return False
        finally:
            session.close()

    @staticmethod
    def remove_user_from_shop(user_id: int, shop_id: int) -> bool:
        session = get_session()
        try:
            session.execute(
                text("DELETE FROM user_shops WHERE user_id = :uid AND shop_id = :sid"),
                {"uid": user_id, "sid": shop_id},
            )
            session.commit()
            log.info("User %s removed from shop %s", user_id, shop_id)
            return True
        except Exception as e:
            session.rollback()
            log.exception("Failed to remove user from shop: %s", e)
            return False
        finally:
            session.close()
