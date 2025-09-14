#!/usr/bin/env python3
"""
Greeum v3.0.0.post3 Integration Test
"""

import sys
import os

# 가상환경 패키지 사용
sys.path.insert(0, 'test_greeum_post3/lib/python3.13/site-packages')

def test_basic_import():
    """기본 임포트 테스트"""
    try:
        import greeum
        print(f"✅ Greeum imported successfully: v{greeum.__version__}")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_core_components():
    """핵심 컴포넌트 테스트"""
    try:
        from greeum.core.block_manager import BlockManager
        from greeum.core.database_manager import DatabaseManager
        from greeum.core.branch_manager import BranchManager
        from greeum.core.usage_analytics import UsageAnalytics

        print("✅ Core components imported successfully")
        return True
    except Exception as e:
        print(f"❌ Core component import failed: {e}")
        return False

def test_memory_operations():
    """메모리 작업 테스트"""
    try:
        from greeum.core.database_manager import DatabaseManager
        from greeum.core.block_manager import BlockManager

        # 임시 DB로 테스트
        db_manager = DatabaseManager(db_path=":memory:")
        block_manager = BlockManager(db_manager)

        # 메모리 추가
        block_id = block_manager.add_block(
            context="테스트 메모리 v3.0.0.post3",
            importance=0.8
        )

        print(f"✅ Memory block added: #{block_id}")

        # 검색 테스트
        results = db_manager.search_blocks("테스트", limit=5)
        print(f"✅ Search completed: {len(results)} results")

        return True
    except Exception as e:
        print(f"❌ Memory operations failed: {e}")
        return False

def test_mcp_tools():
    """MCP 도구 테스트"""
    try:
        from greeum.mcp.production_mcp_server import NativeMCPServer
        import json

        # 서버 초기화
        server = NativeMCPServer()

        # tools/list 테스트
        list_request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/list'
        }
        response = server.process_request(list_request)
        tools = response.get('result', {}).get('tools', [])

        tool_names = [tool['name'] for tool in tools]

        # GPT 필수 도구 확인
        if 'search' in tool_names and 'fetch' in tool_names:
            print(f"✅ MCP GPT tools present: search, fetch")
        else:
            print(f"❌ Missing GPT tools. Found: {tool_names}")
            return False

        print(f"✅ MCP server working with {len(tools)} tools")
        return True

    except Exception as e:
        print(f"❌ MCP tools test failed: {e}")
        return False

def test_cli_commands():
    """CLI 명령 테스트"""
    try:
        import subprocess

        # greeum --version
        result = subprocess.run(
            ['test_greeum_post3/bin/greeum', '--version'],
            capture_output=True,
            text=True
        )

        if '3.0.0.post3' in result.stdout:
            print(f"✅ CLI version check: {result.stdout.strip()}")
        else:
            print(f"❌ CLI version mismatch: {result.stdout}")
            return False

        return True
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("\n" + "="*50)
    print("Greeum v3.0.0.post3 Integration Test")
    print("="*50 + "\n")

    tests = [
        ("Basic Import", test_basic_import),
        ("Core Components", test_core_components),
        ("Memory Operations", test_memory_operations),
        ("MCP Tools", test_mcp_tools),
        ("CLI Commands", test_cli_commands)
    ]

    results = []
    for name, test_func in tests:
        print(f"\n[{name}]")
        success = test_func()
        results.append((name, success))

    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed successfully!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())