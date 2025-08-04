#!/usr/bin/env python3
"""
Test script to verify "All Categories" functionality
"""

import urllib.request
import urllib.parse
import json

def test_all_categories():
    """Test that clearing categories shows all products"""
    
    base_url = "http://localhost:8000"
    
    print("🚀 Testing 'All Categories' Functionality")
    print("=" * 50)
    
    try:
        # Test 1: Search with no category filter (should show all products)
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
        
        # Test 2: Search with a specific category filter
        print("\n🔍 Testing search with category filter...")
        params = urllib.parse.urlencode({
            'q': 'aaa',
            'categories': ['Accessories'],
            'page': 1,
            'per_page': 10
        })
        
        with urllib.request.urlopen(f"{base_url}/search?{params}", timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                total_with_filter = data.get('total', 0)
                print(f"✅ Search with 'Accessories' filter: {total_with_filter} products found")
            else:
                print(f"❌ Search failed: {response.status}")
                return
        
        # Test 3: Verify that filtered results are subset of all results
        if total_with_filter <= total_without_filter:
            print(f"✅ Category filter working correctly: {total_with_filter} ≤ {total_without_filter}")
        else:
            print(f"❌ Category filter issue: {total_with_filter} > {total_without_filter}")
        
        # Test 4: Test with empty categories (should be same as no filter)
        print("\n🔍 Testing search with empty categories (should show all products)...")
        params = urllib.parse.urlencode({
            'q': 'aaa',
            'categories': [''],
            'page': 1,
            'per_page': 10
        })
        
        with urllib.request.urlopen(f"{base_url}/search?{params}", timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                total_empty_categories = data.get('total', 0)
                print(f"✅ Search with empty categories: {total_empty_categories} products found")
                
                if total_empty_categories == total_without_filter:
                    print("✅ Empty categories correctly ignored - same as no filter")
                else:
                    print(f"❌ Empty categories not ignored: {total_empty_categories} vs {total_without_filter}")
            else:
                print(f"❌ Search failed: {response.status}")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_all_categories() 