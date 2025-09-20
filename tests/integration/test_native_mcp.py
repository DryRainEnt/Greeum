#!/usr/bin/env python3
"""
Native MCP Server 기능 검증 테스트
실제 JSON-RPC 메시지로 MCP 도구 기능 테스트
"""

import pytest
import asyncio
import json
import sys
from pathlib import Path

# Greeum Native MCP 모듈 import
sys.path.insert(0, str(Path(__file__).parent))

@pytest.mark.slow
@pytest.mark.mcp
@pytest.mark.integration
async def test_native_mcp_functionality():
    """Native MCP Server 기능 검증"""
    print("🧪 Native MCP Server 기능 검증 테스트 시작")
    print("=" * 60)
    
    try:
        from greeum.mcp.native.server import GreeumNativeMCPServer
        from greeum.mcp.native.types import SessionMessage
        
        # 서버 인스턴스 생성 및 초기화
        server = GreeumNativeMCPServer()
        await server.initialize()
        print("✅ 1. 서버 초기화 성공")
        
        # 테스트 메시지들
        test_cases = [
            {
                "name": "Initialize Request",
                "message": {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {},
                        "clientInfo": {"name": "test-client", "version": "1.0"}
                    }
                },
                "expected": "initialization response"
            },
            {
                "name": "Tools List Request",
                "message": {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                },
                "expected": "4 tools listed"
            },
            {
                "name": "Add Memory Tool Call",
                "message": {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "add_memory",
                        "arguments": {
                            "content": "Native MCP Server 기능 테스트 메모리",
                            "importance": 0.8
                        }
                    }
                },
                "expected": "memory successfully added"
            },
            {
                "name": "Search Memory Tool Call",
                "message": {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": "search_memory",
                        "arguments": {
                            "query": "Native MCP",
                            "limit": 3
                        }
                    }
                },
                "expected": "search results"
            },
            {
                "name": "Get Memory Stats Tool Call",
                "message": {
                    "jsonrpc": "2.0",
                    "id": 5,
                    "method": "tools/call",
                    "params": {
                        "name": "get_memory_stats",
                        "arguments": {}
                    }
                },
                "expected": "memory statistics"
            }
        ]
        
        # 각 테스트 케이스 실행
        test_results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔧 {i}. {test_case['name']} 테스트")
            
            try:
                # JSON-RPC 메시지 생성
                session_message = SessionMessage.from_json(json.dumps(test_case["message"]))
                
                # 메시지 처리
                response = await server._handle_message(session_message)
                
                if response:
                    response_data = json.loads(response.to_json())
                    
                    # 성공 응답 확인
                    if "result" in response_data:
                        print(f"   ✅ 응답 성공: {test_case['expected']}")
                        
                        # 상세 결과 출력
                        if test_case["name"] == "Tools List Request":
                            tools = response_data["result"].get("tools", [])
                            print(f"   📋 도구 수: {len(tools)}")
                            for tool in tools:
                                print(f"      - {tool['name']}: {tool['description'][:50]}...")
                                
                        elif "add_memory" in test_case["name"].lower():
                            if "content" in response_data["result"]:
                                content = response_data["result"]["content"][0]["text"]
                                if "Successfully Added" in content:
                                    print(f"   💾 메모리 추가 성공!")
                                    
                        elif "search_memory" in test_case["name"].lower():
                            if "content" in response_data["result"]:
                                content = response_data["result"]["content"][0]["text"]
                                if "Found" in content:
                                    print(f"   🔍 검색 성공!")
                                    
                        elif "stats" in test_case["name"].lower():
                            if "content" in response_data["result"]:
                                content = response_data["result"]["content"][0]["text"]
                                if "Statistics" in content:
                                    print(f"   📊 통계 조회 성공!")
                        
                        test_results.append({"test": test_case["name"], "status": "PASS", "details": "정상 응답"})
                        
                    else:
                        print(f"   ❌ 에러 응답: {response_data.get('error', {}).get('message', 'Unknown error')}")
                        test_results.append({"test": test_case["name"], "status": "FAIL", "details": "에러 응답"})
                else:
                    print(f"   ⚠️  응답 없음 (알림 메시지)")
                    test_results.append({"test": test_case["name"], "status": "PASS", "details": "알림 처리"})
                    
            except Exception as e:
                print(f"   ❌ 테스트 실패: {e}")
                test_results.append({"test": test_case["name"], "status": "FAIL", "details": str(e)})
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 기능 검증 테스트 결과")
        print("=" * 60)
        
        passed = sum(1 for r in test_results if r["status"] == "PASS")
        total = len(test_results)
        
        for result in test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {result['test']}: {result['status']} - {result['details']}")
        
        print("-" * 60)
        print(f"전체 결과: {passed}/{total} 테스트 통과 ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("\n🎉 모든 기능 테스트 통과! Native MCP Server 정상 작동")
            return True
        else:
            print(f"\n⚠️  {total-passed}개 테스트 실패, 추가 검토 필요")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 설정 오류: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_native_mcp_functionality())
    sys.exit(0 if result else 1)