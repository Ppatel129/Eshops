import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from elasticsearch import AsyncElasticsearch, ConnectionError
from elasticsearch.helpers import async_bulk
from fuzzywuzzy import fuzz, process
from config import Settings
import logging

logger = logging.getLogger(__name__)

class ElasticsearchService:
    def __init__(self):
        self.settings = Settings()
        self.client = None
        self.index_name = "products"
        
    async def connect(self):
        """Initialize Elasticsearch connection"""
        # Check if Elasticsearch is enabled in configuration
        if not self.settings.ELASTICSEARCH_ENABLED:
            logger.info("Elasticsearch disabled in configuration, using PostgreSQL search only")
            self.client = None
            return False
            
        # First check if Elasticsearch is available without creating a client
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 9200))
            sock.close()
            
            if result != 0:
                logger.warning("Elasticsearch not available (port 9200 not accessible), falling back to PostgreSQL search")
                self.client = None
                return False
        except Exception:
            logger.warning("Could not check Elasticsearch availability, falling back to PostgreSQL search")
            self.client = None
            return False
            
        try:
            # Only create client if port is accessible
            self.client = AsyncElasticsearch(
                hosts=[{"host": "localhost", "port": 9200, "scheme": "http"}],
                timeout=3,  # Very short timeout
                max_retries=0,  # No retries
                retry_on_timeout=False
            )
            # Test connection with very short timeout
            await asyncio.wait_for(self.client.ping(), timeout=2.0)
            logger.info("Connected to Elasticsearch successfully")
            return True
        except Exception as e:
            logger.warning(f"Elasticsearch connection failed ({type(e).__name__}), falling back to PostgreSQL search")
            self.client = None
            return False
    
    async def create_index(self):
        """Create products index with proper mappings"""
        if not self.client:
            return False
            
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "greek_analyzer": {
                            "tokenizer": "standard",
                            "filter": ["lowercase", "greek_stop", "greek_stemmer"]
                        },
                        "search_analyzer": {
                            "tokenizer": "standard",
                            "filter": ["lowercase", "asciifolding"]
                        }
                    },
                    "filter": {
                        "greek_stop": {
                            "type": "stop",
                            "stopwords": ["το", "της", "και", "με", "για", "από", "στο", "στη", "στην"]
                        },
                        "greek_stemmer": {
                            "type": "stemmer",
                            "language": "greek"
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "id": {"type": "long"},
                    "title": {
                        "type": "text",
                        "analyzer": "greek_analyzer",
                        "search_analyzer": "search_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "suggest": {"type": "completion"}
                        }
                    },
                    "description": {
                        "type": "text",
                        "analyzer": "greek_analyzer"
                    },
                    "category": {
                        "type": "text",
                        "analyzer": "greek_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "suggest": {"type": "completion"}
                        }
                    },
                    "category_path": {
                        "type": "text",
                        "analyzer": "greek_analyzer"
                    },
                    "brand": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "suggest": {"type": "completion"}
                        }
                    },
                    "price": {"type": "float"},
                    "original_price": {"type": "float"},
                    "availability": {"type": "boolean"},
                    "stock_quantity": {"type": "integer"},
                    "shop": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "ean": {"type": "keyword"},
                    "mpn": {"type": "keyword"},
                    "sku": {"type": "keyword"},
                    "image_url": {"type": "keyword"},
                    "product_url": {"type": "keyword"},
                    "specifications": {"type": "object"},
                    "features": {"type": "object"},
                    "tags": {"type": "keyword"},
                    "search_text": {
                        "type": "text",
                        "analyzer": "greek_analyzer",
                        "search_analyzer": "search_analyzer"
                    },
                    "variants": {
                        "type": "nested",
                        "properties": {
                            "color": {"type": "keyword"},
                            "size": {"type": "keyword"},
                            "price": {"type": "float"},
                            "availability": {"type": "boolean"}
                        }
                    },
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"}
                }
            }
        }
        
        try:
            if await self.client.indices.exists(index=self.index_name):
                await self.client.indices.delete(index=self.index_name)
            
            await self.client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"Created Elasticsearch index: {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return False
    
    async def index_products(self, products: List[Dict[str, Any]]):
        """Bulk index products to Elasticsearch"""
        if not self.client or not products:
            return False
            
        actions = []
        for product in products:
            # Prepare document for indexing
            doc = {
                "_index": self.index_name,
                "_id": product.get("id"),
                "_source": {
                    "id": product.get("id"),
                    "title": product.get("title", ""),
                    "description": product.get("description", ""),
                    "category": product.get("category", {}).get("name", "") if product.get("category") else "",
                    "category_path": product.get("category", {}).get("path", "") if product.get("category") else "",
                    "brand": product.get("brand", {}).get("name", "") if product.get("brand") else "",
                    "price": product.get("price"),
                    "original_price": product.get("original_price"),
                    "availability": product.get("availability", False),
                    "stock_quantity": product.get("stock_quantity", 0),
                    "shop": product.get("shop", {}).get("name", "") if product.get("shop") else "",
                    "ean": product.get("ean"),
                    "mpn": product.get("mpn"),
                    "sku": product.get("sku"),
                    "image_url": product.get("image_url"),
                    "product_url": product.get("product_url"),
                    "specifications": product.get("specifications", {}),
                    "features": product.get("features", {}),
                    "tags": product.get("tags", []),
                    "search_text": f"{product.get('title', '')} {product.get('description', '')} {product.get('brand', {}).get('name', '') if product.get('brand') else ''}",
                    "variants": product.get("variants", []),
                    "created_at": product.get("created_at"),
                    "updated_at": product.get("updated_at")
                }
            }
            actions.append(doc)
        
        try:
            await async_bulk(self.client, actions, chunk_size=100)
            logger.info(f"Indexed {len(actions)} products to Elasticsearch")
            return True
        except Exception as e:
            logger.error(f"Failed to index products: {e}")
            return False
    
    async def search_products(
        self, 
        query: str = "", 
        filters: Dict[str, Any] = None, 
        page: int = 1, 
        per_page: int = 50
    ) -> Dict[str, Any]:
        """Search products with advanced filtering"""
        if not self.client:
            return {"products": [], "total": 0, "aggregations": {}}
            
        if filters is None:
            filters = {}
        
        # Build Elasticsearch query
        es_query = {
            "from": (page - 1) * per_page,
            "size": per_page,
            "query": {
                "bool": {
                    "must": [],
                    "filter": []
                }
            },
            "aggs": {
                "brands": {
                    "terms": {"field": "brand.keyword", "size": 50}
                },
                "categories": {
                    "terms": {"field": "category.keyword", "size": 50}
                },
                "shops": {
                    "terms": {"field": "shop.keyword", "size": 50}
                },
                "price_stats": {
                    "stats": {"field": "price"}
                },
                "availability": {
                    "terms": {"field": "availability"}
                }
            },
            "sort": [
                {"availability": {"order": "desc"}},
                {"_score": {"order": "desc"}},
                {"price": {"order": "asc"}}
            ]
        }
        
        # Add search query
        if query:
            es_query["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": query,
                    "fields": [
                        "title^3",
                        "description^2",
                        "brand^2",
                        "category^2",
                        "category_path",
                        "search_text",
                        "ean",
                        "mpn"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            })
        else:
            es_query["query"]["bool"]["must"].append({"match_all": {}})
        
        # Add filters
        if filters.get("brand"):
            es_query["query"]["bool"]["filter"].append({
                "term": {"brand.keyword": filters["brand"]}
            })
        
        if filters.get("category"):
            es_query["query"]["bool"]["filter"].append({
                "term": {"category.keyword": filters["category"]}
            })
        
        if filters.get("shop"):
            es_query["query"]["bool"]["filter"].append({
                "term": {"shop.keyword": filters["shop"]}
            })
        
        if filters.get("availability") is not None:
            es_query["query"]["bool"]["filter"].append({
                "term": {"availability": filters["availability"]}
            })
        
        # Price range filter
        if filters.get("min_price") is not None or filters.get("max_price") is not None:
            price_range = {}
            if filters.get("min_price") is not None:
                price_range["gte"] = filters["min_price"]
            if filters.get("max_price") is not None:
                price_range["lte"] = filters["max_price"]
            
            es_query["query"]["bool"]["filter"].append({
                "range": {"price": price_range}
            })
        
        try:
            response = await self.client.search(index=self.index_name, body=es_query)
            
            products = []
            for hit in response["hits"]["hits"]:
                product = hit["_source"]
                product["score"] = hit["_score"]
                products.append(product)
            
            return {
                "products": products,
                "total": response["hits"]["total"]["value"],
                "aggregations": response.get("aggregations", {}),
                "took": response.get("took", 0)
            }
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"products": [], "total": 0, "aggregations": {}}
    
    async def get_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get search suggestions using fuzzy matching"""
        if not self.client or not query:
            return []
        
        # Try exact prefix matching first
        es_query = {
            "size": 0,
            "suggest": {
                "title_suggest": {
                    "prefix": query,
                    "completion": {
                        "field": "title.suggest",
                        "size": limit,
                        "skip_duplicates": True
                    }
                },
                "brand_suggest": {
                    "prefix": query,
                    "completion": {
                        "field": "brand.suggest",
                        "size": limit,
                        "skip_duplicates": True
                    }
                },
                "category_suggest": {
                    "prefix": query,
                    "completion": {
                        "field": "category.suggest",
                        "size": limit,
                        "skip_duplicates": True
                    }
                }
            }
        }
        
        try:
            response = await self.client.search(index=self.index_name, body=es_query)
            suggestions = set()
            
            for suggest_type in ["title_suggest", "brand_suggest", "category_suggest"]:
                for suggestion in response["suggest"][suggest_type][0]["options"]:
                    suggestions.add(suggestion["text"])
            
            return list(suggestions)[:limit]
            
        except Exception as e:
            logger.error(f"Suggestion failed: {e}")
            return []
    
    async def search_categories(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search categories specifically"""
        if not self.client:
            return []
        
        es_query = {
            "size": 0,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["category^2", "category_path"],
                    "type": "best_fields",
                    "fuzziness": "AUTO"
                }
            },
            "aggs": {
                "categories": {
                    "terms": {
                        "field": "category.keyword",
                        "size": limit
                    }
                }
            }
        }
        
        try:
            response = await self.client.search(index=self.index_name, body=es_query)
            categories = []
            
            for bucket in response["aggregations"]["categories"]["buckets"]:
                categories.append({
                    "name": bucket["key"],
                    "count": bucket["doc_count"]
                })
            
            return categories
            
        except Exception as e:
            logger.error(f"Category search failed: {e}")
            return []
    
    async def close(self):
        """Close Elasticsearch connection"""
        if self.client:
            await self.client.close()

# Global instance
elasticsearch_service = ElasticsearchService()