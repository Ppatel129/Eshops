#!/usr/bin/env python3
"""
Test script to verify category filter functionality
"""

import asyncio
import aiohttp
import json

async def test_category_filter():
    """Test the category filter functionality"""
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Search with category distribution
        print("🔍 Testing search with category distribution...")
        async with session.get('http://localhost:8000/search', params={
            'q': 'phone',
            'page': 1,
            'per_page': 10
        }) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Search successful: {data.get('total', 0)} products found")
                
                if 'category_distribution' in data:
                    categories = data['category_distribution']
                    print(f"✅ Category distribution found: {len(categories)} categories")
                    for cat in categories[:5]:  # Show first 5
                        print(f"   - {cat.get('category_name_en', cat.get('category_name'))}: {cat.get('count')} products")
                else:
                    print("⚠️  No category distribution in response")
            else:
                print(f"❌ Search failed: {response.status}")
        
        # Test 2: Test category distribution endpoint directly
        print("\n🔍 Testing category distribution endpoint...")
        async with session.get('http://localhost:8000/category-distribution', params={
            'title': 'phone',
            'limit': 5
        }) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Category distribution endpoint working: {data.get('total_categories', 0)} categories")
                for cat in data.get('categories', [])[:3]:
                    print(f"   - {cat.get('category_name_en', cat.get('category_name'))}: {cat.get('count')} products")
            else:
                print(f"❌ Category distribution endpoint failed: {response.status}")
        
        # Test 3: Test with multiple category filters
        print("\n🔍 Testing multiple category filters...")
        async with session.get('http://localhost:8000/search', params={
            'q': 'phone',
            'categories': ['Smartphones', 'Accessories'],
            'page': 1,
            'per_page': 5
        }) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Multiple category filter working: {data.get('total', 0)} products found")
            else:
                print(f"❌ Multiple category filter failed: {response.status}")

if __name__ == "__main__":
    print("🚀 Testing Category Filter Functionality")
    print("=" * 50)
    
    try:
        asyncio.run(test_category_filter())
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Make sure the server is running on http://localhost:8000") 