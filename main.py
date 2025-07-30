import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse


from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, init_db, close_db
from models import Product, Shop, Brand, Category
from schemas import (
    SearchFilters, SearchResponse, Product as ProductSchema, 
    Shop as ShopSchema, ShopCreate, FeedProcessResult
)
from search_service import SearchService
from feed_scheduler import FeedProcessor, scheduler
from config import settings
from elasticsearch_service import elasticsearch_service
from typing import List, Optional, Dict, Any
from pathlib import Path
import uvicorn

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Initialize Elasticsearch (optional)
        try:
            es_connected = await elasticsearch_service.connect()
            if es_connected:
                await elasticsearch_service.create_index()
                logger.info("Elasticsearch initialized")
            else:
                logger.info("Elasticsearch not available - using PostgreSQL search only")
        except Exception as e:
            logger.warning(f"Elasticsearch initialization failed: {e} - using PostgreSQL search only")
        
        # Start background feed scheduler
        asyncio.create_task(scheduler.start())
        logger.info("Feed scheduler started")
        
        yield
    finally:
        # Cleanup
        scheduler.stop()
        try:
            await elasticsearch_service.close()
        except:
            pass
        await close_db()
        logger.info("Application shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="E-commerce Product Search API",
    description="Scalable product search system with XML feed processing",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# API Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main search interface"""
    try:
        index_file = Path("static/index.html")
        if index_file.exists():
            with index_file.open("r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        else:
            return HTMLResponse(content="<h1>index.html not found</h1>", status_code=404)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error loading index.html: {e}</h1>", status_code=500)

@app.get("/admin", response_class=HTMLResponse)
async def admin():
    """Serve the admin dashboard"""
    with open("static/admin.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/search")
async def unified_search(
    q: Optional[str] = Query(None, description="Search query"),
    type: Optional[str] = Query("all", description="Search type: all, products, categories"),
    title: Optional[str] = Query(None, description="Search in product title"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brands: Optional[List[str]] = Query(None, description="Filter by multiple brands"),
    categories: Optional[List[str]] = Query(None, description="Filter by multiple categories"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    availability: Optional[bool] = Query(None, description="Filter by availability"),
    ean: Optional[str] = Query(None, description="Search by EAN code"),
    mpn: Optional[str] = Query(None, description="Search by MPN"),
    color: Optional[str] = Query(None, description="Filter by color"),
    size: Optional[str] = Query(None, description="Filter by size"),
    shops: Optional[List[str]] = Query(None, description="Filter by multiple shops"),
    sort: Optional[str] = Query("relevance", description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    db: AsyncSession = Depends(get_db)
):
    """Unified search for products and categories with multi-shop aggregation"""
    try:
        search_service = SearchService(db)
        
        # Build filters - handle both single and multi-select
        filters = SearchFilters(
            title=q or title,
            brand=brand,
            category=category,
            brands=brands,
            categories=categories,
            min_price=min_price,
            max_price=max_price,
            availability=availability,
            ean=ean,
            mpn=mpn,
            color=color,
            size=size,
            shops=shops
        )
        
        if type == "categories":
            # Search only categories
            categories = await search_service.search_categories(q or "", per_page)
            return {
                "type": "categories",
                "categories": categories,
                "total": len(categories),
                "page": page,
                "per_page": per_page
            }
        elif type == "products":
            # Search only products with multi-shop aggregation
            results = await search_service.search_products_aggregated(filters, page, per_page, sort)
            return results
        else:
            # Unified search (default)
            products = await search_service.search_products_aggregated(filters, page, min(per_page // 2, 20), sort)
            categories = await search_service.search_categories(q or "", min(per_page // 2, 12))
            
            return {
                "type": "unified",
                "products": products,
                "categories": categories,
                "page": page,
                "per_page": per_page
            }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search service error")

@app.get("/categories/search")
async def search_categories(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=20, description="Maximum categories"),
    db: AsyncSession = Depends(get_db)
):
    """Search categories with Elasticsearch support"""
    try:
        # Try Elasticsearch first
        if elasticsearch_service.client:
            categories = await elasticsearch_service.search_categories(q, limit)
            if categories:
                return categories
        
        # Fallback to PostgreSQL category search
        search_service = SearchService(db)
        categories = await search_service.search_categories(q, limit)
        
        return categories
        
    except Exception as e:
        logger.error(f"Category search error: {e}")
        raise HTTPException(status_code=500, detail="Category search service error")

@app.get("/product/{product_id}", response_model=ProductSchema)
async def get_product_by_id(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get product by ID"""
    try:
        search_service = SearchService(db)
        product = await search_service.get_product_by_id(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product by ID {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Product retrieval error")

@app.get("/product/ean/{ean}", response_model=ProductSchema)
async def get_product_by_ean(
    ean: str,
    db: AsyncSession = Depends(get_db)
):
    """Get product by EAN code"""
    try:
        search_service = SearchService(db)
        product = await search_service.get_product_by_ean(ean)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product by EAN {ean}: {e}")
        raise HTTPException(status_code=500, detail="Product retrieval error")

@app.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=20, description="Maximum suggestions"),
    db: AsyncSession = Depends(get_db)
):
    """Get search suggestions with Elasticsearch fallback"""
    try:
        # Try Elasticsearch first
        # if elasticsearch_service.client:
        #     suggestions = await elasticsearch_service.get_suggestions(q, limit)
        #     if suggestions:
        #         return suggestions
        
        # Fallback to PostgreSQL
        search_service = SearchService(db)
        suggestions = await search_service.get_search_suggestions(q, limit)
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        raise HTTPException(status_code=500, detail="Suggestions service error")

@app.get("/facets")
async def get_search_facets(
    title: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    availability: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get search facets for filtering"""
    try:
        filters = SearchFilters(
            title=title,
            brand=brand,
            category=category,
            min_price=min_price,
            max_price=max_price,
            availability=availability
        )
        
        search_service = SearchService(db)
        facets = await search_service.get_facets(filters)
        
        return facets
        
    except Exception as e:
        logger.error(f"Error getting facets: {e}")
        raise HTTPException(status_code=500, detail="Facets service error")

@app.get("/shops", response_model=List[ShopSchema])
async def get_shops(db: AsyncSession = Depends(get_db)):
    """Get all shops"""
    try:
        from sqlalchemy import select
        result = await db.execute(select(Shop))
        shops = result.scalars().all()
        
        return [ShopSchema.from_orm(shop) for shop in shops]
        
    except Exception as e:
        logger.error(f"Error getting shops: {e}")
        raise HTTPException(status_code=500, detail="Shop retrieval error")

@app.post("/shops", response_model=ShopSchema, status_code=201)
async def create_shop(shop: ShopCreate, db: AsyncSession = Depends(get_db)):
    """Create a new shop."""
    try:
        # Check for duplicate shop name
        from sqlalchemy import select
        result = await db.execute(select(Shop).where(Shop.name == shop.name))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Shop with this name already exists")
        new_shop = Shop(name=shop.name, xml_url=shop.xml_url)
        db.add(new_shop)
        await db.commit()
        await db.refresh(new_shop)
        return ShopSchema.from_orm(new_shop)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating shop: {e}")
        raise HTTPException(status_code=500, detail="Shop creation error")

@app.delete("/shops/{shop_id}", status_code=204)
async def delete_shop(shop_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a shop by ID, including all its products (cascade)."""
    try:
        from sqlalchemy import select, delete
        # Check if shop exists
        result = await db.execute(select(Shop).where(Shop.id == shop_id))
        shop = result.scalar_one_or_none()
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        # Delete the shop (products will be deleted via cascade)
        await db.delete(shop)
        await db.commit()
        return
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting shop {shop_id}: {e}")
        raise HTTPException(status_code=500, detail="Shop deletion error")

@app.post("/admin/process-feeds", response_model=List[FeedProcessResult])
async def process_feeds(background_tasks: BackgroundTasks):
    """Manually trigger feed processing"""
    try:
        processor = FeedProcessor()
        results = await processor.process_all_feeds()
        
        return results
        
    except Exception as e:
        logger.error(f"Error processing feeds: {e}")
        raise HTTPException(status_code=500, detail="Feed processing error")

@app.get("/admin/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get system statistics"""
    try:
        from sqlalchemy import select, func
        
        # Get counts
        shop_count = await db.execute(select(func.count(Shop.id)))
        product_count = await db.execute(select(func.count(Product.id)))
        brand_count = await db.execute(select(func.count(Brand.id)))
        category_count = await db.execute(select(func.count(Category.id)))
        
        # Get latest sync info
        latest_sync = await db.execute(
            select(Shop.last_sync, Shop.sync_status)
            .order_by(Shop.last_sync.desc())
            .limit(1)
        )
        sync_info = latest_sync.first()
        
        return {
            "shops": shop_count.scalar(),
            "products": product_count.scalar(),
            "brands": brand_count.scalar(),
            "categories": category_count.scalar(),
            "last_sync": sync_info[0] if sync_info else None,
            "sync_status": sync_info[1] if sync_info else None
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Stats retrieval error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2025-01-03T12:00:00Z"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False,
        log_level=settings.LOG_LEVEL.lower()
    )

@app.post("/image-search")
async def image_search(image: UploadFile = File(...)):
    contents = await image.read()
    # Process the image...
    return JSONResponse({"filename": image.filename, "message": "Image received"})