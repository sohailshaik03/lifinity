from __future__ import annotations

from typing import Any, Dict, List, Optional
from ..db_orm import get_session
from ..models import Product, ExpiryRecord, WasteRecord
from ..logger import logger
from ..utils.cache_manager import cache
from datetime import datetime, timedelta
from sqlalchemy import func, select, text
import streamlit as st


def create_product(
    shop_id: int,
    sku: str,
    name: str,
    category: str | None = None,
    cost_price: float | None = None,
    selling_price: float | None = None,
) -> Optional[int]:
    session = get_session()
    try:
        p = Product(shop_id=shop_id, name=name, sku=sku, default_cost=(cost_price or 0.0))
        session.add(p)
        session.commit()
        session.refresh(p)
        return p.id
    except Exception as e:
        logger.error(f"create_product error: {e}")
        session.rollback()
        return None
    finally:
        session.close()


@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def get_products_by_shop(shop_id: int, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get products for a shop with optional pagination.
    
    Args:
        shop_id: Shop ID
        limit: Max number of products to return (None = all)
        offset: Number of products to skip
    """
    session = get_session()
    try:
        # Optimized query - join with aggregated stock in single query
        query = (
            session.query(
                Product.id,
                Product.name,
                Product.sku,
                Product.default_cost,
                Product.created_at,
                func.coalesce(func.sum(ExpiryRecord.quantity), 0).label('current_stock')
            )
            .outerjoin(ExpiryRecord, Product.id == ExpiryRecord.product_id)
            .filter(Product.shop_id == shop_id)
            .group_by(Product.id, Product.name, Product.sku, Product.default_cost, Product.created_at)
            .order_by(Product.name)
        )
        
        # Apply pagination if specified
        if limit is not None:
            query = query.limit(limit).offset(offset)
        
        products_with_stock = query.all()
        
        result: List[Dict[str, Any]] = []
        for row in products_with_stock:
            result.append({
                "id": row.id,
                "name": row.name,
                "sku": row.sku,
                "cost_price": row.default_cost,
                "current_stock": row.current_stock,
                "created_at": row.created_at,
            })
        return result
    except Exception as e:
        logger.error(f"get_products_by_shop error: {e}")
        return []
    finally:
        session.close()


@st.cache_data(ttl=300, show_spinner=False)
def get_products_count(shop_id: int) -> int:
    """Get total count of products for a shop."""
    session = get_session()
    try:
        count = session.query(func.count(Product.id)).filter(Product.shop_id == shop_id).scalar()
        return count or 0
    except Exception as e:
        logger.error(f"get_products_count error: {e}")
        return 0
    finally:
        session.close()


@st.cache_data(ttl=60, show_spinner=False)  # Cache for 1 minute
def get_expiring_products(shop_id: int, days_threshold: int = 30) -> List[Dict[str, Any]]:
    """Get products expiring within days_threshold."""
    session = get_session()
    try:
        cutoff = datetime.utcnow() + timedelta(days=days_threshold)
        # Optimized: Select only needed columns
        rows = (
            session.query(
                Product.id,
                Product.sku,
                Product.name,
                ExpiryRecord.quantity,
                ExpiryRecord.id.label('expiry_id'),
                ExpiryRecord.expired_at
            )
            .join(ExpiryRecord, Product.id == ExpiryRecord.product_id)
            .filter(Product.shop_id == shop_id)
            .filter(ExpiryRecord.expired_at <= cutoff)
            .order_by(ExpiryRecord.expired_at.asc())
            .all()
        )
        result: List[Dict[str, Any]] = []
        for row in rows:
            result.append({
                "id": row.id,
                "sku": row.sku,
                "name": row.name,
                "current_stock": row.quantity,
                "expiry_id": row.expiry_id,
                "expiry_date": row.expired_at,
            })
        return result
    except Exception as e:
        logger.error(f"get_expiring_products error: {e}")
        return []
    finally:
        session.close()


def add_expiry_record(
    product_id: int,
    quantity_received: int,
    expiry_date: str,
    batch_number: str | None = None,
    received_date: str | None = None,
) -> Optional[int]:
    session = get_session()
    try:
        try:
            exp_dt = datetime.fromisoformat(expiry_date)
        except Exception:
            exp_dt = datetime.utcnow()
        er = ExpiryRecord(product_id=product_id, expired_at=exp_dt, quantity=quantity_received)
        session.add(er)
        session.commit()
        session.refresh(er)
        return er.id
    except Exception as e:
        logger.error(f"add_expiry_record error: {e}")
        session.rollback()
        return None
    finally:
        session.close()


def decrement_expiring_stock(product_id: int, quantity: int = 1) -> bool:
    """Decrement quantity_remaining from the nearest active expiry record for a product.
    Returns True on success, False otherwise."""
    session = get_session()
    try:
        er = (
            session.query(ExpiryRecord)
            .filter(ExpiryRecord.product_id == product_id)
            .filter(ExpiryRecord.quantity > 0)
            .order_by(ExpiryRecord.expired_at.asc())
            .with_for_update()
            .first()
        )
        if not er:
            return False
        er.quantity = max(0, er.quantity - quantity)
        session.commit()
        return True
    except Exception as e:
        logger.error(f"decrement_expiring_stock error: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def record_waste(
    product_id: int,
    quantity_wasted: int,
    reason: str,
    expiry_record_id: int | None = None,
    user_id: int | None = None,
) -> Optional[int]:
    session = get_session()
    try:
        # find expiry record if not provided
        er = None
        if expiry_record_id:
            er = session.get(ExpiryRecord, expiry_record_id)
        else:
            er = (
                session.query(ExpiryRecord)
                .filter(ExpiryRecord.product_id == product_id)
                .filter(ExpiryRecord.quantity > 0)
                .order_by(ExpiryRecord.expired_at.asc())
                .first()
            )
        wr = WasteRecord(
            product_id=product_id, 
            quantity_wasted=quantity_wasted,
            reason=reason,
            expiry_record_id=expiry_record_id,
            recorded_by=user_id
        )
        session.add(wr)
        if er:
            er.quantity = max(0, er.quantity - quantity_wasted)
        session.commit()
        session.refresh(wr)
        return wr.id
    except Exception as e:
        logger.error(f"record_waste error: {e}")
        session.rollback()
        return None
    finally:
        session.close()


def get_waste_records(shop_id: int, days: int = 7) -> List[Dict[str, Any]]:
    """Get waste records from last N days."""
    session = get_session()
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        rows = (
            session.query(WasteRecord)
            .join(Product, WasteRecord.product_id == Product.id)
            .filter(Product.shop_id == shop_id)
            .filter(WasteRecord.recorded_at >= cutoff)
            .order_by(WasteRecord.recorded_at.desc())
            .all()
        )
        result: List[Dict[str, Any]] = []
        for w in rows:
            result.append({
                "id": w.id,
                "product_id": w.product_id,
                "quantity_wasted": w.quantity_wasted,
                "recorded_at": w.recorded_at,
            })
        return result
    except Exception as e:
        logger.error(f"get_waste_records error: {e}")
        return []
    finally:
        session.close()


def get_discount_rules(shop_id: int) -> List[Dict[str, Any]]:
    session = get_session()
    try:
        result = session.execute(
            text("SELECT * FROM discount_rules WHERE shop_id = :shop_id AND active = 1 ORDER BY days_left_min DESC"),
            {"shop_id": shop_id}
        )
        return [dict(row._mapping) for row in result.fetchall()]
    except Exception as e:
        logger.error(f"get_discount_rules error: {e}")
        return []
    finally:
        session.close()


def create_discount_rule(
    shop_id: int,
    name: str,
    days_left_min: int,
    days_left_max: int,
    quantity_min: int,
    discount_percent: float,
) -> Optional[int]:
    session = get_session()
    try:
        result = session.execute(
            text("""
            INSERT INTO discount_rules (shop_id, name, days_left_min, days_left_max,
                                       quantity_min, discount_percent)
            VALUES (:shop_id, :name, :days_left_min, :days_left_max, :quantity_min, :discount_percent)
            """),
            {
                "shop_id": shop_id,
                "name": name,
                "days_left_min": days_left_min,
                "days_left_max": days_left_max,
                "quantity_min": quantity_min,
                "discount_percent": discount_percent
            }
        )
        session.commit()
        return result.lastrowid
    except Exception as e:
        logger.error(f"create_discount_rule error: {e}")
        session.rollback()
        return None
    finally:
        session.close()
