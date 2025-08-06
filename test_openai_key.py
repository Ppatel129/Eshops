import asyncio
import openai
from config import settings

async def test_openai_key():
    """Test if OpenAI API key is working"""
    
    print("🔑 TESTING OPENAI API KEY")
    print("=" * 50)
    
    # Check if API key is set
    if not settings.OPENAI_API_KEY:
        print("❌ No OpenAI API key found in configuration")
        return
    
    print(f"✅ OpenAI API key found: {settings.OPENAI_API_KEY[:20]}...")
    
    try:
        # Initialize OpenAI client
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Test with a simple query
        test_query = "aple"
        print(f"\n🧪 Testing AI correction for: '{test_query}'")
        
        prompt = f"""
        Analyze this e-commerce search query and correct any spelling mistakes:
        Query: "{test_query}"
        
        IMPORTANT: Focus on correcting common typos and misspellings. For example:
        - "aple" should be corrected to "apple"
        - "samsun" should be corrected to "samsung"
        - "iphne" should be corrected to "iphone"
        
        Return a JSON object with:
        {{
            "corrected_query": "spelling corrected version (fix typos)",
            "original_query": "{test_query}",
            "intent": "product_search",
            "confidence": 0.95
        }}
        """
        
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ OpenAI API call successful!")
        print(f"📝 Raw response: {result}")
        
        # Try to parse JSON
        import json
        import re
        
        try:
            # Find JSON in the response
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                corrected = parsed.get('corrected_query', 'unknown')
                print(f"🎯 AI corrected '{test_query}' → '{corrected}'")
                
                if corrected.lower() == 'apple':
                    print("✅ SUCCESS: AI correctly identified the typo!")
                else:
                    print(f"⚠️  AI suggested '{corrected}' instead of 'apple'")
            else:
                print("⚠️  Could not find JSON in AI response")
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"📝 Response was: {result}")
            
    except Exception as e:
        print(f"❌ OpenAI API call failed: {e}")
        
        # Check for specific error types
        if "401" in str(e) or "authentication" in str(e).lower():
            print("🔑 Authentication failed - API key may be invalid")
        elif "quota" in str(e).lower() or "429" in str(e):
            print("💰 API quota exceeded - check your OpenAI account")
        elif "rate limit" in str(e).lower():
            print("⏱️  Rate limit exceeded - try again later")
        else:
            print("❓ Unknown error - check your internet connection and API key")

if __name__ == "__main__":
    asyncio.run(test_openai_key()) 