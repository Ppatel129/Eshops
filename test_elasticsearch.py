#!/usr/bin/env python3
"""
Simple script to test Elasticsearch connection and functionality
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_elasticsearch():
    """Test Elasticsearch connection and basic functionality"""
    
    print("🔍 Testing Elasticsearch Configuration...")
    print("=" * 50)
    
    try:
        # Import after path setup
        from elasticsearch_service import elasticsearch_service
        from config import settings
        
        print(f"📋 Configuration:")
        print(f"   ELASTICSEARCH_ENABLED: {settings.ELASTICSEARCH_ENABLED}")
        print(f"   ELASTICSEARCH_HOST: {settings.ELASTICSEARCH_HOST}")
        print(f"   ELASTICSEARCH_PORT: {settings.ELASTICSEARCH_PORT}")
        print()
        
        if not settings.ELASTICSEARCH_ENABLED:
            print("❌ Elasticsearch is disabled in configuration")
            print("   To enable, set ELASTICSEARCH_ENABLED=true in .env file")
            return False
        
        print("🔌 Testing connection...")
        connection_result = await elasticsearch_service.connect()
        
        if connection_result:
            print("✅ Elasticsearch connection successful!")
            
            # Test index creation
            print("📝 Testing index creation...")
            index_result = await elasticsearch_service.create_index()
            
            if index_result:
                print("✅ Index creation successful!")
                print("🎉 Elasticsearch is fully functional!")
                return True
            else:
                print("❌ Index creation failed")
                return False
        else:
            print("❌ Elasticsearch connection failed")
            print("   Make sure Elasticsearch is running on localhost:9200")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're in the virtual environment and dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

async def test_search_fallback():
    """Test that search works even without Elasticsearch"""
    
    print("\n🔄 Testing Search Fallback...")
    print("=" * 50)
    
    try:
        from search_service import SearchService
        from schemas import SearchFilters
        
        search_service = SearchService()
        
        # Test basic search
        filters = SearchFilters()
        result = await search_service.search("test", filters, 1, 10)
        
        if result:
            print("✅ Search fallback working (PostgreSQL)")
            print(f"   Found {result.get('total', 0)} results")
            return True
        else:
            print("❌ Search fallback failed")
            return False
            
    except Exception as e:
        print(f"❌ Search test error: {e}")
        return False

async def main():
    """Main test function"""
    
    print("🚀 Elasticsearch Test Suite")
    print("=" * 50)
    
    # Test Elasticsearch
    es_working = await test_elasticsearch()
    
    # Test search fallback
    search_working = await test_search_fallback()
    
    print("\n📊 Test Results:")
    print("=" * 50)
    print(f"Elasticsearch: {'✅ Working' if es_working else '❌ Not Working'}")
    print(f"Search Fallback: {'✅ Working' if search_working else '❌ Not Working'}")
    
    if es_working:
        print("\n🎉 Everything is working perfectly!")
    elif search_working:
        print("\n⚠️  Elasticsearch is not available, but search fallback is working")
        print("   The application will use PostgreSQL search instead")
    else:
        print("\n❌ Both Elasticsearch and search fallback are not working")
        print("   Please check your configuration and database connection")

if __name__ == "__main__":
    asyncio.run(main()) 