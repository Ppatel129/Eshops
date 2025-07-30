from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from database import Base

class Shop(Base):
    __tablename__ = "shops"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    xml_url = Column(String(500), nullable=False)
    last_sync = Column(DateTime, default=datetime.utcnow)
    sync_status = Column(String(50), default="pending")
    error_message = Column(Text)
    total_products = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = relationship("Product", back_populates="shop", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Shop(id={self.id}, name='{self.name}')>"

class Brand(Base):
    __tablename__ = "brands"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    normalized_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    products = relationship("Product", back_populates="brand")
    
    # Index for search performance
    __table_args__ = (
        Index('idx_brands_name', 'name'),
        Index('idx_brands_normalized', 'normalized_name'),
    )

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), nullable=False)
    path = Column(String(1000))  # Full category path
    level = Column(Integer, default=0)
    parent_id = Column(Integer, ForeignKey('categories.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    parent = relationship("Category", remote_side=[id])
    children = relationship("Category", back_populates="parent")
    products = relationship("Product", back_populates="category")
    
    # Index for search performance
    __table_args__ = (
        Index('idx_categories_name', 'name'),
        Index('idx_categories_path', 'path'),
        Index('idx_categories_normalized', 'normalized_name'),
        # Add unique constraint to prevent duplicate categories with same name and path
        Index('idx_categories_unique', 'normalized_name', 'path', unique=True),
    )

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    
    # Basic product info
    title = Column(String(1000), nullable=False)
    description = Column(Text)
    ean = Column(String(50))
    mpn = Column(String(100))
    sku = Column(String(100))
    
    # Pricing
    price = Column(Float)
    original_price = Column(Float)
    discount_percentage = Column(Float)
    
    # Availability
    availability = Column(Boolean, default=False)
    stock_quantity = Column(Integer)
    
    # Images and media
    image_url = Column(String(1000))
    additional_images = Column(JSON)
    
    # SEO and URLs
    product_url = Column(String(1000))
    deeplink = Column(String(1000))
    
    # Specifications and features
    specifications = Column(JSONB)
    features = Column(JSONB)
    
    # Search and categorization
    search_text = Column(Text)  # Denormalized search field
    tags = Column(JSON)
    
    # Relationships
    shop_id = Column(Integer, ForeignKey('shops.id'), nullable=False)
    brand_id = Column(Integer, ForeignKey('brands.id'))
    category_id = Column(Integer, ForeignKey('categories.id'))
    
    shop = relationship("Shop", back_populates="products")
    brand = relationship("Brand", back_populates="products")
    category = relationship("Category", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for search performance
    __table_args__ = (
        Index('idx_products_ean', 'ean'),
        Index('idx_products_mpn', 'mpn'),
        Index('idx_products_title', 'title'),
        Index('idx_products_price', 'price'),
        Index('idx_products_availability', 'availability'),
        Index('idx_products_shop_id', 'shop_id'),
        Index('idx_products_brand_id', 'brand_id'),
        Index('idx_products_category_id', 'category_id'),
        Index('idx_products_search_text', 'search_text'),
        Index('idx_products_specifications', 'specifications', postgresql_using='gin'),
    )

class ProductVariant(Base):
    __tablename__ = "product_variants"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    # Variant attributes
    color = Column(String(100))
    size = Column(String(100))
    material = Column(String(100))
    style = Column(String(100))
    
    # Variant-specific data
    ean = Column(String(50))
    sku = Column(String(100))
    price = Column(Float)
    availability = Column(Boolean, default=False)
    stock_quantity = Column(Integer)
    image_url = Column(String(1000))
    
    # Additional variant attributes
    attributes = Column(JSONB)
    
    # Relationships
    product = relationship("Product", back_populates="variants")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_variants_product_id', 'product_id'),
        Index('idx_variants_ean', 'ean'),
        Index('idx_variants_color', 'color'),
        Index('idx_variants_size', 'size'),
        Index('idx_variants_availability', 'availability'),
        Index('idx_variants_attributes', 'attributes', postgresql_using='gin'),
    )
