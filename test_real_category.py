#!/usr/bin/env python3
"""
Test with real category names from the database
"""

import urllib.request
import urllib.parse
import json

def test_real_category():
    """Test with real category names"""
    
    base_url = "http://localhost:8000"
    
    print("🚀 Testing with Real Category Names")
    print("=" * 50)
    
    try:
        # Test 1: Search with no category filter
        print("🔍 Testing search with no category filter...")
        params = urllib.parse.urlencode({
            'q': 'aaa',
            'page': 1,
            'per_page': 10
        })
        
        with urllib.request.urlopen(f"{base_url}/search?{params}", timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                total_without_filter = data.get('total', 0)
                print(f"✅ Search without category filter: {total_without_filter} products found")
            else:
                print(f"❌ Search failed: {response.status}")
                return
        
        # Test 2: Search with real category 'Μπαταρίες' (Batteries)
        print("\n🔍 Testing search with real category 'Μπαταρίες'...")
        params = urllib.parse.urlencode({
            'q': 'aaa',
            'categories': ['Μπαταρίες'],
            'page': 1,
            'per_page': 10
        })
        
        with urllib.request.urlopen(f"{base_url}/search?{params}", timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                total_with_batteries = data.get('total', 0)
                print(f"✅ Search with 'Μπαταρίες': {total_with_batteries} products found")
            else:
                print(f"❌ Search failed: {response.status}")
                return
        
        # Test 3: Search with another real category 'Φακοί' (Lenses)
        print("\n🔍 Testing search with real category 'Φακοί'...")
        params = urllib.parse.urlencode({
            'q': 'aaa',
            'categories': ['Φακοί'],
            'page': 1,
            'per_page': 10
        })
        
        with urllib.request.urlopen(f"{base_url}/search?{params}", timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                total_with_lenses = data.get('total', 0)
                print(f"✅ Search with 'Φακοί': {total_with_lenses} products found")
            else:
                print(f"❌ Search failed: {response.status}")
                return
        
        # Test 4: Test with completely empty categories (should show all)
        print("\n🔍 Testing search with completely empty categories...")
        params = urllib.parse.urlencode({
            'q': 'aaa',
            'page': 1,
            'per_page': 10
        })
        
        with urllib.request.urlopen(f"{base_url}/search?{params}", timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                total_no_categories = data.get('total', 0)
                print(f"✅ Search with no categories parameter: {total_no_categories} products found")
                
                if total_no_categories == total_without_filter:
                    print("✅ No categories parameter works correctly")
                else:
                    print(f"❌ No categories parameter issue: {total_no_categories} vs {total_without_filter}")
            else:
                print(f"❌ Search failed: {response.status}")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_real_category() 