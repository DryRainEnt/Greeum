#!/usr/bin/env python3
"""
Debug memory stats vs search functionality discrepancy
"""

import asyncio
import json
import os
from datetime import datetime

async def debug_memory_discrepancy():
    print("🔍 디버깅: 검색은 되는데 통계는 0개인 문제")
    print("=" * 60)
    
    try:
        # 1. 먼저 실제 메모리 상태 확인
        from greeum import BlockManager, DatabaseManager
        
        print("📊 1. 직접 데이터베이스 조회")
        db_manager = DatabaseManager('./data/memory.db')
        
        # 직접 SQL로 메모리 개수 확인
        if hasattr(db_manager, 'conn'):
            cursor = db_manager.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM blocks")
            direct_count = cursor.fetchone()[0]
            print(f"   직접 SQL 조회 결과: {direct_count}개 메모리")
            
            # 최근 몇개 메모리 확인
            cursor.execute("SELECT block_index, timestamp, context FROM blocks ORDER BY timestamp DESC LIMIT 5")
            recent_memories = cursor.fetchall()
            print(f"   최근 메모리 {len(recent_memories)}개:")
            for idx, (block_idx, ts, context) in enumerate(recent_memories):
                preview = context[:50] + "..." if len(context) > 50 else context
                print(f"     {idx+1}. #{block_idx} ({ts}): {preview}")
        
        print()
        print("🔍 2. 검색 기능 테스트")
        from greeum.mcp.tools.enhanced_memory_tools import search_memory_contextual
        
        search_result = await search_memory_contextual("memory", limit=5)
        search_data = json.loads(search_result)
        print(f"   검색 결과: {len(search_data.get('memories', []))}개 발견")
        
        print()
        print("📈 3. get_memory_stats 상세 분석")
        
        # BaseAdapter를 통한 통계 확인
        from greeum.mcp.adapters.base_adapter import BaseAdapter
        class DebugAdapter(BaseAdapter):
            async def run(self):
                pass
        
        adapter = DebugAdapter()
        components = adapter.initialize_greeum_components()
        
        if components:
            print("   ✅ BaseAdapter 컴포넌트 초기화 성공")
            
            # _get_detailed_memory_stats 메서드 직접 호출
            db_mgr = components['db_manager']
            detailed_stats = adapter._get_detailed_memory_stats(db_mgr)
            
            print(f"   상세 통계:")
            for key, value in detailed_stats.items():
                print(f"     - {key}: {value}")
            
            # get_memory_stats_tool 결과
            stats_result = adapter.get_memory_stats_tool()
            print(f"   get_memory_stats_tool 결과 (처음 200자):")
            print(f"     {stats_result[:200]}...")
        
        print()
        print("🧪 4. check_memory_freshness 상세 분석")
        from greeum.mcp.tools.enhanced_memory_tools import check_memory_freshness
        
        freshness_result = await check_memory_freshness()
        freshness_data = json.loads(freshness_result)
        
        print(f"   check_memory_freshness 결과:")
        if 'frequency_analysis' in freshness_data:
            freq_data = freshness_data['frequency_analysis']
            for key, value in freq_data.items():
                print(f"     - {key}: {value}")
        
        print()
        print("💡 5. usage_analytics 테스트")
        
        # usage_analytics도 테스트
        try:
            from greeum.mcp.tools.enhanced_memory_tools import MCP_TOOLS_WITH_ENCOURAGEMENT
            # usage_analytics 함수가 있는지 찾아보기
            print("   MCP 도구 목록:")
            for tool in MCP_TOOLS_WITH_ENCOURAGEMENT:
                print(f"     - {tool['name']}: {tool['description'][:50]}...")
        except Exception as e:
            print(f"   usage_analytics 접근 실패: {e}")
        
        # 컴포넌트에서 usage_analytics 직접 접근
        if 'usage_analytics' in components:
            usage_analytics = components['usage_analytics']
            print(f"   usage_analytics 컴포넌트 타입: {type(usage_analytics)}")
            
            # 기본 통계 메서드들 확인
            if hasattr(usage_analytics, 'get_memory_usage_stats'):
                usage_stats = usage_analytics.get_memory_usage_stats(days=7)
                print(f"   사용량 통계: {usage_stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ 디버깅 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'db_manager' in locals() and hasattr(db_manager, 'close'):
            db_manager.close()

if __name__ == "__main__":
    success = asyncio.run(debug_memory_discrepancy())
    print()
    if success:
        print("✅ 디버깅 완료 - 위 정보로 문제점을 파악할 수 있습니다")
    else:
        print("❌ 디버깅 중 오류 발생")