import asyncio
import aiohttp
import time

async def test_suggestions_performance():
    """Test suggestions performance"""
    
    print("⚡ SUGGESTIONS PERFORMANCE TEST")
    print("=" * 50)
    
    test_queries = [
        "aple",      # Should show "apple" correction
        "samsun",    # Should show "samsung" correction
        "apple",     # Direct search
        "samsung",   # Direct search
        "iph",       # Partial search
        "lap",       # Partial search
    ]
    
    async with aiohttp.ClientSession() as session:
        for query in test_queries:
            print(f"\n🧪 Testing suggestions for: '{query}'")
            
            start_time = time.time()
            
            try:
                async with session.get(f"http://localhost:8000/suggestions?q={query}&limit=5") as response:
                    end_time = time.time()
                    response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                    
                    if response.status == 200:
                        suggestions = await response.json()
                        
                        print(f"   ⚡ Response time: {response_time:.1f}ms")
                        print(f"   📊 Found: {len(suggestions)} suggestions")
                        
                        if suggestions:
                            print(f"   📝 Suggestions: {suggestions[:3]}...")
                        
                        # Performance rating
                        if response_time < 100:
                            print(f"   ✅ EXCELLENT (< 100ms)")
                        elif response_time < 500:
                            print(f"   ✅ GOOD (100-500ms)")
                        elif response_time < 1000:
                            print(f"   ⚠️  MODERATE (500-1000ms)")
                        else:
                            print(f"   ❌ SLOW (> 1000ms)")
                            
                    else:
                        print(f"   ❌ Failed: HTTP {response.status}")
                        
            except Exception as e:
                end_time = time.time()
                response_time = (end_time - start_time) * 1000
                print(f"   ❌ Error: {e} ({response_time:.1f}ms)")
    
    print(f"\n" + "=" * 50)
    print("📊 SUGGESTIONS OPTIMIZATION SUMMARY:")
    print("   🚀 Optimizations applied:")
    print("   - Removed AI processing")
    print("   - Removed fuzzy search")
    print("   - Single optimized database query")
    print("   - Fast common corrections")
    print("   - Direct database lookup")
    print("   ")
    print("   💡 Expected improvements:")
    print("   - 80-95% faster response times")
    print("   - Instant suggestions display")
    print("   - Better user experience")

if __name__ == "__main__":
    asyncio.run(test_suggestions_performance()) 