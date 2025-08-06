import asyncio
import asyncpg
from config import settings

async def debug_search():
    """Debug search logic directly"""
    
    print("🔍 DEBUGGING SEARCH LOGIC")
    print("=" * 50)
    
    # Connect to database
    conn = await asyncpg.connect(settings.DATABASE_URL)
    
    # Test the correction logic
    original_query = "aple"
    common_corrections = {
        'aple': 'apple',
        'aplle': 'apple',
        'appel': 'apple',
        'samsun': 'samsung',
        'samsng': 'samsung',
        'iphne': 'iphone',
        'iphon': 'iphone',
        'smartphne': 'smartphone',
        'smartphn': 'smartphone',
        'laptp': 'laptop',
        'lapto': 'laptop',
        'headphnes': 'headphones',
        'headphne': 'headphone',
    }
    
    # Apply correction
    corrected_query = original_query
    if original_query.lower().strip() in common_corrections:
        corrected_query = common_corrections[original_query.lower().strip()]
        print(f"✅ Applied correction: '{original_query}' -> '{corrected_query}'")
    else:
        print(f"❌ No correction found for '{original_query}'")
    
    # Test search with original query
    print(f"\n🔍 Testing search with original query: '{original_query}'")
    result1 = await conn.fetch("SELECT title FROM products WHERE title ILIKE $1 LIMIT 3", f"%{original_query}%")
    print(f"Found {len(result1)} products with '{original_query}':")
    for row in result1:
        print(f"  - {row['title']}")
    
    # Test search with corrected query
    print(f"\n🔍 Testing search with corrected query: '{corrected_query}'")
    result2 = await conn.fetch("SELECT title FROM products WHERE title ILIKE $1 LIMIT 3", f"%{corrected_query}%")
    print(f"Found {len(result2)} products with '{corrected_query}':")
    for row in result2:
        print(f"  - {row['title']}")
    
    # Test search excluding original query
    print(f"\n🔍 Testing search with '{corrected_query}' but excluding '{original_query}':")
    result3 = await conn.fetch(
        "SELECT title FROM products WHERE title ILIKE $1 AND title NOT ILIKE $2 LIMIT 3", 
        f"%{corrected_query}%", f"%{original_query}%"
    )
    print(f"Found {len(result3)} products with '{corrected_query}' but not '{original_query}':")
    for row in result3:
        print(f"  - {row['title']}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(debug_search()) 