import asyncio
import aiohttp
import json

async def test_ai_processing():
    """Test AI processing functionality"""
    
    print("🤖 TESTING AI PROCESSING")
    print("=" * 50)
    
    # Test cases for AI processing
    test_cases = [
        "aple",      # Should be corrected to "apple"
        "samsun",    # Should be corrected to "samsung"
        "iphne",     # Should be corrected to "iphone"
        "smartphne", # Should be corrected to "smartphone"
        "laptp",     # Should be corrected to "laptop"
    ]
    
    async with aiohttp.ClientSession() as session:
        for query in test_cases:
            print(f"\n🧪 Testing AI processing for: '{query}'")
            
            try:
                # Test search with AI processing
                async with session.get(f"http://localhost:8000/search?title={query}&per_page=3") as response:
                    if response.status == 200:
                        data = await response.json()
                        products = data.get('products', [])
                        total = data.get('total', 0)
                        
                        print(f"   ✅ Search successful: {len(products)} products, {total} total")
                        
                        if products:
                            # Check if any product contains the expected corrected term
                            expected_corrections = {
                                'aple': 'apple',
                                'samsun': 'samsung',
                                'iphne': 'iphone',
                                'smartphne': 'smartphone',
                                'laptp': 'laptop',
                            }
                            
                            expected = expected_corrections.get(query, query)
                            found_expected = False
                            
                            for product in products:
                                title = product.get('title', '').lower()
                                if expected.lower() in title:
                                    found_expected = True
                                    print(f"   🎯 Found '{expected}' in: {product.get('title', '')[:60]}...")
                                    break
                            
                            if found_expected:
                                print(f"   ✅ SUCCESS: AI corrected '{query}' → '{expected}'")
                            else:
                                print(f"   ⚠️  Found products but not the expected '{expected}'")
                                print(f"   📝 First product: {products[0].get('title', '')[:60]}...")
                        else:
                            print(f"   ❌ No products found for '{query}'")
                    else:
                        print(f"   ❌ Search failed: HTTP {response.status}")
                        
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    print(f"\n" + "=" * 50)
    print("📊 AI PROCESSING SUMMARY:")
    print("   🤖 AI processing should correct typos automatically")
    print("   ✅ Uses OpenAI API for intelligent query correction")
    print("   🔄 Falls back to common corrections if AI fails")
    print("   🎯 Should find relevant products even with typos")

if __name__ == "__main__":
    asyncio.run(test_ai_processing()) 