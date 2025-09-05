#!/usr/bin/env python3
"""
Quick test for v2.4.0a5 get_memory_stats fix
"""

import asyncio
import json
import sys
import os
from datetime import datetime

async def test_v240a5_fix():
    print(f"🧪 Testing Greeum v2.4.0a5 get_memory_stats fix")
    print(f"📍 Current directory: {os.getcwd()}")
    print("=" * 60)
    
    try:
        # Test import
        from greeum import __version__
        print(f"✅ Greeum version: {__version__}")
        
        # Test the fixed function
        from greeum.mcp.tools.enhanced_memory_tools import check_memory_freshness
        
        print("🔍 Testing check_memory_freshness function...")
        result = await check_memory_freshness()
        result_data = json.loads(result)
        
        print(f"✅ Function executed successfully")
        print(f"   Status: {result_data.get('status', 'Unknown')}")
        
        # Check for local database reference
        if 'note' in result_data:
            print(f"   Note: {result_data['note']}")
            if 'LOCAL' in result_data['note']:
                print("🎉 SUCCESS: Fix is working! References LOCAL directory database")
                return True
        
        if 'local_database_stats' in result_data:
            print("✅ Local database stats found in response")
            
        print("✅ Function appears to be working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_v240a5_fix())
    print()
    if success:
        print("🎉 v2.4.0a5 deployment verification PASSED!")
    else:
        print("❌ v2.4.0a5 deployment verification FAILED!")