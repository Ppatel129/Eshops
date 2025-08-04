import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database import AsyncSessionLocal
from models import Shop, Product, Brand, Category, ProductVariant
from xml_parser import XMLFeedParser
from schemas import FeedProcessResult
from config import settings
import time

logger = logging.getLogger(__name__)

class FeedProcessor:
    def __init__(self):
        self.parser = None
    
    async def process_all_feeds(self) -> List[FeedProcessResult]:
        """Process all shops from the database"""
        results = []
        async with XMLFeedParser() as parser:
            self.parser = parser
            # Fetch all shops from the database
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                result = await db.execute(select(Shop))
                shops = result.scalars().all()
            for shop in shops:
                try:
                    result = await self.process_feed(str(shop.name), str(shop.xml_url))
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing feed {shop.name}: {e}")
                    results.append(FeedProcessResult(
                        shop_name=str(shop.name),
                        status="error",
                        products_processed=0,
                        products_created=0,
                        products_updated=0,
                        errors=[str(e)],
                        processing_time_seconds=0,
                        timestamp=datetime.utcnow()
                    ))
        return results
    
    async def process_feed(self, shop_name: str, xml_url: str) -> FeedProcessResult:
        """Process a single XML feed"""
        start_time = time.time()
        errors = []
        products_processed = 0
        products_created = 0
        products_updated = 0
        
        try:
            # Get or create shop
            async with AsyncSessionLocal() as db:
                shop = await self.get_or_create_shop(db, shop_name, xml_url)
                
                # Update shop status
                await db.execute(
                    update(Shop)
                    .where(Shop.id == shop.id)
                    .values(sync_status="processing", last_sync=datetime.utcnow())
                )
                await db.commit()
                
                # Parse XML feed
                logger.info(f"Processing feed for {shop_name}...")
                product_data_list = await self.parser.parse_feed(xml_url)
                
                if not product_data_list:
                    errors.append("No products found in XML feed")
                    await self.update_shop_status(db, shop.id, "error", "No products found")
                    return FeedProcessResult(
                        shop_name=shop_name,
                        status="error",
                        products_processed=0,
                        products_created=0,
                        products_updated=0,
                        errors=errors,
                        processing_time_seconds=time.time() - start_time,
                        timestamp=datetime.utcnow()
                    )
                
                logger.info(f"Found {len(product_data_list)} products, processing in batches...")
                
                # Process products in batches
                batch_size = 100
                total_batches = (len(product_data_list) + batch_size - 1) // batch_size
                
                for batch_num in range(0, len(product_data_list), batch_size):
                    batch = product_data_list[batch_num:batch_num + batch_size]
                    current_batch = (batch_num // batch_size) + 1
                    
                    logger.info(f"Processing batch {current_batch}/{total_batches} ({len(batch)} products)")
                    
                    for product_data in batch:
                        try:
                            created, updated = await self.process_product(db, shop, product_data)
                            products_processed += 1
                            if created:
                                products_created += 1
                            if updated:
                                products_updated += 1
                        except Exception as e:
                            errors.append(f"Error processing product {product_data.get('title', 'unknown')}: {e}")
                            logger.warning(f"Error processing product: {e}")
                    
                    # Commit batch
                    await db.commit()
                    
                    # Log progress
                    if current_batch % 10 == 0:
                        logger.info(f"Processed {batch_num + len(batch)} / {len(product_data_list)} products for {shop_name}")
                
                # Update shop status
                await self.update_shop_status(db, shop.id, "completed", None, products_processed)
                
                processing_time = time.time() - start_time
                logger.info(f"Completed processing {shop_name}: {products_processed} products in {processing_time:.2f}s")
                
                return FeedProcessResult(
                    shop_name=shop_name,
                    status="completed",
                    products_processed=products_processed,
                    products_created=products_created,
                    products_updated=products_updated,
                    errors=errors,
                    processing_time_seconds=processing_time,
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Error processing feed {shop_name}: {e}")
            errors.append(str(e))
            
            # Update shop status
            try:
                async with AsyncSessionLocal() as db:
                    await self.update_shop_status(db, shop.id if 'shop' in locals() else None, "error", str(e))
            except:
                pass
            
            return FeedProcessResult(
                shop_name=shop_name,
                status="error",
                products_processed=products_processed,
                products_created=products_created,
                products_updated=products_updated,
                errors=errors,
                processing_time_seconds=time.time() - start_time,
                timestamp=datetime.utcnow()
            )
    
    async def get_or_create_shop(self, db: AsyncSession, shop_name: str, xml_url: str) -> Shop:
        """Get existing shop or create new one"""
        query = select(Shop).where(Shop.name == shop_name)
        result = await db.execute(query)
        shop = result.scalar_one_or_none()
        
        if not shop:
            shop = Shop(name=shop_name, xml_url=xml_url)
            db.add(shop)
            await db.commit()
            await db.refresh(shop)
            logger.info(f"Created new shop: {shop_name}")
        
        return shop
    
    async def process_product(self, db: AsyncSession, shop: Shop, product_data: Dict[str, Any]) -> tuple[bool, bool]:
        """Process a single product, return (created, updated) flags"""
        created = False
        updated = False
        
        try:
            # Look for existing product by EAN or title+shop
            existing_product = None
            
            if product_data.get('ean'):
                query = select(Product).where(
                    Product.ean == product_data['ean'],
                    Product.shop_id == shop.id
                )
                result = await db.execute(query)
                existing_product = result.scalar_one_or_none()
            
            if not existing_product:
                # Try to find by title and shop
                query = select(Product).where(
                    Product.title == product_data['title'],
                    Product.shop_id == shop.id
                )
                result = await db.execute(query)
                existing_product = result.scalar_one_or_none()
            
            # Get or create brand
            brand = None
            if product_data.get('brand'):
                brand = await self.get_or_create_brand(db, product_data['brand'])
            
            # Get or create category
            category = None
            if product_data.get('category'):
                category = await self.get_or_create_category(db, product_data['category'], product_data.get('category_path', []))
            
            # Create or update product
            if existing_product:
                # Update existing product
                for key, value in product_data.items():
                    if key not in ['brand', 'category', 'category_path'] and hasattr(existing_product, key):
                        setattr(existing_product, key, value)
                
                existing_product.brand_id = brand.id if brand else None
                existing_product.category_id = category.id if category else None
                existing_product.updated_at = datetime.utcnow()
                updated = True
                
                product = existing_product
            else:
                # Create new product
                product_dict = {k: v for k, v in product_data.items() if k not in ['brand', 'category', 'category_path']}
                product = Product(
                    shop_id=shop.id,
                    brand_id=brand.id if brand else None,
                    category_id=category.id if category else None,
                    **product_dict
                )
                db.add(product)
                await db.flush()  # Get product ID
                created = True
            
            # Process variants if any
            if any(key in product_data for key in ['color', 'size', 'material']):
                await self.process_product_variants(db, product, product_data)
            
            return created, updated
            
        except Exception as e:
            logger.error(f"Error processing product {product_data.get('title', 'unknown')}: {e}")
            raise
    
    async def get_or_create_brand(self, db: AsyncSession, brand_name: str) -> Brand:
        """Get existing brand or create new one"""
        normalized_name = brand_name.lower().strip()
        
        query = select(Brand).where(Brand.normalized_name == normalized_name)
        result = await db.execute(query)
        brand = result.scalar_one_or_none()
        
        if not brand:
            brand = Brand(name=brand_name, normalized_name=normalized_name)
            db.add(brand)
            await db.flush()
        
        return brand
    
    async def get_or_create_category(self, db: AsyncSession, category_name: str, category_path: List[str]) -> Category:
        """Get existing category or create new one"""
        normalized_name = category_name.lower().strip()
        path = " > ".join(category_path) if category_path else category_name
        
        # First try to find by normalized_name and path to be more specific
        query = select(Category).where(
            Category.normalized_name == normalized_name,
            Category.path == path
        )
        result = await db.execute(query)
        category = result.scalar_one_or_none()
        
        if not category:
            category = Category(
                name=category_name,
                normalized_name=normalized_name,
                path=path,
                level=len(category_path) - 1 if category_path else 0
            )
            db.add(category)
            await db.flush()
        
        return category
    
    async def process_product_variants(self, db: AsyncSession, product: Product, product_data: Dict[str, Any]):
        """Process product variants"""
        # For now, create a single variant with the main product attributes
        variant_data = {}
        
        for key in ['color', 'size', 'material']:
            if key in product_data:
                variant_data[key] = product_data[key]
        
        if variant_data:
            # Check if variant already exists - get all variants for this product
            query = select(ProductVariant).where(ProductVariant.product_id == product.id)
            result = await db.execute(query)
            existing_variant = result.scalar_one_or_none()
            
            if existing_variant:
                # Update existing variant
                for key, value in variant_data.items():
                    setattr(existing_variant, key, value)
                existing_variant.updated_at = datetime.utcnow()
            else:
                # Create new variant
                variant = ProductVariant(
                    product_id=product.id,
                    ean=product_data.get('ean'),
                    price=product_data.get('price'),
                    availability=product_data.get('availability', False),
                    stock_quantity=product_data.get('stock_quantity'),
                    **variant_data
                )
                db.add(variant)
    
    async def update_shop_status(self, db: AsyncSession, shop_id: int, status: str, error_message: str = None, total_products: int = None):
        """Update shop sync status"""
        if not shop_id:
            return
        
        update_data = {
            'sync_status': status,
            'last_sync': datetime.utcnow()
        }
        
        if error_message:
            update_data['error_message'] = error_message
        
        if total_products is not None:
            update_data['total_products'] = total_products
        
        await db.execute(
            update(Shop).where(Shop.id == shop_id).values(**update_data)
        )
        await db.commit()

class FeedScheduler:
    def __init__(self):
        self.processor = FeedProcessor()
        self.running = False
    
    async def start(self):
        """Start the feed scheduler"""
        self.running = True
        logger.info("Feed scheduler started")
        
        while self.running:
            try:
                # Process all feeds
                results = await self.processor.process_all_feeds()
                
                # Log results
                for result in results:
                    logger.info(f"Feed processing result: {result.shop_name} - {result.status}")
                
                # Wait for next cycle
                await asyncio.sleep(settings.FEED_REFRESH_INTERVAL_HOURS * 3600)
                
            except Exception as e:
                logger.error(f"Error in feed scheduler: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    def stop(self):
        """Stop the feed scheduler"""
        self.running = False
        logger.info("Feed scheduler stopped")

# Global scheduler instance
scheduler = FeedScheduler()
