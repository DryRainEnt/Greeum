#!/usr/bin/env python3
"""
Detailed debug of search functionality
"""

import asyncio
import json
from datetime import datetime

async def debug_search_detailed():
    print(f"🔍 상세 검색 기능 디버깅 at {datetime.now()}")
    print("=" * 60)
    
    try:
        # 1. 컴포넌트 초기화 직접 테스트
        from greeum.mcp.adapters.base_adapter import BaseAdapter
        
        class DebugSearchAdapter(BaseAdapter):
            async def run(self):
                pass
        
        adapter = DebugSearchAdapter()
        components = adapter.initialize_greeum_components()
        
        print("📊 1. 컴포넌트 초기화 결과:")
        if components:
            for key, comp in components.items():
                print(f"   - {key}: {type(comp)}")
        else:
            print("   ❌ 컴포넌트 초기화 실패")
            return False
        
        # 2. 검색 엔진 직접 테스트
        search_engine = components.get('search_engine')
        block_manager = components.get('block_manager')
        
        print("\n🔍 2. 검색 엔진 직접 테스트:")
        if search_engine:
            print(f"   Search engine type: {type(search_engine)}")
            print("   Available methods:")
            methods = [method for method in dir(search_engine) if not method.startswith('_')]
            for method in methods[:10]:  # Show first 10 methods
                print(f"     - {method}")
            
            # 검색 엔진으로 직접 검색 테스트
            try:
                if hasattr(search_engine, 'search_by_embedding'):
                    print("   Testing search_by_embedding...")
                    search_results = search_engine.search_by_embedding("memory", limit=3)
                    print(f"     Results: {len(search_results) if search_results else 0}")
                    if search_results:
                        for i, result in enumerate(search_results[:2]):
                            print(f"       {i+1}. Block #{result.get('block_index', '?')}: score={result.get('similarity_score', '?')}")
                elif hasattr(search_engine, 'search_by_keywords'):
                    print("   Testing search_by_keywords...")
                    search_results = search_engine.search_by_keywords(["memory"], limit=3)
                    print(f"     Results: {len(search_results) if search_results else 0}")
                else:
                    print("   ❌ No suitable search method found")
                    
            except Exception as e:
                print(f"   ❌ Search engine test failed: {e}")
        
        # 3. 블록 매니저 직접 테스트
        print("\n📦 3. 블록 매니저 직접 테스트:")
        if block_manager:
            print(f"   Block manager type: {type(block_manager)}")
            
            try:
                # 키워드 검색 테스트
                if hasattr(block_manager, 'search_by_keywords'):
                    print("   Testing block_manager.search_by_keywords...")
                    search_results = block_manager.search_by_keywords(["memory"], limit=3)
                    print(f"     Results: {len(search_results) if search_results else 0}")
                    if search_results:
                        for i, result in enumerate(search_results[:2]):
                            content_preview = result.get('context', '')[:50] + "..." if len(result.get('context', '')) > 50 else result.get('context', '')
                            print(f"       {i+1}. Block #{result.get('block_index', '?')}: {content_preview}")
                elif hasattr(block_manager, 'get_recent_blocks'):
                    print("   Testing block_manager.get_recent_blocks...")
                    recent_blocks = block_manager.get_recent_blocks(limit=3)
                    print(f"     Recent blocks: {len(recent_blocks) if recent_blocks else 0}")
                else:
                    print("   ❌ No suitable block manager search method found")
                    
            except Exception as e:
                print(f"   ❌ Block manager test failed: {e}")
        
        # 4. 수정된 검색 함수 테스트
        print("\n🧪 4. 수정된 search_memory_contextual 테스트:")
        from greeum.mcp.tools.enhanced_memory_tools import search_memory_contextual
        
        result = await search_memory_contextual("memory", limit=3)
        print(f"   Raw result length: {len(result)}")
        print(f"   First 200 chars: {result[:200]}...")
        
        try:
            result_data = json.loads(result)
            print(f"   Parsed status: {result_data.get('status', 'Unknown')}")
            print(f"   Parsed message: {result_data.get('message', 'No message')}")
            if 'memories' in result_data:
                print(f"   Found memories: {len(result_data['memories'])}")
            if 'error' in result_data:
                print(f"   Error: {result_data['error']}")
        except json.JSONDecodeError as e:
            print(f"   JSON decode error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_search_detailed())
    print()
    if success:
        print("✅ Detailed search debug completed!")
    else:
        print("❌ Detailed search debug failed!")