"""SQLAlchemy ORM models for RetailSights application.

Defines database schema for users, shops, products, sales, waste tracking,
and markdown sales. Uses declarative base pattern for clean model definition.
"""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, Table
from sqlalchemy.orm import relationship, declarative_base, Mapped

if TYPE_CHECKING:
    from sqlalchemy.orm import RelationshipProperty

Base = declarative_base()

# Association table for many-to-many relationship between users and shops
user_shops = Table(
    'user_shops',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('shop_id', Integer, ForeignKey('shops.id'), primary_key=True)
)


class User(Base):
    """User model representing system users (admin, manager, staff).
    
    Attributes:
        id: Primary key
        email: Unique email address for login
        password_hash: Bcrypt hashed password (never store plain text)
        full_name: User's display name
        role: User role (admin, manager, user)
        is_active: Account status flag
        created_at: Account creation timestamp
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="user", nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Shop(Base):
    """Shop/store location model.
    
    Represents a physical retail location with products and sales.
    Each shop can have multiple users assigned and tracks its own inventory.
    
    Attributes:
        id: Primary key
        name: Shop display name
        address: Street address
        city: City name
        country: Country name
        created_at: Shop registration timestamp
        owner_user_id: Reference to owning user (optional)
        owner: Relationship to User model
    """
    __tablename__ = "shops"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    address = Column(Text)
    city = Column(String(100))
    country = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", backref="shops")


class Product(Base):
    """Product catalog model.
    
    Represents items sold in shops. Each product belongs to a specific shop
    and tracks SKU, pricing, and other attributes.
    
    Attributes:
        id: Primary key
        shop_id: Reference to owning shop
        name: Product display name
        sku: Stock keeping unit identifier
        default_cost: Default product cost/price
        created_at: Product creation timestamp
        shop: Relationship to Shop model
    """
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sku = Column(String(100), index=True)
    default_cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    shop = relationship("Shop", backref="products")


class SalesTransaction(Base):
    __tablename__ = "sales_transactions"
    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    transaction_dt = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Float, default=0.0)
    shop = relationship("Shop", backref="sales_transactions")


class SalesLine(Base):
    __tablename__ = "sales_lines"
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey("sales_transactions.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, default=0.0)
    unit_price = Column(Float, default=0.0)
    product = relationship("Product", backref="sales_lines")
    transaction = relationship("SalesTransaction", backref="lines")


class WasteRecord(Base):
    __tablename__ = "waste_records"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    expiry_record_id = Column(Integer, ForeignKey("expiry_records.id"), nullable=True)
    quantity_wasted = Column(Float, default=0.0)
    reason = Column(String(255), nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product", backref="waste_records")


class MarkdownSale(Base):
    __tablename__ = "markdown_sales"
    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    sold_at = Column(DateTime, default=datetime.utcnow)
    # Extended fields for compatibility with existing codepaths
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    sku = Column(String(100), nullable=True)
    original_price = Column(Float, nullable=True)
    discounted_price = Column(Float, default=0.0)
    quantity_sold = Column(Integer, default=0)
    discount_percent = Column(Float, nullable=True)
    discount_amount = Column(Float, nullable=True)
    rule_id = Column(Integer, nullable=True)
    rule_name = Column(String(255), nullable=True)
    expiry_record_id = Column(Integer, ForeignKey("expiry_records.id"), nullable=True)
    sold_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    shop = relationship("Shop", backref="markdown_sales")


class ExpiryRecord(Base):
    __tablename__ = "expiry_records"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    batch_number = Column(String(100), nullable=True)
    quantity_received = Column(Integer, nullable=True)
    quantity_remaining = Column(Integer, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    received_date = Column(DateTime, nullable=True)
    days_left = Column(Integer, nullable=True)
    status = Column(String(32), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product", backref="expiry_records")
