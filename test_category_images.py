#!/usr/bin/env python3
"""
Simple test script to check category images quickly
"""

import asyncio
import asyncpg

async def test_category_images():
    """Test what images are available for categories - FAST VERSION"""
    try:
        # Connect to database using the correct URL
        conn = await asyncpg.connect("postgresql://postgres:123123@localhost:5432/postgres")
        
        # Simple query to check if we have any images at all
        print("Checking for images in database...")
        
        # Count products with images
        count_query = """
        SELECT 
            COUNT(*) as total_products,
            COUNT(CASE WHEN image_url IS NOT NULL AND image_url != '' AND image_url != 'N/A' AND image_url != 'null' THEN 1 END) as products_with_images
        FROM products
        """
        
        result = await conn.fetchrow(count_query)
        total_products, products_with_images = result
        
        print(f"Total products: {total_products}")
        print(f"Products with images: {products_with_images}")
        print(f"Percentage with images: {(products_with_images/total_products*100):.1f}%" if total_products > 0 else "0%")
        
        # Get a few sample images
        sample_query = """
        SELECT image_url, title 
        FROM products 
        WHERE image_url IS NOT NULL 
        AND image_url != '' 
        AND image_url != 'N/A' 
        AND image_url != 'null'
        LIMIT 5
        """
        
        samples = await conn.fetch(sample_query)
        print(f"\nSample images:")
        for sample in samples:
            print(f"  {sample['title'][:50]}... -> {sample['image_url']}")
        
        await conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_category_images()) 