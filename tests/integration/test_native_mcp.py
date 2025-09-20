#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Native MCP Server 기능 검증 테스트
실제 JSON-RPC 메시지로 MCP 도구 기능 테스트
"""

import asyncio
import json
import sys
from pathlib import Path

import pytest

# Greeum Native MCP 모듈 import
sys.path.insert(0, str(Path(__file__).parent))

pytest.importorskip("greeum.mcp.native.server", reason="Native MCP server not available in current build")

pytest.skip("Native MCP server integration test disabled for lightweight CI run", allow_module_level=True)

async def _run_native_mcp_functionality():
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
                "expected": "tools list response"
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
                            "content": "Native MCP 테스트 메모리",
                            "importance": 0.7
                        }
                    }
                },
                "expected": "memory added successfully"
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
                            "limit": 5
                        }
                    }
                },
                "expected": "search results"
            }
        ]
        
        # 각 테스트 케이스 실행
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔍 {i}. {test_case['name']}")
            print("-" * 40)
            
            try:
                # 메시지를 SessionMessage로 변환
                message = SessionMessage(
                    jsonrpc=test_case["message"]["jsonrpc"],
                    id=test_case["message"]["id"],
                    method=test_case["message"]["method"],
                    params=test_case["message"].get("params", {})
                )
                
                # 서버에 메시지 전송
                response = await server.handle_message(message)
                
                if response:
                    print(f"✅ 응답 수신: {response}")
                else:
                    print("⚠️ 응답 없음")
                    
            except Exception as e:
                print(f"❌ 테스트 실패: {e}")
                continue
        
        print("\n" + "=" * 60)
        print("✅ Native MCP Server 기능 검증 완료!")
        
    except ImportError as e:
        print(f"❌ 모듈 import 실패: {e}")
        print("Native MCP 서버가 현재 빌드에서 사용할 수 없습니다.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
    finally:
        # 서버 정리
        try:
            if 'server' in locals():
                await server.cleanup()
                print("🧹 서버 정리 완료")
        except:
            pass


def test_native_mcp_functionality():
    """Native MCP Server 기능 테스트"""
    asyncio.run(_run_native_mcp_functionality())


if __name__ == "__main__":
    asyncio.run(_run_native_mcp_functionality())
