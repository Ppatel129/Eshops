#!/usr/bin/env python3
"""
Very simple test to check category images
"""

import asyncio
import asyncpg

async def simple_test():
    """Simple test to check if category images work"""
    try:
        conn = await asyncpg.connect("postgresql://postgres:123123@localhost:5432/postgres")
        
        # Test the exact query we're using
        query = """
        WITH category_counts AS (
            SELECT 
                c.id,
                c.name,
                COUNT(p.id) as count
            FROM categories c
            JOIN products p ON p.category_id = c.id
            WHERE c.id IS NOT NULL 
            AND LOWER(p.title) LIKE LOWER('%aaa%')
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
            AND LOWER(title) LIKE LOWER('%aaa%')
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
        LIMIT 3
        """
        
        print("Testing category images query...")
        results = await conn.fetch(query)
        
        print(f"Found {len(results)} categories:")
        for row in results:
            print(f"  Category: {row['name']}")
            print(f"    Count: {row['count']}")
            print(f"    Image: {row['representative_image']}")
            print()
        
        await conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(simple_test()) 