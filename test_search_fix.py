#!/usr/bin/env python3
"""
Test the fixed search functionality
"""

import asyncio
import json
from datetime import datetime

async def test_search_fix():
    print(f"🧪 Testing fixed search functionality at {datetime.now()}")
    print("=" * 60)
    
    try:
        # Test the fixed search function
        from greeum.mcp.tools.enhanced_memory_tools import search_memory_contextual
        
        print("🔍 1. Testing search with 'memory' query...")
        result = await search_memory_contextual("memory", limit=5)
        result_data = json.loads(result)
        
        print(f"   Status: {result_data.get('status', 'Unknown')}")
        print(f"   Message: {result_data.get('message', 'No message')}")
        
        if 'memories' in result_data:
            memories = result_data['memories']
            print(f"   Found memories: {len(memories)}")
            for i, mem in enumerate(memories[:3]):  # Show first 3
                content_preview = mem['content'][:50] + "..." if len(mem['content']) > 50 else mem['content']
                print(f"     {i+1}. #{mem['memory_id']}: {content_preview}")
        
        if 'note' in result_data:
            print(f"   Note: {result_data['note']}")
        
        print()
        print("🔍 2. Testing search with 'deploy' query...")
        result2 = await search_memory_contextual("deploy", limit=3)
        result2_data = json.loads(result2)
        
        print(f"   Status: {result2_data.get('status', 'Unknown')}")
        if 'memories' in result2_data:
            print(f"   Found memories: {len(result2_data['memories'])}")
        
        print()
        print("🔍 3. Testing search with uncommon query...")
        result3 = await search_memory_contextual("xyz123nonexistent", limit=3)
        result3_data = json.loads(result3)
        
        print(f"   Status for uncommon query: {result3_data.get('status', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_search_fix())
    print()
    if success:
        print("✅ Search functionality test completed!")
    else:
        print("❌ Search functionality test failed!")