#!/usr/bin/env python3
"""
Test script to verify the get_memory_stats fix for v2.4.0a4
This script tests if the memory stats now properly reference local directory database instead of global memory.
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add the Greeum path to the Python path
sys.path.insert(0, '/Users/dryrain/DevRoom/Greeum')

async def test_memory_stats_fix():
    """Test the memory stats fix"""
    print("🔍 Testing memory stats fix for v2.4.0a4")
    print("=" * 60)
    
    # Test 1: Import the fixed function
    try:
        from greeum.mcp.tools.enhanced_memory_tools import check_memory_freshness
        print("✅ Successfully imported check_memory_freshness")
    except ImportError as e:
        print(f"❌ Failed to import check_memory_freshness: {e}")
        return False
    
    # Test 2: Test BaseAdapter approach directly  
    try:
        from greeum.mcp.adapters.base_adapter import BaseAdapter
        print("✅ Successfully imported BaseAdapter")
        
        # Create concrete implementation like the MCP servers do
        class TestGreaumAdapter(BaseAdapter):
            async def run(self):
                pass
        
        adapter = TestGreaumAdapter()
        components = adapter.initialize_greeum_components()
        
        if components:
            print("✅ BaseAdapter components initialized successfully")
            print(f"   - Components: {list(components.keys())}")
            
            # Test get_memory_stats_tool
            stats_result = adapter.get_memory_stats_tool()
            print("✅ get_memory_stats_tool executed successfully")
            print(f"   - Stats preview: {stats_result[:100]}...")
        else:
            print("⚠️  BaseAdapter components initialization returned None")
            
    except Exception as e:
        print(f"❌ BaseAdapter test failed: {e}")
        return False
    
    # Test 3: Test the fixed check_memory_freshness function
    try:
        print("\n🧪 Testing fixed check_memory_freshness function...")
        result = await check_memory_freshness()
        result_data = json.loads(result)
        
        print("✅ check_memory_freshness executed successfully")
        print(f"   - Status: {result_data.get('status', 'Unknown')}")
        print(f"   - Message: {result_data.get('message', 'No message')}")
        
        if 'note' in result_data:
            print(f"   - Note: {result_data['note']}")
        
        if 'local_database_stats' in result_data:
            stats_preview = result_data['local_database_stats'][:200] + "..." if len(result_data['local_database_stats']) > 200 else result_data['local_database_stats']
            print(f"   - Local database stats: {stats_preview}")
            
        # Check if it's referencing LOCAL database 
        if 'local_database_stats' in result_data and 'LOCAL' in result_data.get('note', ''):
            print("✅ SUCCESS: Function is now properly referencing LOCAL directory database")
            return True
        else:
            print("⚠️  WARNING: May still be referencing global database")
            return False
            
    except Exception as e:
        print(f"❌ check_memory_freshness test failed: {e}")
        return False

if __name__ == "__main__":
    print(f"Testing at: {datetime.now()}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path includes: {'/Users/dryrain/DevRoom/Greeum' in sys.path}")
    print()
    
    success = asyncio.run(test_memory_stats_fix())
    
    if success:
        print("\n🎉 OVERALL RESULT: MEMORY STATS FIX SUCCESSFUL")
        print("   The get_memory_stats issue has been resolved!")
        print("   Memory statistics now reference local directory database instead of global memory.")
    else:
        print("\n❌ OVERALL RESULT: MEMORY STATS FIX INCOMPLETE")  
        print("   Additional work may be needed to fully resolve the issue.")