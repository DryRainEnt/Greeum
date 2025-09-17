#!/usr/bin/env python3
"""
MCP 서버 테스트 스크립트
"""

import asyncio
import json
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

async def test_mcp_server():
    """MCP 서버 기능 테스트"""
    print("🧪 MCP 서버 테스트 시작")
    print("=" * 50)
    
    try:
        from greeum.mcp.native.server import GreeumNativeMCPServer
        
        # 서버 인스턴스 생성
        server = GreeumNativeMCPServer()
        
        # 초기화 테스트
        print("1. 서버 초기화 테스트...")
        success = await server.initialize()
        if success:
            print("   ✅ 서버 초기화 성공")
        else:
            print("   ❌ 서버 초기화 실패")
            return False
        
        # 도구 목록 테스트
        print("\n2. 도구 목록 테스트...")
        tools_result = await server.handle_tools_list({})
        tools = tools_result.get("tools", [])
        print(f"   📋 등록된 도구 수: {len(tools)}")
        for tool in tools:
            print(f"      - {tool['name']}: {tool['description']}")
        
        # 메모리 추가 테스트
        print("\n3. 메모리 추가 테스트...")
        add_result = await server.handle_tools_call({
            "name": "add_memory",
            "arguments": {
                "content": "테스트 메모리입니다",
                "importance": 0.8
            }
        })
        print(f"   결과: {add_result.get('content', [{}])[0].get('text', 'N/A')}")
        
        # 메모리 검색 테스트
        print("\n4. 메모리 검색 테스트...")
        search_result = await server.handle_tools_call({
            "name": "search_memory",
            "arguments": {
                "query": "테스트",
                "limit": 3
            }
        })
        print(f"   결과: {search_result.get('content', [{}])[0].get('text', 'N/A')}")
        
        # 통계 조회 테스트
        print("\n5. 통계 조회 테스트...")
        stats_result = await server.handle_tools_call({
            "name": "get_memory_stats",
            "arguments": {}
        })
        print(f"   결과: {stats_result.get('content', [{}])[0].get('text', 'N/A')}")
        
        print("\n" + "=" * 50)
        print("✅ 모든 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_mcp_server())
    sys.exit(0 if result else 1)
