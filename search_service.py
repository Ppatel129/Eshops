import asyncio
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text

from models import Product, Shop, Brand, Category, ProductVariant
from schemas import SearchFilters, SearchResponse, Product as ProductSchema
import logging
import time
from fuzzywuzzy import fuzz, process
import re
from elasticsearch_service import elasticsearch_service
import openai
from config import settings

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            try:
                self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.warning(f"OpenAI client initialization failed: {e}")

    async def process_query_with_ai(self, query: str) -> Dict[str, Any]:
        """Process search query using AI to extract intent, correct misspellings, and identify components"""
        if not self.openai_client or not query.strip():
            return self._fallback_query_processing(query)
        
        try:
            # Create a structured prompt for query analysis
            prompt = f"""
            Analyze this e-commerce search query and extract structured information:
            Query: "{query}"
            
            Return a JSON object with:
            {{
                "corrected_query": "spelling corrected version",
                "original_query": "{query}",
                "intent": "product_search|category_search|brand_search|combined",
                "components": {{
                    "brands": ["list of brand names found"],
                    "categories": ["list of category names found"],
                    "product_terms": ["list of product-specific terms"],
                    "attributes": ["color", "size", "model", etc.]
                }},
                "confidence": 0.95,
                "suggestions": ["alternative search terms"]
            }}
            
            Examples:
            - "PanzerGlass Samsung" -> brands: ["PanzerGlass", "Samsung"], intent: "combined"
            - "iphone 13 pro" -> brands: ["Apple"], product_terms: ["iPhone", "13", "Pro"], intent: "product_search"
            - "smartphones" -> categories: ["Smartphones"], intent: "category_search"
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            result = response.choices[0].message.content.strip()
            # Extract JSON from response
            import json
            try:
                # Find JSON in the response
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    return parsed
                else:
                    return self._fallback_query_processing(query)
            except json.JSONDecodeError:
                return self._fallback_query_processing(query)
                
        except Exception as e:
            logger.warning(f"AI query processing failed: {e}")
            return self._fallback_query_processing(query)

    def _fallback_query_processing(self, query: str) -> Dict[str, Any]:
        """Fallback query processing without AI"""
        # Simple regex-based extraction
        query_lower = query.lower()
        
        # Common brand patterns
        brands = []
        brand_patterns = [
            r'\b(samsung|apple|iphone|ipad|macbook|sony|lg|panasonic|canon|nikon|nike|adidas|puma|reebok)\b',
            r'\b(panzerglass|otterbox|spigen|caseology|ringke|supcase)\b',
            r'\b(intel|amd|nvidia|asus|msi|gigabyte|evga|corsair|kingston|samsung|western digital)\b'
        ]
        
        for pattern in brand_patterns:
            matches = re.findall(pattern, query_lower)
            brands.extend(matches)
        
        # Category patterns
        categories = []
        category_patterns = [
            r'\b(smartphone|phone|mobile|tablet|laptop|computer|pc|desktop|tv|television|headphone|earphone|speaker)\b',
            r'\b(camera|gaming|console|accessory|case|cover|charger|cable|adapter)\b'
        ]
        
        for pattern in category_patterns:
            matches = re.findall(pattern, query_lower)
            categories.extend(matches)
        
        return {
            "corrected_query": query,
            "original_query": query,
            "intent": "combined" if brands and categories else "product_search",
            "components": {
                "brands": list(set(brands)),
                "categories": list(set(categories)),
                "product_terms": [term for term in query.split() if term.lower() not in brands + categories],
                "attributes": []
            },
            "confidence": 0.7,
            "suggestions": []
        }

    async def search_with_elasticsearch(self, query: str, filters: SearchFilters, page: int = 1, per_page: int = 50) -> Optional[Dict[str, Any]]:
        """Search using Elasticsearch if available"""
        try:
            if not elasticsearch_service.client:
                return None
                
            # Process query with AI
            query_analysis = await self.process_query_with_ai(query or filters.title or "")
            
            # Build Elasticsearch filters
            es_filters = {}
            if filters.brand:
                es_filters['brand'] = filters.brand
            if filters.category:
                es_filters['category'] = filters.category
            if filters.min_price is not None:
                es_filters['min_price'] = filters.min_price
            if filters.max_price is not None:
                es_filters['max_price'] = filters.max_price
            if filters.availability is not None:
                es_filters['availability'] = filters.availability
                
            # Search in Elasticsearch
            es_results = await elasticsearch_service.search_products(
                query=query_analysis['corrected_query'],
                filters=es_filters,
                page=page,
                per_page=per_page
            )
            
            if es_results and es_results.get('products'):
                # Enhance results with additional data from database
                enhanced_results = await self._enhance_elasticsearch_results(es_results)
                return enhanced_results
                
        except Exception as e:
            logger.warning(f"Elasticsearch search failed: {e}")
            
        return None

    async def _enhance_elasticsearch_results(self, es_results: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance Elasticsearch results with database data"""
        try:
            # Get product IDs from ES results
            product_ids = [product['id'] for product in es_results.get('products', [])]
            
            if not product_ids:
                return es_results
                
            # Get additional data from database
            query = select(Product).where(Product.id.in_(product_ids))
            result = await self.db.execute(query)
            db_products = result.scalars().all()
            
            # Create lookup for database products
            db_lookup = {p.id: p for p in db_products}
            
            # Enhance ES results with DB data
            enhanced_products = []
            for es_product in es_results.get('products', []):
                db_product = db_lookup.get(es_product['id'])
                if db_product:
                    enhanced_product = es_product.copy()
                    enhanced_product.update({
                        'shop_name': db_product.shop.name if db_product.shop else None,
                        'brand_name': db_product.brand.name if db_product.brand else None,
                        'category_name': db_product.category.name if db_product.category else None,
                        'last_updated': db_product.updated_at.isoformat() if db_product.updated_at else None
                    })
                    enhanced_products.append(enhanced_product)
                else:
                    enhanced_products.append(es_product)
                    
            es_results['products'] = enhanced_products
            return es_results
            
        except Exception as e:
            logger.error(f"Error enhancing Elasticsearch results: {e}")
            return es_results

    async def search_products_aggregated(
        self,
        filters: SearchFilters,
        page: int = 1,
        per_page: int = 50,
        sort: str = 'relevance'
    ) -> SearchResponse:
        """Search products with AI-powered query processing and multi-shop aggregation"""
        start_time = time.time()

        try:
            # First try Elasticsearch with AI processing
            es_results = await self.search_with_elasticsearch(
                query=filters.title or "",
                filters=filters,
                page=page,
                per_page=per_page
            )
            
            if es_results:
                logger.info("Using Elasticsearch results with AI processing")
                return es_results

            # Fallback to PostgreSQL with AI-enhanced query processing
            logger.info("Falling back to PostgreSQL search with AI processing")
            
            # Process query with AI for better understanding
            query_analysis = await self.process_query_with_ai(filters.title or "")
            
            # Build base conditions with AI-enhanced filtering
            conditions = ["1=1"]
            
            # Prepare search terms for relevance scoring
            search_terms = []
            if filters.title:
                search_terms = [term.strip().lower() for term in filters.title.split() if term.strip()]
            
            # Build relevance scoring parameters
            relevance_params = {
                "exact_phrase": f"%{filters.title.lower()}%" if filters.title else "%",
                "start_phrase": f"{filters.title.lower()}%" if filters.title else "%",
                "word1": f"%{search_terms[0]}%" if len(search_terms) > 0 else "%",
                "word2": f"%{search_terms[1]}%" if len(search_terms) > 1 else "%",
                "word3": f"%{search_terms[2]}%" if len(search_terms) > 2 else "%",
                "word4": f"%{search_terms[3]}%" if len(search_terms) > 3 else "%",
                "word5": f"%{search_terms[4]}%" if len(search_terms) > 4 else "%",
                "word_order_1": f"%{search_terms[0]}%{search_terms[1]}%" if len(search_terms) > 1 else "%",
                "word_order_2": f"%{search_terms[1]}%{search_terms[2]}%" if len(search_terms) > 2 else "%",
                "word_order_3": f"%{search_terms[2]}%{search_terms[3]}%" if len(search_terms) > 3 else "%",
                "start_word1": f"{search_terms[0]}%" if len(search_terms) > 0 else "%",
                "start_word2": f"{search_terms[1]}%" if len(search_terms) > 1 else "%",
                "start_word3": f"{search_terms[2]}%" if len(search_terms) > 2 else "%"
            }
            
            params = {
                "limit": per_page,
                "offset": (page - 1) * per_page,
                "sort": sort,
                **relevance_params
            }

            # Build search conditions based on AI analysis (make them optional)
            if query_analysis['components']['brands']:
                brand_conditions = []
                for brand in query_analysis['components']['brands']:
                    brand_conditions.append(f"LOWER(b.name) LIKE '%{brand.lower()}%'")
                if brand_conditions:
                    # Make brand conditions optional by using OR with title search
                    brand_or_title = f"({' OR '.join(brand_conditions)}) OR LOWER(p.title) LIKE '%{filters.title.lower()}%'"
                    conditions.append(f"({brand_or_title})")

            if query_analysis['components']['categories']:
                category_conditions = []
                for category in query_analysis['components']['categories']:
                    category_conditions.append(f"LOWER(c.name) LIKE '%{category.lower()}%'")
                if category_conditions:
                    # Make category conditions optional by using OR with title search
                    category_or_title = f"({' OR '.join(category_conditions)}) OR LOWER(p.title) LIKE '%{filters.title.lower()}%'"
                    conditions.append(f"({category_or_title})")

            # Add product terms to title search with fuzzy matching
            if query_analysis['components']['product_terms']:
                product_conditions = []
                for term in query_analysis['components']['product_terms']:
                    product_conditions.append(f"LOWER(p.title) LIKE '%{term.lower()}%'")
                    product_conditions.append(f"LOWER(p.search_text) LIKE '%{term.lower()}%'")
                if product_conditions:
                    conditions.append(f"({' OR '.join(product_conditions)})")

            # Always include original title search as a fallback
            if filters.title:
                conditions.append("LOWER(p.title) ILIKE :title OR p.title % :title_similar")
                params["title"] = f"%{filters.title.lower()}%"
                params["title_similar"] = filters.title

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
                # Filter out empty categories
                valid_categories = [cat for cat in filters.categories if cat and cat.strip()]
                if valid_categories:
                    conditions.append("c.name = ANY(:categories)")
                    params["categories"] = valid_categories

            # Optimize price filtering
            if filters.min_price is not None:
                conditions.append("p.price >= :min_price")
                params["min_price"] = filters.min_price

            if filters.max_price is not None:
                conditions.append("p.price <= :max_price")
                params["max_price"] = filters.max_price

            # Optimize exact match searches
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

            # Main query with improved product grouping and duplicate handling
            query = text(f"""
                WITH product_groups AS (
                    SELECT 
                        CASE 
                            WHEN p.ean IS NOT NULL AND p.ean != '' THEN p.ean
                            WHEN p.mpn IS NOT NULL AND p.mpn != '' THEN p.mpn
                            ELSE LOWER(REGEXP_REPLACE(p.title, '[^a-zA-Z0-9\s]', '', 'g'))
                        END as group_key,
                        -- Use the most common title for the group
                        MODE() WITHIN GROUP (ORDER BY p.title) as title,
                        -- Use the most common description for the group
                        MODE() WITHIN GROUP (ORDER BY p.description) as description,
                        -- Use the first image_url for the group
                        (ARRAY_AGG(p.image_url ORDER BY p.id))[1] as image_url,
                        p.brand_id,
                        p.category_id,
                        MIN(p.price) as min_price,
                        MAX(p.price) as max_price,
                        AVG(p.price) as avg_price,
                        COUNT(DISTINCT p.shop_id) as shop_count,
                        BOOL_OR(p.availability) as any_available,
                        COUNT(CASE WHEN p.availability = true THEN 1 END) as available_shops,
                        MIN(CASE WHEN p.availability = true THEN p.price END) as best_available_price,
                        ARRAY_AGG(DISTINCT s.name ORDER BY s.name) as shop_names,
                        ARRAY_AGG(DISTINCT p.id ORDER BY p.id) as product_ids,
                        ARRAY_AGG(DISTINCT p.price ORDER BY p.price) as all_prices,
                        MAX(p.updated_at) as last_updated,
                        STRING_AGG(DISTINCT s.name, ' vs ') as price_comparison,
                        -- Enhanced duplicate detection
                        COUNT(DISTINCT p.title) as title_variations,
                        COUNT(DISTINCT p.ean) FILTER (WHERE p.ean IS NOT NULL) as ean_count,
                        COUNT(DISTINCT p.mpn) FILTER (WHERE p.mpn IS NOT NULL) as mpn_count
                    FROM products p
                    JOIN shops s ON p.shop_id = s.id
                    LEFT JOIN brands b ON p.brand_id = b.id
                    LEFT JOIN categories c ON p.category_id = c.id
                    WHERE {" AND ".join(conditions)}
                    GROUP BY 
                        CASE 
                            WHEN p.ean IS NOT NULL AND p.ean != '' THEN p.ean
                            WHEN p.mpn IS NOT NULL AND p.mpn != '' THEN p.mpn
                            ELSE LOWER(REGEXP_REPLACE(p.title, '[^a-zA-Z0-9\s]', '', 'g'))
                        END,
                        p.brand_id, p.category_id
                    HAVING COUNT(*) > 0
                ),
                relevance_scored AS (
                    SELECT *,
                        -- Word match scoring
                        CASE 
                            WHEN LOWER(title) LIKE :exact_phrase THEN 100  -- Exact phrase match
                            WHEN LOWER(title) LIKE :start_phrase THEN 80   -- Starts with phrase
                            ELSE (
                                -- Count matching words
                                (CASE WHEN LOWER(title) LIKE :word1 THEN 1 ELSE 0 END +
                                 CASE WHEN LOWER(title) LIKE :word2 THEN 1 ELSE 0 END +
                                 CASE WHEN LOWER(title) LIKE :word3 THEN 1 ELSE 0 END +
                                 CASE WHEN LOWER(title) LIKE :word4 THEN 1 ELSE 0 END +
                                 CASE WHEN LOWER(title) LIKE :word5 THEN 1 ELSE 0 END) * 20
                            )
                        END as word_match_score,
                        -- Word order bonus (words appearing in sequence)
                        CASE 
                            WHEN LOWER(title) LIKE :word_order_1 THEN 30
                            WHEN LOWER(title) LIKE :word_order_2 THEN 20
                            WHEN LOWER(title) LIKE :word_order_3 THEN 10
                            ELSE 0
                        END as word_order_score,
                        -- Title position bonus (matches at beginning get higher score)
                        CASE 
                            WHEN LOWER(title) LIKE :start_word1 THEN 15
                            WHEN LOWER(title) LIKE :start_word2 THEN 10
                            WHEN LOWER(title) LIKE :start_word3 THEN 5
                            ELSE 0
                        END as position_score
                    FROM product_groups
                )
                SELECT * FROM relevance_scored
                ORDER BY 
                    CASE WHEN :sort = 'price_asc' THEN min_price END ASC,
                    CASE WHEN :sort = 'price_desc' THEN min_price END DESC,
                    CASE WHEN :sort = 'availability' THEN any_available END DESC,
                    CASE WHEN :sort = 'newest' THEN last_updated END DESC,
                    -- Enhanced relevance scoring with word matching
                    CASE WHEN :sort = 'relevance' THEN 
                        (word_match_score + word_order_score + position_score) 
                    END DESC,
                    (available_shops::float / NULLIF(shop_count, 0)) DESC,
                    min_price ASC,
                    shop_count DESC
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

                # Enhanced duplicate product handling
                duplicate_info = {
                    "is_duplicate": group.shop_count > 1,
                    "duplicate_type": "ean" if hasattr(group, 'ean_count') and group.ean_count > 1 else "title",
                    "title_variations": getattr(group, 'title_variations', 1),
                    "price_variations": len(getattr(group, 'all_prices', [])),
                    "grouped_products": group.shop_count,
                    "price_range": f"€{group.min_price:.2f} - €{group.max_price:.2f}" if group.min_price != group.max_price else f"€{group.min_price:.2f}",
                    "best_deal": group.best_available_price == group.min_price
                }

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
                    "price_comparison": group.price_comparison if hasattr(group, 'price_comparison') else None,
                    "all_prices": list(getattr(group, 'all_prices', [])),
                    "duplicate_info": duplicate_info,
                    "availability_info": {
                        "available_in_shops": group.available_shops,
                        "total_shops": group.shop_count,
                        "estimated_delivery": "1-3 days" if group.any_available else "3-7 days",
                        "price_savings": float(group.max_price - group.min_price) if group.max_price and group.min_price else 0
                    },
                    "brand": {"name": brand_info.name} if brand_info else None,
                    "category": {"name": category_info.name} if category_info else None,
                    "last_updated": group.last_updated,
                    "product_ids": list(group.product_ids),
                    "search_relevance": {
                        "ai_processed": True,
                        "confidence": query_analysis.get('confidence', 0.7),
                        "word_match_score": getattr(group, 'word_match_score', 0),
                        "word_order_score": getattr(group, 'word_order_score', 0),
                        "position_score": getattr(group, 'position_score', 0),
                        "total_relevance_score": getattr(group, 'word_match_score', 0) + getattr(group, 'word_order_score', 0) + getattr(group, 'position_score', 0)
                    }
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

            # Get category distribution for the current search results (optional and fast)
            category_distribution = []
            # Only get categories for meaningful searches (not empty or too short)
            if filters.title and len(filters.title.strip()) >= 2:
                try:
                    category_distribution = await self.get_category_distribution(filters, limit=10)
                except Exception as e:
                    logger.warning(f"Failed to get category distribution: {e}")
                    # Continue without category distribution

            return {
                "products": aggregated_products,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "execution_time_ms": round(execution_time, 2),
                "search_type": "aggregated",
                "category_distribution": category_distribution
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
            
            # Build base query with left joins
            query = select(Product).outerjoin(Product.shop).outerjoin(Product.brand).outerjoin(Product.category)
            
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
            
            # Apply filters with left joins
            if filters.brand:
                query = query.outerjoin(Brand).where(Brand.name.ilike(f"%{filters.brand}%"))
                logger.info(f"Applied brand filter: {filters.brand}")
            
            if filters.category:
                query = query.outerjoin(Category).where(Category.name.ilike(f"%{filters.category}%"))
                logger.info(f"Applied category filter: {filters.category}")
            
            if filters.categories:
                # Filter out empty categories
                valid_categories = [cat for cat in filters.categories if cat and cat.strip()]
                if valid_categories:
                    query = query.outerjoin(Category).where(Category.name.in_(valid_categories))
                    logger.info(f"Applied categories filter: {valid_categories}")
            
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
                query = query.outerjoin(Shop).where(Shop.name.in_(filters.shops))
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
            
            # Get category distribution for the current search results (optional and fast)
            category_distribution = []
            # Only get categories for meaningful searches (not empty or too short)
            if filters.title and len(filters.title.strip()) >= 2:
                try:
                    category_distribution = await self.get_category_distribution(filters, limit=10)
                except Exception as e:
                    logger.warning(f"Failed to get category distribution: {e}")
                    # Continue without category distribution
            
            return SearchResponse(
                products=product_schemas,
                total=total_count,
                page=page,
                per_page=per_page,
                total_pages=(total_count + per_page - 1) // per_page,
                filters_applied={},
                execution_time_ms=0.0,
                category_distribution=category_distribution
            )
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            raise

    def process_search_query(self, query: str) -> List[str]:
        """Process search query to extract individual terms with fuzzy search support"""
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
        
        # Add common misspellings and variations
        # This helps with fuzzy search
        variations = []
        for term in terms:
            if len(term) > 3:
                # Add common variations
                variations.extend([
                    term.replace('ph', 'f'),  # phone -> fone
                    term.replace('f', 'ph'),  # fone -> phone
                    term.replace('ck', 'k'),  # back -> bak
                    term.replace('k', 'ck'),  # bak -> back
                ])
        
        terms.extend(variations)
        
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
            query = select(Product).where(Product.id == product_id)

            result = await self.db.execute(query)
            product = result.scalar_one_or_none()

            if product:
                # Create a product dict without relationships to avoid schema issues
                product_dict = {
                    "id": product.id,
                    "title": product.title,
                    "description": product.description,
                    "ean": product.ean,
                    "mpn": product.mpn,
                    "sku": product.sku,
                    "price": product.price,
                    "original_price": product.original_price,
                    "discount_percentage": product.discount_percentage,
                    "availability": product.availability,
                    "stock_quantity": product.stock_quantity,
                    "image_url": product.image_url,
                    "additional_images": product.additional_images,
                    "product_url": product.product_url,
                    "deeplink": product.deeplink,
                    "specifications": product.specifications,
                    "features": product.features,
                    "tags": product.tags,
                    "shop_id": product.shop_id,
                    "brand_id": product.brand_id,
                    "category_id": product.category_id,
                    "created_at": product.created_at,
                    "updated_at": product.updated_at,
                    "shop": None,
                    "brand": None,
                    "category": None,
                    "variants": []
                }
                return ProductSchema(**product_dict)
            return None

        except Exception as e:
            logger.error(f"Error getting product by ID {product_id}: {e}")
            return None

    async def get_product_by_ean(self, ean: str) -> Optional[ProductSchema]:
        """Get product by EAN code"""
        try:
            query = select(Product).where(Product.ean == ean)

            result = await self.db.execute(query)
            product = result.scalar_one_or_none()

            if product:
                return ProductSchema.from_orm(product)
            return None

        except Exception as e:
            logger.error(f"Error getting product by EAN {ean}: {e}")
            return None

    async def get_product_comparison(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get product comparison data across different shops"""
        try:
            logger.info(f"Getting product comparison for ID: {product_id}")
            
            # First, get the base product to find its EAN, MPN, and title
            base_query = text("""
                SELECT 
                    p.id,
                    p.title,
                    p.description,
                    p.price,
                    p.availability,
                    p.ean,
                    p.mpn,
                    p.image_url,
                    p.product_url,
                    s.name as shop_name,
                    b.name as brand_name,
                    c.name as category_name
                FROM products p
                JOIN shops s ON p.shop_id = s.id
                LEFT JOIN brands b ON p.brand_id = b.id
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE p.id = :product_id
            """)
            
            result = await self.db.execute(base_query, {"product_id": product_id})
            base_product = result.fetchone()
            
            if not base_product:
                logger.error(f"Product {product_id} not found in database")
                return None
            
            logger.info(f"Base product: {base_product.title} (EAN: {base_product.ean}, MPN: {base_product.mpn}, Brand: {base_product.brand_name})")
            
            # Find exact same products across different shops using EAN, MPN, or exact title match
            comparison_query = text("""
                SELECT DISTINCT ON (s.name)
                    p.id,
                    p.title,
                    p.description,
                    p.price,
                    p.availability,
                    p.ean,
                    p.mpn,
                    p.image_url,
                    p.product_url,
                    s.name as shop_name,
                    b.name as brand_name,
                    c.name as category_name
                FROM products p
                JOIN shops s ON p.shop_id = s.id
                LEFT JOIN brands b ON p.brand_id = b.id
                LEFT JOIN categories c ON p.category_id = c.id
                WHERE (
                    -- Exact EAN match (highest priority)
                    (p.ean IS NOT NULL AND p.ean = :ean AND p.ean != '' AND p.ean IS NOT NULL)
                    OR
                    -- Exact MPN match (second priority)
                    (p.mpn IS NOT NULL AND p.mpn = :mpn AND p.mpn != '' AND p.mpn IS NOT NULL)
                    OR
                    -- Exact title match (third priority)
                    (LOWER(p.title) = LOWER(:title) AND p.id != :product_id)
                )
                AND (p.price IS NOT NULL OR p.availability = true)
                ORDER BY 
                    s.name,
                    CASE 
                        WHEN p.ean = :ean THEN 1
                        WHEN p.mpn = :mpn THEN 2
                        WHEN LOWER(p.title) = LOWER(:title) THEN 3
                        ELSE 4
                    END,
                    p.price ASC, 
                    p.availability DESC, 
                    p.updated_at DESC
                LIMIT 10
            """)
            
            comparison_result = await self.db.execute(comparison_query, {
                "product_id": product_id,
                "ean": base_product.ean,
                "mpn": base_product.mpn,
                "title": base_product.title
            })
            
            comparison_products = comparison_result.fetchall()
            
            logger.info(f"Found {len(comparison_products)} exact matches for product {product_id}")
            if comparison_products:
                for i, product in enumerate(comparison_products):
                    logger.info(f"  Match {i+1}: {product.shop_name} - {product.title[:50]}... (EAN: {product.ean}, MPN: {product.mpn})")
            
            # Log unique shops found
            unique_shops = set()
            for product in comparison_products:
                unique_shops.add(product.shop_name)
            logger.info(f"Unique shops found: {len(unique_shops)} - {list(unique_shops)}")
            
            # If no exact matches found, try a very strict broader search (only as last resort)
            if not comparison_products:
                logger.info("No exact matches found, trying very strict broader search")
                broader_query = text("""
                    SELECT DISTINCT ON (s.name)
                        p.id,
                        p.title,
                        p.description,
                        p.price,
                        p.availability,
                        p.ean,
                        p.mpn,
                        p.image_url,
                        p.product_url,
                        s.name as shop_name,
                        b.name as brand_name,
                        c.name as category_name
                    FROM products p
                    JOIN shops s ON p.shop_id = s.id
                    LEFT JOIN brands b ON p.brand_id = b.id
                    LEFT JOIN categories c ON p.category_id = c.id
                    WHERE (
                        -- Very high similarity threshold (0.8+)
                        (p.title % :title AND similarity(p.title, :title) > 0.8)
                        OR
                        -- Same brand and very similar title
                        (b.name = :brand_name AND similarity(p.title, :title) > 0.7)
                    )
                    AND (p.price IS NOT NULL OR p.availability = true)
                    AND p.id != :product_id
                    ORDER BY 
                        s.name,
                        similarity(p.title, :title) DESC, 
                        p.price ASC, 
                        p.availability DESC
                    LIMIT 5
                """)
                
                broader_result = await self.db.execute(broader_query, {
                    "product_id": product_id,
                    "title": base_product.title,
                    "brand_name": base_product.brand_name
                })
                
                comparison_products = broader_result.fetchall()
                
                if comparison_products:
                    logger.info(f"Found {len(comparison_products)} similar products with high similarity threshold")
                    for i, product in enumerate(comparison_products):
                        logger.info(f"  Similar {i+1}: {product.shop_name} - {product.title[:50]}...")
                else:
                    logger.info("No similar products found even with broader search - will show only base product")
            
            # Convert to list format with deduplication by shop
            products_list = []
            prices = []
            available_count = 0
            total_shops = 0
            seen_shops = set()
            
            # Add the base product first
            base_product_data = {
                "id": base_product.id,
                "title": base_product.title,
                "description": base_product.description,
                "price": float(base_product.price) if base_product.price else 0,
                "image_url": base_product.image_url,
                "availability": base_product.availability,
                "ean": base_product.ean or "",
                "mpn": base_product.mpn or "",
                "url": base_product.product_url or "",
                "shop_name": base_product.shop_name,
                "brand_name": base_product.brand_name or "",
                "category_name": base_product.category_name or ""
            }
            products_list.append(base_product_data)
            seen_shops.add(base_product.shop_name.lower())
            total_shops += 1
            
            if base_product.price:
                prices.append(float(base_product.price))
            if base_product.availability:
                available_count += 1
            
            # Add comparison products (deduplicate by shop)
            for product in comparison_products:
                # Skip if we already have a product from this shop
                if product.shop_name.lower() in seen_shops:
                    logger.info(f"Skipping duplicate shop: {product.shop_name} - {product.title[:50]}...")
                    continue
                
                product_data = {
                    "id": product.id,
                    "title": product.title,
                    "description": product.description,
                    "price": float(product.price) if product.price else 0,
                    "image_url": product.image_url,
                    "availability": product.availability,
                    "ean": product.ean or "",
                    "mpn": product.mpn or "",
                    "url": product.product_url or "",
                    "shop_name": product.shop_name,
                    "brand_name": product.brand_name or "",
                    "category_name": product.category_name or ""
                }
                products_list.append(product_data)
                seen_shops.add(product.shop_name.lower())
                total_shops += 1
                
                if product.price:
                    prices.append(float(product.price))
                if product.availability:
                    available_count += 1
            
            # Calculate stats
            min_price = min(prices) if prices else 0
            max_price = max(prices) if prices else 0
            best_price = min_price
            
            logger.info(f"Found {len(products_list)} products for comparison across {total_shops} shops, {available_count} available")
            
            return {
                "title": base_product.title,
                "description": base_product.description,
                "products": products_list,
                "min_price": min_price,
                "max_price": max_price,
                "best_price": best_price,
                "available_count": available_count,
                "total_shops": total_shops,
                "total_count": len(products_list)
            }
            
        except Exception as e:
            logger.error(f"Error getting product comparison {product_id}: {e}")
            return None

    async def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get AI-enhanced search suggestions based on query"""
        try:
            if not query or len(query) < 2:
                return []
                
            # Process query with AI for better suggestions
            query_analysis = await self.process_query_with_ai(query)
            suggestions = []

            # Add AI-generated suggestions
            if query_analysis.get('suggestions'):
                suggestions.extend(query_analysis['suggestions'][:limit//2])
            
            # Add corrected query if different from original
            if query_analysis.get('corrected_query') and query_analysis['corrected_query'] != query:
                suggestions.insert(0, query_analysis['corrected_query'])
            
            # Get database-based suggestions
            db_suggestions = await self._get_database_suggestions(query, limit // 2)
            suggestions.extend(db_suggestions)
            
            # Remove duplicates and limit
            unique_suggestions = []
            seen = set()
            for suggestion in suggestions:
                if suggestion.lower() not in seen and len(suggestion) >= 2:
                    unique_suggestions.append(suggestion)
                    seen.add(suggestion.lower())
                    if len(unique_suggestions) >= limit:
                        break
            
            return unique_suggestions

        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return await self._get_database_suggestions(query, limit)

    async def _get_database_suggestions(self, query: str, limit: int) -> List[str]:
        """Get database-based search suggestions"""
        try:
            suggestions = []

            # Title suggestions with improved matching
            title_query = select(Product.title).where(
                or_(
                    func.lower(Product.title).contains(query.lower()),
                    func.lower(Product.title).like(f"{query.lower()}%"),
                    func.lower(Product.search_text).contains(query.lower())
                )
            ).limit(limit // 3)

            title_result = await self.db.execute(title_query)
            titles = [row[0] for row in title_result if row[0]]
            suggestions.extend(titles)

            # Brand suggestions
            brand_query = select(Brand.name).where(
                or_(
                    func.lower(Brand.name).contains(query.lower()),
                    func.lower(Brand.name).like(f"{query.lower()}%")
                )
            ).limit(limit // 3)

            brand_result = await self.db.execute(brand_query)
            brands = [row[0] for row in brand_result if row[0]]
            suggestions.extend(brands)

            # Category suggestions
            category_query = select(Category.name).where(
                or_(
                    func.lower(Category.name).contains(query.lower()),
                    func.lower(Category.name).like(f"{query.lower()}%")
                )
            ).limit(limit // 3)

            category_result = await self.db.execute(category_query)
            categories = [row[0] for row in category_result if row[0]]
            suggestions.extend(categories)

            return suggestions

        except Exception as e:
            logger.error(f"Error getting database suggestions: {e}")
            return []

    async def fuzzy_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get fuzzy search suggestions with misspelling correction"""
        try:
            if not query or len(query) < 2:
                return []
                
            # Get all possible suggestions from database
            all_titles = await self.db.execute(select(Product.title).distinct())
            all_brands = await self.db.execute(select(Brand.name).distinct())
            all_categories = await self.db.execute(select(Category.name).distinct())
            
            titles = [row[0] for row in all_titles if row[0]]
            brands = [row[0] for row in all_brands if row[0]]
            categories = [row[0] for row in all_categories if row[0]]
            
            # Combine all searchable terms
            all_terms = titles + brands + categories
            
            # Use fuzzy matching to find similar terms
            matches = process.extract(query, all_terms, limit=limit, scorer=fuzz.partial_ratio)
            
            # Filter matches with good similarity (above 60%)
            good_matches = [match[0] for match in matches if match[1] > 60]
            
            return good_matches[:limit]
            
        except Exception as e:
            logger.error(f"Error in fuzzy search suggestions: {e}")
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

            # Price stats
            price_query = select(
                func.min(Product.price).label('min_price'),
                func.max(Product.price).label('max_price'),
                func.avg(Product.price).label('avg_price')
            ).where(Product.price.is_not(None))

            price_result = await self.db.execute(price_query)
            price_stats = price_result.first()

            if price_stats and price_stats[0] is not None:
                facets['price_stats'] = {
                    'min': float(price_stats[0]),
                    'max': float(price_stats[1]),
                    'avg': float(price_stats[2])
                }

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

    async def get_category_distribution(self, filters: SearchFilters, limit: int = 10) -> List[Dict[str, Any]]:
        """Get category distribution for current search results - SIMPLIFIED VERSION"""
        try:
            # Only get categories if we have a search query
            if not filters.title or len(filters.title.strip()) < 2:
                return []
            
            # Fast query: get categories with product counts and representative images from matching products
            query = text("""
                WITH category_counts AS (
                    SELECT 
                        c.id,
                        c.name,
                        COUNT(p.id) as count
                    FROM categories c
                    JOIN products p ON p.category_id = c.id
                    WHERE c.id IS NOT NULL 
                    AND LOWER(p.title) LIKE LOWER(:search_term)
                    GROUP BY c.id, c.name
                ),
                category_images AS (
                    SELECT DISTINCT ON (category_id) 
                        category_id,
                        image_url
                    FROM products 
                    WHERE image_url IS NOT NULL 
                    AND image_url != '' 
                    AND image_url != 'N/A' 
                    AND image_url != 'null'
                    AND LOWER(title) LIKE LOWER(:search_term)
                    AND category_id IN (SELECT id FROM category_counts)
                    ORDER BY category_id, id
                )
                SELECT 
                    cc.id,
                    cc.name,
                    cc.count,
                    ci.image_url as representative_image
                FROM category_counts cc
                LEFT JOIN category_images ci ON cc.id = ci.category_id
                ORDER BY cc.count DESC
                LIMIT :limit
            """)
            
            result = await self.db.execute(query, {
                'search_term': f'%{filters.title}%',
                'limit': limit
            })
            
            categories = []
            for row in result:
                category_id, category_name, count, representative_image = row
                if count > 0:  # Only include categories with products
                    category_name_en = self._translate_category_name(category_name)
                    categories.append({
                        'category_id': category_id,
                        'category_name': category_name,
                        'category_name_en': category_name_en,
                        'count': count,
                        'percentage': 0,  # Simplified - no percentage calculation
                        'representative_image': representative_image
                    })
            
            return categories
            
        except Exception as e:
            logger.warning(f"Error getting category distribution: {e}")
            return []

    def _translate_category_name(self, category_name: str) -> str:
        """Translate category name to English (simple mapping)"""
        # Greek to English category translations
        translations = {
            # Electronics
            'Ηλεκτρονικά': 'Electronics',
            'Κινητά Τηλέφωνα': 'Mobile Phones',
            'Smartphones': 'Smartphones',
            'Τηλέφωνα': 'Phones',
            'Υπολογιστές': 'Computers',
            'Laptops': 'Laptops',
            'Tablets': 'Tablets',
            'Τηλεοράσεις': 'TVs',
            'Οθόνες': 'Monitors',
            'Ακουστικά': 'Headphones',
            'Ηχεία': 'Speakers',
            'Κάμερες': 'Cameras',
            'Φωτογραφικές Μηχανές': 'Cameras',
            
            # Fashion
            'Ρούχα': 'Clothing',
            'Παπούτσια': 'Shoes',
            'Αθλητικά': 'Sports',
            'Άθληση': 'Sports',
            'Μόδα': 'Fashion',
            'Accessories': 'Accessories',
            'Αξεσουάρ': 'Accessories',
            
            # Home & Garden
            'Σπίτι': 'Home',
            'Κήπος': 'Garden',
            'Κουζίνα': 'Kitchen',
            'Μπάνιο': 'Bathroom',
            'Έπιπλα': 'Furniture',
            
            # Books & Media
            'Βιβλία': 'Books',
            'Βιβλιοθήκη': 'Books',
            'Ταινίες': 'Movies',
            'Μουσική': 'Music',
            'Games': 'Games',
            'Παιχνίδια': 'Games',
            
            # Health & Beauty
            'Υγεία': 'Health',
            'Ομορφιά': 'Beauty',
            'Καλλυντικά': 'Cosmetics',
            'Φάρμακα': 'Medicine',
            
            # Automotive
            'Αυτοκίνητα': 'Automotive',
            'Αυτοκινητικά': 'Automotive',
            'Μοτοσυκλέτες': 'Motorcycles',
            
            # Tools & DIY
            'Εργαλεία': 'Tools',
            'DIY': 'DIY',
            'Κατασκευές': 'DIY',
            
            # Toys & Kids
            'Παιχνίδια': 'Toys',
            'Παιδικά': 'Kids',
            'Μωρά': 'Babies',
            
            # Food & Beverages
            'Τρόφιμα': 'Food',
            'Ροφήματα': 'Beverages',
            'Καφέ': 'Coffee',
            'Τσάι': 'Tea',
            
            # Office & Business
            'Γραφείο': 'Office',
            'Επιχειρήσεις': 'Business',
            'Εκτύπωση': 'Printing',
            
            # Default fallbacks
            'Άλλα': 'Others',
            'Διάφορα': 'Miscellaneous'
        }
        
        return translations.get(category_name, category_name)
