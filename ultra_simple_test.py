#!/usr/bin/env python3
"""
Ultra-simple test script to verify category filter functionality
Uses only built-in Python libraries
"""

import urllib.request
import urllib.parse
import json

def test_category_filter():
    """Test the category filter functionality using urllib"""
    
    base_url = "http://localhost:8000"
    
    print("🚀 Testing Category Filter Functionality")
    print("=" * 50)
    
    try:
        # Test 1: Health check
        print("🔍 Testing server health...")
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=5) as response:
                if response.status == 200:
                    print("✅ Server is running")
                else:
                    print(f"❌ Server health check failed: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Could not connect to server: {e}")
            return
        
        # Test 2: Search with category distribution
        print("\n🔍 Testing search with category distribution...")
        params = urllib.parse.urlencode({
            'q': 'phone',
            'page': 1,
            'per_page': 10
        })
        
        try:
            with urllib.request.urlopen(f"{base_url}/search?{params}", timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    print(f"✅ Search successful: {data.get('total', 0)} products found")
                    
                    if 'category_distribution' in data:
                        categories = data['category_distribution']
                        print(f"✅ Category distribution found: {len(categories)} categories")
                        for cat in categories[:5]:  # Show first 5
                            name = cat.get('category_name_en', cat.get('category_name', 'Unknown'))
                            count = cat.get('count', 0)
                            print(f"   - {name}: {count} products")
                    else:
                        print("⚠️  No category distribution in response")
                else:
                    print(f"❌ Search failed: {response.status}")
        except Exception as e:
            print(f"❌ Search test failed: {e}")
        
        # Test 3: Test category distribution endpoint directly
        print("\n🔍 Testing category distribution endpoint...")
        params = urllib.parse.urlencode({
            'title': 'phone',
            'limit': 5
        })
        
        try:
            with urllib.request.urlopen(f"{base_url}/category-distribution?{params}", timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    print(f"✅ Category distribution endpoint working: {data.get('total_categories', 0)} categories")
                    for cat in data.get('categories', [])[:3]:
                        name = cat.get('category_name_en', cat.get('category_name', 'Unknown'))
                        count = cat.get('count', 0)
                        print(f"   - {name}: {count} products")
                else:
                    print(f"❌ Category distribution endpoint failed: {response.status}")
        except Exception as e:
            print(f"❌ Category distribution test failed: {e}")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_category_filter() 