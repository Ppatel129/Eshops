#!/usr/bin/env python3
"""
Simple test script to verify category filter functionality
"""

import requests
import json

def test_category_filter():
    """Test the category filter functionality using requests"""
    
    base_url = "http://localhost:8000"
    
    print("🚀 Testing Category Filter Functionality")
    print("=" * 50)
    
    try:
        # Test 1: Health check
        print("🔍 Testing server health...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return
        
        # Test 2: Search with category distribution
        print("\n🔍 Testing search with category distribution...")
        response = requests.get(f"{base_url}/search", params={
            'q': 'phone',
            'page': 1,
            'per_page': 10
        }, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
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
            print(f"❌ Search failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
        
        # Test 3: Test category distribution endpoint directly
        print("\n🔍 Testing category distribution endpoint...")
        response = requests.get(f"{base_url}/category-distribution", params={
            'title': 'phone',
            'limit': 5
        }, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Category distribution endpoint working: {data.get('total_categories', 0)} categories")
            for cat in data.get('categories', [])[:3]:
                name = cat.get('category_name_en', cat.get('category_name', 'Unknown'))
                count = cat.get('count', 0)
                print(f"   - {name}: {count} products")
        else:
            print(f"❌ Category distribution endpoint failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
        
        # Test 4: Test with multiple category filters
        print("\n🔍 Testing multiple category filters...")
        response = requests.get(f"{base_url}/search", params={
            'q': 'phone',
            'categories': ['Smartphones', 'Accessories'],
            'page': 1,
            'per_page': 5
        }, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Multiple category filter working: {data.get('total', 0)} products found")
        else:
            print(f"❌ Multiple category filter failed: {response.status_code}")
        
        print("\n✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on http://localhost:8000")
    except requests.exceptions.Timeout:
        print("❌ Request timed out. Server might be slow or overloaded.")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_category_filter() 