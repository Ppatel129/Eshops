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
from sqlalchemy import select, func

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

@app.get("/terms", response_class=HTMLResponse)
async def terms():
    """Serve the terms of service page"""
    with open("static/terms.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/privacy", response_class=HTMLResponse)
async def privacy():
    """Serve the privacy policy page"""
    with open("static/privacy.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/all-products")
async def get_all_products(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    db: AsyncSession = Depends(get_db)
):
    """Get all products without any filters - for testing"""
    try:
        # Get total count
        count_result = await db.execute(select(func.count()).select_from(Product))
        total = count_result.scalar()
        
        # Get products with pagination
        offset = (page - 1) * per_page
        query = select(Product).offset(offset).limit(per_page)
        
        result = await db.execute(query)
        products = result.scalars().all()
        
        # Convert to response format
        product_list = []
        for product in products:
            product_data = {
                "id": product.id,
                "title": product.title,
                "description": product.description,
                "price": float(product.price) if product.price else None,
                "image_url": product.image_url,
                "availability": product.availability,
                "ean": product.ean,
                "mpn": product.mpn,
                "shop": {"name": product.shop.name} if product.shop else None,
                "brand": {"name": product.brand.name} if product.brand else None,
                "category": {"name": product.category.name} if product.category else None,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None
            }
            product_list.append(product_data)
        
        total_pages = (total + per_page - 1) // per_page
        
        return {
            "products": product_list,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "search_type": "all_products"
        }
        
    except Exception as e:
        logger.error(f"Error getting all products: {e}")
        return {
            "products": [],
            "total": 0,
            "page": page,
            "per_page": per_page,
            "total_pages": 0,
            "error": str(e)
        }

@app.get("/test-search")
async def test_search(db: AsyncSession = Depends(get_db)):
    """Test endpoint to check if search is working"""
    try:
        # Check if we have any products
        count_result = await db.execute(select(func.count()).select_from(Product))
        total_products = count_result.scalar()
        
        # Get a few sample products
        sample_result = await db.execute(select(Product).limit(5))
        sample_products = sample_result.scalars().all()
        
        # Check if we have any brands
        brand_result = await db.execute(select(func.count()).select_from(Brand))
        total_brands = brand_result.scalar()
        
        # Check if we have any categories
        category_result = await db.execute(select(func.count()).select_from(Category))
        total_categories = category_result.scalar()
        
        return {
            "status": "success",
            "total_products": total_products,
            "total_brands": total_brands,
            "total_categories": total_categories,
            "sample_products": [
                {
                    "id": p.id,
                    "title": p.title,
                    "price": p.price,
                    "shop_id": p.shop_id
                } for p in sample_products
            ]
        }
    except Exception as e:
        logger.error(f"Test search error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

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
    """Unified search endpoint with enhanced error handling"""
    try:
        # Validate and sanitize inputs
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
            
        # Build search filters
        filters = SearchFilters(
            title=title or q,  # Use q as title if no specific title filter
            brand=brand,
            brands=brands,
            category=category,
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

        search_service = SearchService(db)
        
        # Log search request for debugging
        logger.info(f"Search request: query='{q}', filters={filters.dict()}, page={page}, per_page={per_page}")
        
        # Perform search with AI-enhanced processing
        try:
            if type == "categories":
                results = await search_service.search_categories(q or "", limit=per_page)
                return {
                    "categories": results,
                    "total": len(results),
                    "page": page,
                    "per_page": per_page,
                    "search_type": "categories"
                }
            else:
                # Use AI-enhanced aggregated search as primary method
                try:
                    results = await search_service.search_products_aggregated(
                        filters, page, per_page, sort
                    )
                    logger.info("AI-enhanced search successful")
                    return results
                except Exception as ai_error:
                    logger.warning(f"AI-enhanced search failed: {ai_error}")
                    # Fallback to basic search
                    try:
                        results = await search_service.search_products(filters, page, per_page)
                        logger.info("Basic search successful")
                        return results
                    except Exception as basic_error:
                        logger.error(f"All search methods failed: {basic_error}")
                        # Return empty results
                        return {
                            "products": [],
                            "total": 0,
                            "page": page,
                            "per_page": per_page,
                            "total_pages": 0,
                            "execution_time_ms": 0,
                            "search_type": "fallback",
                            "error": "No results found"
                        }
                
        except Exception as search_error:
            logger.error(f"All search methods failed: {search_error}")
            # Return empty results instead of error
            return {
                "products": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
                "execution_time_ms": 0,
                "search_type": "fallback",
                "error": "No results found"
            }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in search endpoint: {e}")
        raise HTTPException(
            status_code=500, 
            detail="An unexpected error occurred. Please try again later."
        )

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

@app.get("/product/{product_id}/comparison")
async def get_product_comparison(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get product comparison data - all individual products that make up an aggregated product"""
    try:
        search_service = SearchService(db)
        comparison_data = await search_service.get_product_comparison(product_id)
        
        if not comparison_data:
            raise HTTPException(status_code=404, detail="Product comparison not found")
        
        return comparison_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product comparison {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Product comparison retrieval error")

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
    fuzzy: bool = Query(True, description="Enable fuzzy search"),
    db: AsyncSession = Depends(get_db)
):
    """Get AI-enhanced search suggestions with fuzzy search support"""
    try:
        search_service = SearchService(db)
        
        # Always use AI-enhanced suggestions first
        suggestions = await search_service.get_search_suggestions(q, limit)
        
        # If no AI suggestions, try fuzzy search
        if not suggestions:
            suggestions = await search_service.fuzzy_search_suggestions(q, limit)
        
        # If still no suggestions, try basic search
        if not suggestions:
            suggestions = await search_service._get_database_suggestions(q, limit)
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        # Return empty list instead of error to prevent frontend issues
        return []

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
        result = await db.execute(select(Shop).where(Shop.id == shop_id))
        shop = result.scalar_one_or_none()
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
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
    from datetime import datetime
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "message": "Application is running"
    }

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