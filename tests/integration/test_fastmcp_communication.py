#!/usr/bin/env python3
"""
FastMCP 핫픽스 서버 실제 통신 테스트
- JSON-RPC 2.0 프로토콜 준수 확인
- Claude Code MCP 클라이언트와의 호환성 검증
"""

import json
import subprocess
import time
import threading
import sys
import os
from pathlib import Path

import pytest

pytest.importorskip("greeum.mcp.fastmcp_hotfix_server", reason="FastMCP hotfix server unavailable in current build")

def test_mcp_server_communication():
    """FastMCP 서버와 실제 JSON-RPC 통신 테스트"""
    print("🧪 FastMCP 핫픽스 서버 통신 테스트")
    print("=" * 50)
    
    # 서버 프로세스 시작
    project_root = Path(__file__).resolve().parents[2]
    server_proc = subprocess.Popen(
        ["python3", "-c", """
import asyncio
import sys
sys.path.insert(0, '.')
from greeum.mcp.fastmcp_hotfix_server import main
asyncio.run(main())
"""],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(project_root)
    )
    
    def send_request(request_dict):
        """JSON-RPC 요청 전송"""
        request_json = json.dumps(request_dict) + "\n"
        print(f"📤 Request: {json.dumps(request_dict, indent=2)}")
        
        server_proc.stdin.write(request_json)
        server_proc.stdin.flush()
        
        # 응답 읽기 (타임아웃 5초)
        response_line = server_proc.stdout.readline()
        if response_line:
            try:
                response_dict = json.loads(response_line.strip())
                print(f"📥 Response: {json.dumps(response_dict, indent=2)}")
                return response_dict
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"Raw response: {response_line}")
                return None
        else:
            print("❌ No response received")
            return None
    
    try:
        time.sleep(1)  # 서버 시작 대기
        
        # 1. 초기화 요청
        print("1️⃣ Initialize 요청")
        init_response = send_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        })
        
        assert init_response is not None, "Initialize failed"
        
        time.sleep(0.5)
        
        # 2. 도구 목록 요청
        print()
        print("2️⃣ Tools 목록 요청")
        tools_response = send_request({
            "jsonrpc": "2.0", 
            "id": 2,
            "method": "tools/list",
            "params": {}
        })
        
        assert tools_response and "result" in tools_response, "tools/list call failed"
        tools = tools_response["result"]["tools"]
        print(f"✅ 도구 목록 수신: {len(tools)}개")
        for tool in tools:
            print(f"  - {tool['name']}: {tool.get('description', '')[:50]}...")

        time.sleep(0.5)
        
        # 3. 메모리 추가 도구 호출
        print()
        print("3️⃣ add_memory 도구 호출")
        add_response = send_request({
            "jsonrpc": "2.0",
            "id": 3, 
            "method": "tools/call",
            "params": {
                "name": "add_memory",
                "arguments": {
                    "content": "FastMCP 핫픽스 테스트 - 실제 MCP 통신 검증",
                    "importance": 0.8
                }
            }
        })
        
        assert add_response and "result" in add_response, "add_memory tool call failed"
        print("✅ 메모리 추가 성공")
        
        time.sleep(0.5)
        
        # 4. 메모리 검색 도구 호출
        print()
        print("4️⃣ search_memory 도구 호출")
        search_response = send_request({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call", 
            "params": {
                "name": "search_memory",
                "arguments": {
                    "query": "FastMCP",
                    "limit": 3
                }
            }
        })
        
        assert search_response and "result" in search_response, "search_memory tool call failed"
        print("✅ 메모리 검색 성공")
        
        print()
        print("🎉 모든 MCP 통신 테스트 통과!")
        
    except Exception as e:
        pytest.fail(f"MCP 통신 테스트 실패: {e}")
    finally:
        # 서버 프로세스 정리
        server_proc.terminate()
        time.sleep(1)
        if server_proc.poll() is None:
            server_proc.kill()

if __name__ == "__main__":
    test_mcp_server_communication()