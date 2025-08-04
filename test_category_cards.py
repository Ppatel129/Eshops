#!/usr/bin/env python3
"""
Test script to verify category cards with images
"""

import urllib.request
import urllib.parse
import json

def test_category_cards():
    """Test that category distribution includes representative images"""
    
    base_url = "http://localhost:8000"
    
    print("🚀 Testing Category Cards with Images")
    print("=" * 50)
    
    try:
        # Test category distribution endpoint
        print("🔍 Getting category distribution with images...")
        params = urllib.parse.urlencode({
            'title': 'aaa',
            'limit': 10
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
                    image = cat.get('representative_image', 'No image')
                    
                    print(f"   {i}. {name} ({name_en}) - {count} products")
                    if image and image != 'No image':
                        print(f"      📷 Image: {image[:50]}...")
                    else:
                        print(f"      📷 No representative image")
                
                # Check if images are included
                categories_with_images = [cat for cat in categories if cat.get('representative_image')]
                print(f"\n📊 Categories with images: {len(categories_with_images)}/{len(categories)}")
                
            else:
                print(f"❌ Failed to get categories: {response.status}")
                return
        
        print("\n✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_category_cards() 