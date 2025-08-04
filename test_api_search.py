import asyncio
import aiohttp
import json

async def test_api_search():
    """Test the API search endpoint"""
    
    print("Testing API search endpoint...\n")
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Single word search
        print("1. Testing 'apple' search:")
        async with session.get(f"{base_url}/search?title=apple&page=1&per_page=5") as response:
            if response.status == 200:
                data = await response.json()
                print(f"   Status: {response.status}")
                print(f"   Total results: {data.get('total', 0)}")
                print(f"   Products found: {len(data.get('products', []))}")
                if data.get('products'):
                    print(f"   First product: {data['products'][0]['title'][:50]}...")
            else:
                print(f"   Error: {response.status}")
        
        print()
        
        # Test 2: Multi-word search
        print("2. Testing 'apple tv' search:")
        async with session.get(f"{base_url}/search?title=apple%20tv&page=1&per_page=5") as response:
            if response.status == 200:
                data = await response.json()
                print(f"   Status: {response.status}")
                print(f"   Total results: {data.get('total', 0)}")
                print(f"   Products found: {len(data.get('products', []))}")
                print(f"   Search type: {data.get('search_type', 'unknown')}")
                if data.get('products'):
                    print(f"   First product: {data['products'][0]['title'][:50]}...")
            else:
                print(f"   Error: {response.status}")
        
        print()
        
        # Test 3: URL encoded search
        print("3. Testing URL encoded 'apple tv' search:")
        async with session.get(f"{base_url}/search", params={
            "title": "apple tv",
            "page": 1,
            "per_page": 5
        }) as response:
            if response.status == 200:
                data = await response.json()
                print(f"   Status: {response.status}")
                print(f"   Total results: {data.get('total', 0)}")
                print(f"   Products found: {len(data.get('products', []))}")
                print(f"   Search type: {data.get('search_type', 'unknown')}")
            else:
                print(f"   Error: {response.status}")
        
        print()
        
        # Test 4: Check if the issue is with the search method
        print("4. Testing direct search endpoint:")
        async with session.get(f"{base_url}/search", params={
            "q": "apple tv",
            "page": 1,
            "per_page": 5
        }) as response:
            if response.status == 200:
                data = await response.json()
                print(f"   Status: {response.status}")
                print(f"   Total results: {data.get('total', 0)}")
                print(f"   Products found: {len(data.get('products', []))}")
            else:
                print(f"   Error: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_api_search()) 