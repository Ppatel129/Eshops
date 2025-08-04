from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class ShopBase(BaseModel):
    name: str
    xml_url: str

class ShopCreate(ShopBase):
    pass

class Shop(ShopBase):
    id: int
    last_sync: Optional[datetime] = None
    sync_status: str = "pending"
    error_message: Optional[str] = None
    total_products: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BrandBase(BaseModel):
    name: str
    normalized_name: str

class BrandCreate(BrandBase):
    pass

class Brand(BrandBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    name: str
    normalized_name: str
    path: Optional[str] = None
    level: int = 0
    parent_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ProductVariantBase(BaseModel):
    color: Optional[str] = None
    size: Optional[str] = None
    material: Optional[str] = None
    style: Optional[str] = None
    ean: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None
    availability: bool = False
    stock_quantity: Optional[int] = None
    image_url: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

class ProductVariantCreate(ProductVariantBase):
    pass

class ProductVariant(ProductVariantBase):
    id: int
    product_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    title: str
    description: Optional[str] = None
    ean: Optional[str] = None
    mpn: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    availability: bool = False
    stock_quantity: Optional[int] = None
    image_url: Optional[str] = None
    additional_images: Optional[List[str]] = None
    product_url: Optional[str] = None
    deeplink: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    features: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

class ProductCreate(ProductBase):
    shop_id: int
    brand_id: Optional[int] = None
    category_id: Optional[int] = None

class Product(ProductBase):
    id: int
    shop_id: int
    brand_id: Optional[int] = None
    category_id: Optional[int] = None
    shop: Optional[Shop] = None
    brand: Optional[Brand] = None
    category: Optional[Category] = None
    variants: List[ProductVariant] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SearchFilters(BaseModel):
    title: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    brands: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    availability: Optional[bool] = None
    ean: Optional[str] = None
    mpn: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    shops: Optional[List[str]] = None
    sort: Optional[str] = "relevance"

    @validator('min_price', 'max_price')
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Price must be non-negative')
        return v

class CategoryDistribution(BaseModel):
    """Schema for category distribution data"""
    category_id: int
    category_name: str
    category_name_en: Optional[str] = None  # English translation
    count: int
    percentage: float
    representative_image: Optional[str] = None  # Representative product image URL

class SearchResponse(BaseModel):
    products: List[Product]
    total: int
    page: int
    per_page: int
    total_pages: int
    filters_applied: Dict[str, Any]
    execution_time_ms: float
    facets: Optional[Dict[str, Any]] = None
    category_distribution: Optional[List[CategoryDistribution]] = None  # Top 10 categories

class FeedProcessResult(BaseModel):
    shop_name: str
    status: str
    products_processed: int
    products_created: int
    products_updated: int
    errors: List[str]
    processing_time_seconds: float
    timestamp: datetime