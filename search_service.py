import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import selectinload
from models import Product, Shop, Brand, Category, ProductVariant
from schemas import SearchFilters, SearchResponse, Product as ProductSchema
import logging
import time

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # async def search_products_aggregated(
    #     self,
    #     filters: SearchFilters,
    #     page: int = 1,
    #     per_page: int = 50,
    #     sort: str = 'relevance'
    # ) -> SearchResponse:
    #     """Search products with multi-shop aggregation and enhanced availability info"""
    #     start_time = time.time()

    #     try:
    #         # Build query to group products by EAN/title similarity
    #         query = text("""
    #             WITH product_groups AS (
    #                 SELECT 
    #                     COALESCE(p.ean, '') as group_key,
    #                     p.title,
    #                     p.description,
    #                     p.image_url,
    #                     p.brand_id,
    #                     p.category_id,
    #                     MIN(p.price) as min_price,
    #                     MAX(p.price) as max_price,
    #                     AVG(p.price) as avg_price,
    #                     COUNT(DISTINCT p.shop_id) as shop_count,
    #                     BOOL_OR(p.availability) as any_available,
    #                     COUNT(CASE WHEN p.availability = true THEN 1 END) as available_shops,
    #                     MIN(CASE WHEN p.availability = true THEN p.price END) as best_available_price,
    #                     ARRAY_AGG(DISTINCT s.name) as shop_names,
    #                     ARRAY_AGG(DISTINCT p.id) as product_ids,
    #                     MAX(p.updated_at) as last_updated
    #                 FROM products p
    #                 JOIN shops s ON p.shop_id = s.id
    #                 LEFT JOIN brands b ON p.brand_id = b.id
    #                 LEFT JOIN categories c ON p.category_id = c.id
    #                 WHERE 1=1
    #                 GROUP BY COALESCE(p.ean, ''), p.title, p.description, p.image_url, p.brand_id, p.category_id
    #                 HAVING COUNT(*) > 0
    #             )
    #             SELECT * FROM product_groups
    #             ORDER BY 
    #                 CASE WHEN :sort = 'price_asc' THEN min_price END ASC,
    #                 CASE WHEN :sort = 'price_desc' THEN min_price END DESC,
    #                 CASE WHEN :sort = 'availability' THEN any_available END DESC,
    #                 CASE WHEN :sort = 'newest' THEN last_updated END DESC,
    #                 any_available DESC, min_price ASC
    #             LIMIT :limit OFFSET :offset
    #         """)

    #         offset = (page - 1) * per_page
    #         result = await self.db.execute(query, {"limit": per_page, "offset": offset, "sort": sort})
    #         product_groups = result.fetchall()

    #         # Convert to response format
    #         aggregated_products = []
    #         for group in product_groups:
    #             # Get brand and category info
    #             brand_info = None
    #             if group.brand_id:
    #                 brand_query = select(Brand).where(Brand.id == group.brand_id)
    #                 brand_result = await self.db.execute(brand_query)
    #                 brand_info = brand_result.scalar_one_or_none()

    #             category_info = None
    #             if group.category_id:
    #                 cat_query = select(Category).where(Category.id == group.category_id)
    #                 cat_result = await self.db.execute(cat_query)
    #                 category_info = cat_result.scalar_one_or_none()

    #             product_data = {
    #                 "id": group.product_ids[0] if group.product_ids else 0,
    #                 "title": group.title,
    #                 "description": group.description,
    #                 "image_url": group.image_url,
    #                 "min_price": float(group.min_price) if group.min_price else None,
    #                 "max_price": float(group.max_price) if group.max_price else None,
    #                 "avg_price": float(group.avg_price) if group.avg_price else None,
    #                 "best_available_price": float(group.best_available_price) if group.best_available_price else None,
    #                 "shop_count": group.shop_count,
    #                 "available_shops": group.available_shops,
    #                 "shop_names": list(group.shop_names),
    #                 "availability": group.any_available,
    #                 "availability_info": {
    #                     "available_in_shops": group.available_shops,
    #                     "total_shops": group.shop_count,
    #                     "estimated_delivery": "1-3 days" if group.any_available else "3-7 days"
    #                 },
    #                 "brand": {"name": brand_info.name} if brand_info else None,
    #                 "category": {"name": category_info.name} if category_info else None,
    #                 "last_updated": group.last_updated,
    #                 "product_ids": list(group.product_ids)
    #             }
    #             aggregated_products.append(product_data)

    #         # Get total count
    #         count_query = text("""
    #             SELECT COUNT(DISTINCT COALESCE(p.ean, p.title))
    #             FROM products p
    #             WHERE 1=1
    #         """)
    #         total_result = await self.db.execute(count_query)
    #         total = total_result.scalar() or 0

    #         execution_time = (time.time() - start_time) * 1000
    #         total_pages = (total + per_page - 1) // per_page

    #         return {
    #             "products": aggregated_products,
    #             "total": total,
    #             "page": page,
    #             "per_page": per_page,
    #             "total_pages": total_pages,
    #             "execution_time_ms": round(execution_time, 2),
    #             "search_type": "aggregated"
    #         }

    #     except Exception as e:
    #         logger.error(f"Aggregated search error: {e}")
    #         execution_time = (time.time() - start_time) * 1000
    #         return {
    #             "products": [],
    #             "total": 0,
    #             "page": page,
    #             "per_page": per_page,
    #             "total_pages": 0,
    #             "execution_time_ms": round(execution_time, 2),
    #             "search_type": "aggregated"
    #         }

    async def search_products_aggregated(
        self,
        filters: SearchFilters,
        page: int = 1,
        per_page: int = 50,
        sort: str = 'relevance'
    ) -> SearchResponse:
        """Search products with multi-shop aggregation and enhanced availability info"""
        start_time = time.time()

        try:
            conditions = ["1=1"]
            params = {
                "limit": per_page,
                "offset": (page - 1) * per_page,
                "sort": sort
            }

            if filters.title:
                conditions.append("LOWER(p.title) ILIKE :title")
                params["title"] = f"%{filters.title.lower()}%"

            if filters.brand:
                conditions.append("LOWER(b.name) = :brand")
                params["brand"] = filters.brand.lower()

            if filters.brands:
                conditions.append("b.name = ANY(:brands)")
                params["brands"] = filters.brands

            if filters.category:
                conditions.append("LOWER(c.name) = :category")
                params["category"] = filters.category.lower()

            if filters.categories:
                conditions.append("c.name = ANY(:categories)")
                params["categories"] = filters.categories

            if filters.min_price is not None:
                conditions.append("p.price >= :min_price")
                params["min_price"] = filters.min_price

            if filters.max_price is not None:
                conditions.append("p.price <= :max_price")
                params["max_price"] = filters.max_price

            if filters.ean:
                conditions.append("p.ean = :ean")
                params["ean"] = filters.ean

            if filters.mpn:
                conditions.append("p.mpn = :mpn")
                params["mpn"] = filters.mpn

            if filters.availability is not None:
                conditions.append("p.availability = :availability")
                params["availability"] = filters.availability

            # Shop filter (multi-select by name)
            if filters.shops:
                conditions.append("s.name = ANY(:shops)")
                params["shops"] = filters.shops

            # Main query with filters injected
            query = text(f"""
                WITH product_groups AS (
                    SELECT 
                        COALESCE(p.ean, '') as group_key,
                        p.title,
                        p.description,
                        p.image_url,
                        p.brand_id,
                        p.category_id,
                        MIN(p.price) as min_price,
                        MAX(p.price) as max_price,
                        AVG(p.price) as avg_price,
                        COUNT(DISTINCT p.shop_id) as shop_count,
                        BOOL_OR(p.availability) as any_available,
                        COUNT(CASE WHEN p.availability = true THEN 1 END) as available_shops,
                        MIN(CASE WHEN p.availability = true THEN p.price END) as best_available_price,
                        ARRAY_AGG(DISTINCT s.name) as shop_names,
                        ARRAY_AGG(DISTINCT p.id) as product_ids,
                        MAX(p.updated_at) as last_updated
                    FROM products p
                    JOIN shops s ON p.shop_id = s.id
                    LEFT JOIN brands b ON p.brand_id = b.id
                    LEFT JOIN categories c ON p.category_id = c.id
                    WHERE {" AND ".join(conditions)}
                    GROUP BY COALESCE(p.ean, ''), p.title, p.description, p.image_url, p.brand_id, p.category_id
                    HAVING COUNT(*) > 0
                )
                SELECT * FROM product_groups
                ORDER BY 
                    CASE WHEN :sort = 'price_asc' THEN min_price END ASC,
                    CASE WHEN :sort = 'price_desc' THEN min_price END DESC,
                    CASE WHEN :sort = 'availability' THEN any_available END DESC,
                    CASE WHEN :sort = 'newest' THEN last_updated END DESC,
                    any_available DESC, min_price ASC
                LIMIT :limit OFFSET :offset
            """)

            result = await self.db.execute(query, params)
            product_groups = result.fetchall()

            aggregated_products = []
            for group in product_groups:
                # Get brand info
                brand_info = None
                if group.brand_id:
                    brand_result = await self.db.execute(select(Brand).where(Brand.id == group.brand_id))
                    brand_info = brand_result.scalar_one_or_none()

                # Get category info
                category_info = None
                if group.category_id:
                    category_result = await self.db.execute(select(Category).where(Category.id == group.category_id))
                    category_info = category_result.scalar_one_or_none()

                aggregated_products.append({
                    "id": group.product_ids[0] if group.product_ids else 0,
                    "title": group.title,
                    "description": group.description,
                    "image_url": group.image_url,
                    "min_price": float(group.min_price) if group.min_price else None,
                    "max_price": float(group.max_price) if group.max_price else None,
                    "avg_price": float(group.avg_price) if group.avg_price else None,
                    "best_available_price": float(group.best_available_price) if group.best_available_price else None,
                    "shop_count": group.shop_count,
                    "available_shops": group.available_shops,
                    "shop_names": list(group.shop_names),
                    "availability": group.any_available,
                    "availability_info": {
                        "available_in_shops": group.available_shops,
                        "total_shops": group.shop_count,
                        "estimated_delivery": "1-3 days" if group.any_available else "3-7 days"
                    },
                    "brand": {"name": brand_info.name} if brand_info else None,
                    "category": {"name": category_info.name} if category_info else None,
                    "last_updated": group.last_updated,
                    "product_ids": list(group.product_ids)
                })

            # Total count
            if filters.shops:
                count_query = text(f"""
                    SELECT COUNT(DISTINCT COALESCE(p.ean, p.title))
                    FROM products p
                    JOIN shops s ON p.shop_id = s.id
                    LEFT JOIN brands b ON p.brand_id = b.id
                    LEFT JOIN categories c ON p.category_id = c.id
                    WHERE {" AND ".join(conditions)}
                """)
            else:
                count_query = text(f"""
                    SELECT COUNT(DISTINCT COALESCE(p.ean, p.title))
                    FROM products p
                    LEFT JOIN brands b ON p.brand_id = b.id
                    LEFT JOIN categories c ON p.category_id = c.id
                    WHERE {" AND ".join(conditions)}
                """)

            count_result = await self.db.execute(count_query, params)
            total = count_result.scalar() or 0

            execution_time = (time.time() - start_time) * 1000
            total_pages = (total + per_page - 1) // per_page

            return {
                "products": aggregated_products,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "execution_time_ms": round(execution_time, 2),
                "search_type": "aggregated"
            }

        except Exception as e:
            logger.error(f"Aggregated search error: {e}")
            execution_time = (time.time() - start_time) * 1000
            return {
                "products": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
                "execution_time_ms": round(execution_time, 2),
                "search_type": "aggregated"
            }

    async def search_products(
        self,
        filters: SearchFilters,
        page: int = 1,
        per_page: int = 50
    ) -> SearchResponse:
        """Search products with enhanced multi-term support"""
        try:
            # Process complex queries
            query_terms = self.process_search_query(filters.title or filters.q or "")
            logger.info(f"Search query: '{filters.title or filters.q}', processed terms: {query_terms}")
            
            # Build base query
            query = select(Product).options(selectinload(Product.shop))
            
            # Apply search conditions for multiple terms
            if query_terms:
                search_conditions = []
                for term in query_terms:
                    # Use ILIKE for case-insensitive search
                    term_condition = or_(
                        Product.title.ilike(f"%{term}%"),
                        Product.description.ilike(f"%{term}%"),
                        Product.ean.ilike(f"%{term}%"),
                        Product.mpn.ilike(f"%{term}%")
                    )
                    search_conditions.append(term_condition)
                
                # Combine all search conditions with OR
                query = query.where(or_(*search_conditions))
                logger.info(f"Applied search conditions for terms: {query_terms}")
            
            # Apply filters
            if filters.brand:
                query = query.join(Brand).where(Brand.name.ilike(f"%{filters.brand}%"))
                logger.info(f"Applied brand filter: {filters.brand}")
            
            if filters.category:
                query = query.join(Category).where(Category.name.ilike(f"%{filters.category}%"))
                logger.info(f"Applied category filter: {filters.category}")
            
            if filters.min_price is not None:
                query = query.where(Product.price >= filters.min_price)
                logger.info(f"Applied min price filter: {filters.min_price}")
            
            if filters.max_price is not None:
                query = query.where(Product.price <= filters.max_price)
                logger.info(f"Applied max price filter: {filters.max_price}")
            
            if filters.availability is not None:
                query = query.where(Product.availability == filters.availability)
                logger.info(f"Applied availability filter: {filters.availability}")
            
            if filters.ean:
                query = query.where(Product.ean.ilike(f"%{filters.ean}%"))
                logger.info(f"Applied EAN filter: {filters.ean}")
            
            if filters.mpn:
                query = query.where(Product.mpn.ilike(f"%{filters.mpn}%"))
                logger.info(f"Applied MPN filter: {filters.mpn}")
            
            if filters.shops:
                query = query.join(Shop).where(Shop.name.in_(filters.shops))
                logger.info(f"Applied shops filter: {filters.shops}")
            
            # Apply sorting
            if filters.sort == 'price_asc':
                query = query.order_by(Product.price.asc())
            elif filters.sort == 'price_desc':
                query = query.order_by(Product.price.desc())
            elif filters.sort == 'availability':
                query = query.order_by(Product.availability.desc(), Product.price.asc())
            elif filters.sort == 'newest':
                query = query.order_by(Product.updated_at.desc())
            else:  # relevance - order by availability and price
                query = query.order_by(Product.availability.desc(), Product.price.asc())
            
            # Apply pagination
            offset = (page - 1) * per_page
            query = query.offset(offset).limit(per_page)
            
            # Execute query
            result = await self.db.execute(query)
            products = result.scalars().all()
            logger.info(f"Found {len(products)} products for query")
            
            # Convert to response format
            product_schemas = []
            for product in products:
                # Get brand and category info
                brand_info = None
                if product.brand_id:
                    brand_query = select(Brand).where(Brand.id == product.brand_id)
                    brand_result = await self.db.execute(brand_query)
                    brand_info = brand_result.scalar_one_or_none()
                
                category_info = None
                if product.category_id:
                    cat_query = select(Category).where(Category.id == product.category_id)
                    cat_result = await self.db.execute(cat_query)
                    category_info = cat_result.scalar_one_or_none()
                
                # Create basic product schema without complex objects
                product_schemas.append(ProductSchema(
                    id=product.id,
                    title=product.title,
                    description=product.description,
                    price=product.price,
                    image_url=product.image_url,
                    availability=product.availability,
                    ean=product.ean,
                    mpn=product.mpn,
                    brand=None,  # Skip complex objects for now
                    category=None,  # Skip complex objects for now
                    shop=None,  # Skip complex objects for now
                    shop_id=product.shop_id,
                    brand_id=product.brand_id,
                    category_id=product.category_id,
                    variants=[],  # Empty list for now
                    created_at=product.created_at,
                    updated_at=product.updated_at
                ))
            
            # Get total count for pagination
            count_query = select(func.count(Product.id))
            if query_terms:
                search_conditions = []
                for term in query_terms:
                    term_condition = or_(
                        Product.title.ilike(f"%{term}%"),
                        Product.description.ilike(f"%{term}%"),
                        Product.ean.ilike(f"%{term}%"),
                        Product.mpn.ilike(f"%{term}%")
                    )
                    search_conditions.append(term_condition)
                count_query = count_query.where(or_(*search_conditions))
            
            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar()
            logger.info(f"Total count for query: {total_count}")
            
            return SearchResponse(
                products=product_schemas,
                total=total_count,
                page=page,
                per_page=per_page,
                total_pages=(total_count + per_page - 1) // per_page,
                filters_applied={},
                execution_time_ms=0.0
            )
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            raise

    def process_search_query(self, query: str) -> List[str]:
        """Process search query to extract individual terms"""
        if not query:
            return []
        
        # Handle OR separated queries
        if ' OR ' in query:
            terms = [term.strip() for term in query.split(' OR ') if term.strip()]
            return terms
        
        # Split query into words and filter out short words
        words = query.lower().split()
        terms = [word.strip() for word in words if len(word.strip()) >= 2]
        
        # Add the original query as a term for exact matches
        if query.strip():
            terms.insert(0, query.strip())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)
        
        return unique_terms

    async def get_product_by_id(self, product_id: int) -> Optional[ProductSchema]:
        """Get product by ID"""
        try:
            query = select(Product).options(
                selectinload(Product.shop),
                selectinload(Product.brand),
                selectinload(Product.category),
                selectinload(Product.variants)
            ).where(Product.id == product_id)

            result = await self.db.execute(query)
            product = result.scalar_one_or_none()

            if product:
                return ProductSchema.from_orm(product)
            return None

        except Exception as e:
            logger.error(f"Error getting product by ID {product_id}: {e}")
            return None

    async def get_product_by_ean(self, ean: str) -> Optional[ProductSchema]:
        """Get product by EAN code"""
        try:
            query = select(Product).options(
                selectinload(Product.shop),
                selectinload(Product.brand),
                selectinload(Product.category),
                selectinload(Product.variants)
            ).where(Product.ean == ean)

            result = await self.db.execute(query)
            product = result.scalar_one_or_none()

            if product:
                return ProductSchema.from_orm(product)
            return None

        except Exception as e:
            logger.error(f"Error getting product by EAN {ean}: {e}")
            return None

    async def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get search suggestions based on query"""
        try:
            # Search in product titles and brands
            suggestions = []

            # Title suggestions
            # title_query = select(Product.title).where(
            #     func.lower(Product.title).contains(query.lower())
            # ).limit(limit // 2)

            # title_result = await self.db.execute(title_query)
            # titles = [row[0] for row in title_result]
            # suggestions.extend(titles)

            # Category suggestions
            category_query = select(Category.name).where(
                func.lower(Category.name).contains(query.lower())
            ).limit(limit // 2)

            category_result = await self.db.execute(category_query)
            categories = [row[0] for row in category_result]
            suggestions.extend(categories)

            # Remove duplicates and limit
            unique_suggestions = list(set(suggestions))[:limit]
            return unique_suggestions

        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return []

    async def get_facets(self, filters: SearchFilters) -> Dict[str, List[Dict[str, Any]]]:
        """Get facets for search results"""
        try:
            facets = {}

            # Brand facets
            brand_query = select(
                Brand.name,
                func.count(Product.id).label('count')
            ).join(Product).group_by(Brand.name).order_by(func.count(Product.id).desc())

            brand_result = await self.db.execute(brand_query)
            facets['brands'] = [
                {'name': row[0], 'count': row[1]} 
                for row in brand_result
            ]

            # Category facets
            category_query = select(
                Category.name,
                func.count(Product.id).label('count')
            ).join(Product).group_by(Category.name).order_by(func.count(Product.id).desc())

            category_result = await self.db.execute(category_query)
            facets['categories'] = [
                {'name': row[0], 'count': row[1]} 
                for row in category_result
            ]

            # Shop facets
            shop_query = select(
                Shop.name,
                func.count(Product.id).label('count')
            ).join(Product).group_by(Shop.name).order_by(func.count(Product.id).desc())

            shop_result = await self.db.execute(shop_query)
            facets['shops'] = [
                {'name': row[0], 'count': row[1]}
                for row in shop_result
            ]

            # Price ranges
            price_query = select(
                func.min(Product.price).label('min_price'),
                func.max(Product.price).label('max_price'),
                func.avg(Product.price).label('avg_price')
            ).where(Product.price.is_not(None))

            price_result = await self.db.execute(price_query)
            price_stats = price_result.first()

            if price_stats and price_stats[0] is not None:
                facets['price_ranges'] = [
                    {'range': f"0-{price_stats[2]:.0f}", 'label': f"Under €{price_stats[2]:.0f}"},
                    {'range': f"{price_stats[2]:.0f}-{price_stats[1]:.0f}", 'label': f"€{price_stats[2]:.0f} - €{price_stats[1]:.0f}"},
                    {'range': f"{price_stats[1]:.0f}+", 'label': f"Over €{price_stats[1]:.0f}"}
                ]

            return facets

        except Exception as e:
            logger.error(f"Error getting facets: {e}")
            return {}

    async def search_categories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Enhanced category search with product aggregation"""
        try:
            if not query:
                return []

            # Search categories with product count
            category_query = select(
                Category.name,
                func.count(Product.id).label('total_products')
            ).join(Product, isouter=True).where(
                Category.name.ilike(f"%{query}%")
            ).group_by(Category.name).order_by(
                func.count(Product.id).desc()
            ).limit(limit)

            result = await self.db.execute(category_query)
            categories = []
            
            for row in result:
                categories.append({
                    'name': row[0],
                    'total_products': row[1] or 0
                })

            return categories

        except Exception as e:
            logger.error(f"Error searching categories: {e}")
            return []
