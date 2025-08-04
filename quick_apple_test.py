import asyncio
import asyncpg
from config import settings

async def quick_apple_test():
    """Quick test for Apple TV products"""
    
    print("Connecting to database...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(settings.DATABASE_URL)
        print("✓ Database connected successfully\n")
        
        # Quick count check
        total_products = await conn.fetchval("SELECT COUNT(*) FROM products")
        print(f"Total products in database: {total_products}")
        
        if total_products == 0:
            print("❌ No products found in database!")
            return
        
        # Quick Apple TV search
        print("\nSearching for 'apple tv'...")
        apple_tv_count = await conn.fetchval("""
            SELECT COUNT(*) 
            FROM products 
            WHERE LOWER(title) LIKE LOWER('%apple tv%')
        """)
        
        print(f"Products containing 'apple tv': {apple_tv_count}")
        
        if apple_tv_count > 0:
            # Show a few examples
            examples = await conn.fetch("""
                SELECT title 
                FROM products 
                WHERE LOWER(title) LIKE LOWER('%apple tv%')
                LIMIT 3
            """)
            print("Examples:")
            for example in examples:
                print(f"  - {example['title']}")
        else:
            print("❌ No Apple TV products found")
            
            # Check for just "apple"
            apple_count = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM products 
                WHERE LOWER(title) LIKE LOWER('%apple%')
            """)
            print(f"\nProducts containing 'apple': {apple_count}")
            
            # Check for just "tv"
            tv_count = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM products 
                WHERE LOWER(title) LIKE LOWER('%tv%')
            """)
            print(f"Products containing 'tv': {tv_count}")
        
        await conn.close()
        print("\n✓ Test completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(quick_apple_test()) 