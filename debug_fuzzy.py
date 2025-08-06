import asyncio
import asyncpg
from config import settings
from fuzzywuzzy import fuzz, process

async def debug_fuzzy_search():
    """Debug fuzzy search functionality"""
    
    print("🔍 DEBUGGING FUZZY SEARCH")
    print("=" * 50)
    
    # Connect to database
    conn = await asyncpg.connect(settings.DATABASE_URL)
    
    # Get some sample data
    titles = await conn.fetch("SELECT DISTINCT title FROM products WHERE title ILIKE '%apple%' LIMIT 10")
    brands = await conn.fetch("SELECT DISTINCT name FROM brands WHERE name ILIKE '%apple%' LIMIT 10")
    
    print(f"Found {len(titles)} Apple products and {len(brands)} Apple brands")
    
    # Test fuzzy search for "aple"
    query = "aple"
    all_terms = []
    
    # Add titles
    for row in titles:
        all_terms.append(row['title'])
    
    # Add brands
    for row in brands:
        all_terms.append(row['name'])
    
    # Add some common terms
    all_terms.extend(['apple', 'Apple', 'APPLE', 'staples', 'Staples', 'STAPLES'])
    
    print(f"\nTesting fuzzy search for '{query}' against {len(all_terms)} terms")
    
    # Test different fuzzy matching methods
    methods = [
        ('partial_ratio', fuzz.partial_ratio),
        ('token_sort_ratio', fuzz.token_sort_ratio),
        ('simple_ratio', fuzz.ratio),
        ('token_set_ratio', fuzz.token_set_ratio)
    ]
    
    for method_name, method_func in methods:
        print(f"\n📊 {method_name.upper()}:")
        matches = process.extract(query, all_terms, limit=5, scorer=method_func)
        
        for term, score in matches:
            print(f"   '{term}' -> {score}%")
    
    # Test common corrections
    common_corrections = {
        'aple': 'apple',
        'aplle': 'apple',
        'appel': 'apple',
    }
    
    print(f"\n🔧 COMMON CORRECTIONS:")
    for typo, correction in common_corrections.items():
        if typo in common_corrections:
            print(f"   '{typo}' -> '{correction}'")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(debug_fuzzy_search()) 