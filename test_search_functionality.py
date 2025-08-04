import asyncio
import asyncpg
from config import settings

async def test_search_functionality():
    """Test the search functionality for Apple TV"""
    
    print("Testing search functionality for 'apple tv'...\n")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(settings.DATABASE_URL)
        
        # Test 1: Direct database query (what we know works)
        print("1. Direct database query (LIKE '%apple tv%'):")
        direct_results = await conn.fetch("""
            SELECT title 
            FROM products 
            WHERE LOWER(title) LIKE LOWER('%apple tv%')
            LIMIT 3
        """)
        
        for result in direct_results:
            print(f"   ✓ {result['title']}")
        
        print()
        
        # Test 2: Test the process_search_query method logic
        print("2. Testing query processing logic:")
        query = "apple tv"
        
        # Simulate the process_search_query method
        words = query.lower().split()
        terms = [word.strip() for word in words if len(word.strip()) >= 2]
        
        # Add the original query as a term for exact matches
        if query.strip():
            terms.insert(0, query.strip())
        
        print(f"   Original query: '{query}'")
        print(f"   Processed terms: {terms}")
        
        # Test 3: Test each term individually
        print("\n3. Testing each search term:")
        for term in terms:
            count = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM products 
                WHERE LOWER(title) LIKE LOWER($1)
            """, f"%{term}%")
            print(f"   Term '{term}': {count} products")
        
        print()
        
        # Test 4: Test the exact search conditions used in the app
        print("4. Testing exact search conditions (ILIKE):")
        
        # Test the conditions used in search_products method
        conditions = [
            ("Product.title.ilike", f"%{query}%"),
            ("Product.description.ilike", f"%{query}%"),
            ("Product.ean.ilike", f"%{query}%"),
            ("Product.mpn.ilike", f"%{query}%")
        ]
        
        for condition_name, pattern in conditions:
            count = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM products 
                WHERE LOWER(title) ILIKE LOWER($1)
            """, pattern)
            print(f"   {condition_name} '{pattern}': {count} products")
        
        print()
        
        # Test 5: Check if there are any encoding issues
        print("5. Checking for encoding issues:")
        sample_product = await conn.fetchrow("""
            SELECT title, LENGTH(title) as title_length
            FROM products 
            WHERE LOWER(title) LIKE LOWER('%apple tv%')
            LIMIT 1
        """)
        
        if sample_product:
            print(f"   Sample title: '{sample_product['title']}'")
            print(f"   Title length: {sample_product['title_length']}")
            print(f"   Title bytes: {sample_product['title'].encode('utf-8')}")
        
        await conn.close()
        print("\n✓ Search functionality test completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_search_functionality()) 