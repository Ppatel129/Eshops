#!/usr/bin/env python3
"""
Test script to analyze XML feeds and understand stock/availability data structure
"""

import asyncio
import logging
from xml_parser import XMLFeedParser
from config import settings

# Set up logging - only show INFO and above to reduce noise
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

async def analyze_xml_feeds():
    """Analyze XML feeds to understand stock/availability data"""
    
    async with XMLFeedParser() as parser:
        for shop_name, xml_url in settings.XML_FEEDS.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"Analyzing feed: {shop_name}")
            logger.info(f"URL: {xml_url}")
            logger.info(f"{'='*60}")
            
            try:
                # Parse the feed
                logger.info("Fetching and parsing XML feed...")
                products = await parser.parse_feed(xml_url)
                logger.info(f"Total products found: {len(products)}")
                
                if not products:
                    logger.warning("No products found in feed")
                    continue
                
                # Analyze first 5 products for stock/availability data
                logger.info("Analyzing stock/availability data for first 5 products...")
                stock_analysis = {
                    'has_availability': 0,
                    'has_stock_quantity': 0,
                    'availability_values': set(),
                    'stock_quantity_values': set(),
                    'sample_products': []
                }
                
                for i, product in enumerate(products[:5]):  # Analyze first 5 products
                    logger.info(f"\nProduct {i+1}: {product.get('title', 'No title')[:50]}...")
                    
                    # Check availability
                    if 'availability' in product:
                        stock_analysis['has_availability'] += 1
                        avail_value = product['availability']
                        stock_analysis['availability_values'].add(str(avail_value))
                        logger.info(f"  Availability: {avail_value} (type: {type(avail_value)})")
                    else:
                        logger.info("  Availability: NOT FOUND")
                    
                    # Check stock quantity
                    if 'stock_quantity' in product:
                        stock_analysis['has_stock_quantity'] += 1
                        stock_value = product['stock_quantity']
                        stock_analysis['stock_quantity_values'].add(str(stock_value))
                        logger.info(f"  Stock Quantity: {stock_value} (type: {type(stock_value)})")
                    else:
                        logger.info("  Stock Quantity: NOT FOUND")
                    
                    # Store sample product data
                    stock_analysis['sample_products'].append({
                        'title': product.get('title', 'No title')[:50],
                        'availability': product.get('availability'),
                        'stock_quantity': product.get('stock_quantity'),
                        'raw_data': {k: v for k, v in product.items() if 'stock' in k.lower() or 'avail' in k.lower()}
                    })
                
                # Summary
                logger.info(f"\nSummary for {shop_name}:")
                logger.info(f"  Products with availability data: {stock_analysis['has_availability']}/5")
                logger.info(f"  Products with stock quantity data: {stock_analysis['has_stock_quantity']}/5")
                logger.info(f"  Availability values found: {stock_analysis['availability_values']}")
                logger.info(f"  Stock quantity values found: {stock_analysis['stock_quantity_values']}")
                
                # Show raw data for debugging
                logger.info(f"\nRaw stock/availability data from first product:")
                if stock_analysis['sample_products']:
                    raw_data = stock_analysis['sample_products'][0]['raw_data']
                    for key, value in raw_data.items():
                        logger.info(f"  {key}: {value}")
                
            except Exception as e:
                logger.error(f"Error analyzing feed {shop_name}: {e}")

async def main():
    """Main function"""
    logger.info("Starting XML feed analysis...")
    await analyze_xml_feeds()
    logger.info("Analysis complete!")

if __name__ == "__main__":
    asyncio.run(main()) 