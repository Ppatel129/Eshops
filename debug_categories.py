#!/usr/bin/env python3
"""
Debug script to see what categories are available
"""

import urllib.request
import urllib.parse
import json

def debug_categories():
    """Debug what categories are available"""
    
    base_url = "http://localhost:8000"
    
    print("🔍 Debugging Available Categories")
    print("=" * 50)
    
    try:
        # Test 1: Get category distribution for a simple search
        print("🔍 Getting category distribution for 'aaa'...")
        params = urllib.parse.urlencode({
            'title': 'aaa',
            'limit': 20
        })
        
        with urllib.request.urlopen(f"{base_url}/category-distribution?{params}", timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                categories = data.get('categories', [])
                print(f"✅ Found {len(categories)} categories:")
                for i, cat in enumerate(categories, 1):
                    name = cat.get('category_name', 'Unknown')
                    name_en = cat.get('category_name_en', 'No translation')
                    count = cat.get('count', 0)
                    print(f"   {i}. {name} ({name_en}) - {count} products")
            else:
                print(f"❌ Failed to get categories: {response.status}")
                return
        
        # Test 2: Try searching with the first available category
        if categories:
            first_category = categories[0]['category_name']
            print(f"\n🔍 Testing search with first category: '{first_category}'...")
            
            params = urllib.parse.urlencode({
                'q': 'aaa',
                'categories': [first_category],
                'page': 1,
                'per_page': 10
            })
            
            with urllib.request.urlopen(f"{base_url}/search?{params}", timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    total = data.get('total', 0)
                    print(f"✅ Search with '{first_category}': {total} products found")
                else:
                    print(f"❌ Search failed: {response.status}")
        
        print("\n✅ Debug completed!")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    debug_categories() 