import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from urllib.parse import urljoin, urlparse
import re

logger = logging.getLogger(__name__)

class XMLFeedParser:
    def __init__(self, timeout: int = 300):
        self.timeout = timeout
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_xml(self, url: str) -> Optional[str]:
        """Fetch XML content from URL"""
        try:
            logger.info(f"Fetching XML from: {url}")
            if self.session is None:
                logger.error("Session is not initialized")
                return None
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"Successfully fetched XML content ({len(content)} chars)")
                    return content
                else:
                    logger.error(f"Failed to fetch XML: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching XML from {url}: {e}")
            return None
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for search and comparison"""
        if not text:
            return ""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        return text.lower()
    
    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None
        
        # Remove currency symbols and extract number
        price_clean = re.sub(r'[^\d.,]', '', price_text)
        price_clean = price_clean.replace(',', '.')
        
        try:
            return float(price_clean)
        except ValueError:
            return None
    
    def parse_category_path(self, category_text: str) -> Tuple[str, List[str]]:
        """Parse category path and return normalized name and path components"""
        if not category_text:
            return "", []
        
        # Split by common separators
        path_parts = re.split(r'[>\/\-\|]', category_text)
        path_parts = [part.strip() for part in path_parts if part.strip()]
        
        # Return the last part as main category and full path
        main_category = path_parts[-1] if path_parts else ""
        return main_category, path_parts
    
    def extract_image_urls(self, image_text: str) -> Tuple[Optional[str], List[str]]:
        """Extract main image URL and additional images"""
        if not image_text:
            return None, []
        
        # Split by common separators for multiple images
        urls = re.split(r'[,;\|]', image_text)
        urls = [url.strip() for url in urls if url.strip()]
        
        # Validate URLs
        valid_urls = []
        for url in urls:
            if self.is_valid_url(url):
                valid_urls.append(url)
        
        main_image = valid_urls[0] if valid_urls else None
        additional_images = valid_urls[1:] if len(valid_urls) > 1 else []
        
        return main_image, additional_images
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def parse_skroutz_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        """Parse Skroutz XML format"""
        products = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Find products based on common XML structures
            product_elements = root.findall('.//product') or root.findall('.//item')
            
            logger.info(f"Found {len(product_elements)} products in XML")
            
            for product_elem in product_elements:
                try:
                    product_data = self.extract_product_data(product_elem)
                    if product_data:
                        products.append(product_data)
                except Exception as e:
                    logger.warning(f"Error parsing product: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(products)} products")
            return products
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing XML: {e}")
            return []
    
    def extract_product_data(self, product_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """Extract product data from XML element"""
        try:
            # Common field mappings for Skroutz XML
            field_mappings = {
                'title': ['name', 'title', 'product_name'],
                'description': ['description', 'summary'],
                'ean': ['ean', 'barcode'],
                'mpn': ['mpn', 'model', 'part_number'],
                'sku': ['sku', 'id', 'product_id', 'uid'],
                'price': ['price_with_vat', 'price', 'final_price', 'selling_price'],
                'price_without_vat': ['price_without_vat', 'price_no_vat', 'net_price'],
                'original_price': ['original_price', 'list_price'],
                'availability': ['instock', 'availability', 'in_stock', 'stock'],
                'stock_quantity': ['quantity', 'stock_quantity'],
                'image_url': ['image', 'image_url', 'main_image'],
                'product_url': ['link', 'url', 'product_url'],
                'brand': ['manufacturer', 'brand'],
                'category': ['category', 'categories'],
                'color': ['color', 'colour'],
                'size': ['size', 'dimensions'],
                'material': ['material', 'fabric'],
            }
            
            product_data = {}
            
            # Extract basic fields
            for field, possible_tags in field_mappings.items():
                value = self.get_element_value(product_elem, possible_tags)
                if value:
                    product_data[field] = value
            
            # Process specific fields
            if 'title' not in product_data:
                logger.warning("Product missing title, skipping")
                return None
            
            # Process price
            if 'price' in product_data:
                product_data['price'] = self.extract_price(product_data['price'])
            
            if 'price_without_vat' in product_data:
                product_data['price_without_vat'] = self.extract_price(product_data['price_without_vat'])
                # If we have price without VAT, use it as the main price
                if product_data['price_without_vat']:
                    product_data['price'] = product_data['price_without_vat']
            
            if 'original_price' in product_data:
                product_data['original_price'] = self.extract_price(product_data['original_price'])
            
            # Calculate discount
            price = product_data.get('price')
            original_price = product_data.get('original_price')
            if price is not None and original_price is not None and original_price > price:
                product_data['discount_percentage'] = round(((original_price - price) / original_price) * 100, 2)
            
            # Process availability
            if 'availability' in product_data:
                avail_text = str(product_data['availability']).lower()
                # Handle various availability formats
                product_data['availability'] = avail_text in ['true', '1', 'yes', 'y', 'available', 'in stock', 'διαθέσιμο']
            else:
                product_data['availability'] = False
            
            # Process stock quantity
            if 'stock_quantity' in product_data:
                try:
                    product_data['stock_quantity'] = int(product_data['stock_quantity'])
                except ValueError:
                    product_data['stock_quantity'] = None
            
            # Process images
            if 'image_url' in product_data:
                main_image, additional_images = self.extract_image_urls(product_data['image_url'])
                product_data['image_url'] = main_image
                product_data['additional_images'] = additional_images
            
            # Process category
            if 'category' in product_data:
                main_category, category_path = self.parse_category_path(product_data['category'])
                product_data['category'] = main_category
                product_data['category_path'] = category_path
            
            # Create search text (limit length to avoid index issues)
            search_parts = []
            for field in ['title', 'brand', 'category', 'ean', 'mpn']:
                if field in product_data and product_data[field]:
                    search_parts.append(str(product_data[field]))
            
            # Add limited description (first 200 chars)
            if 'description' in product_data and product_data['description']:
                desc = str(product_data['description'])[:200]
                search_parts.append(desc)
            
            search_text = ' '.join(search_parts)
            # Limit total search text to 1000 characters to avoid index issues
            product_data['search_text'] = search_text[:1000]
            
            # Extract specifications from remaining elements
            specs = {}
            for child in product_elem:
                if child.tag not in [tag for tags in field_mappings.values() for tag in tags]:
                    if child.text and child.text.strip():
                        specs[child.tag] = child.text.strip()
            
            if specs:
                product_data['specifications'] = specs
            
            return product_data
            
        except Exception as e:
            logger.error(f"Error extracting product data: {e}")
            return None
    
    def get_element_value(self, parent: ET.Element, tag_names: List[str]) -> Optional[str]:
        """Get value from first matching tag"""
        for tag in tag_names:
            elem = parent.find(tag)
            if elem is not None and elem.text:
                return elem.text.strip()
        return None
    
    async def parse_feed(self, url: str) -> List[Dict[str, Any]]:
        """Parse XML feed from URL"""
        xml_content = await self.fetch_xml(url)
        if not xml_content:
            return []
        
        return self.parse_skroutz_xml(xml_content)
