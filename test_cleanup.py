#!/usr/bin/env python3
"""
Dead Code 정리 후 테스트
"""

import os
import sys

def test_removed_files():
    """삭제된 파일들이 없는지 확인"""
    removed_files = [
        'greeum/ai_memory_guidance.py',
        'greeum/token_utils.py',
        'greeum/core/neural_memory.py',
        'greeum/core/engram.py',
        'greeum/core/phase_three_coordinator.py',
        'greeum/core/precompact_hook.py',
        'greeum/core/auto_compact_monitor.py',
        'greeum/core/metrics_collector.py',
        'greeum/core/metrics_dashboard.py',
        'greeum/core/migration/ai_parser.py',
        'greeum/core/migration/validation_rollback.py',
        'greeum/mcp/claude_code_mcp_server.py',
        'greeum/mcp/working_mcp_server.py',
        'greeum/mcp/fastmcp_hotfix_server.py',
        'greeum/mcp/simple_mcp_bridge.py',
        'legacy_backup/'
    ]

    print("삭제된 파일 확인:")
    for file_path in removed_files:
        exists = os.path.exists(file_path)
        status = "❌ 아직 존재" if exists else "✅ 삭제됨"
        print(f"  {file_path}: {status}")

    return all(not os.path.exists(f) for f in removed_files)

def test_core_functionality():
    """핵심 기능 테스트"""
    print("\n핵심 기능 테스트:")

    try:
        # 1. 기본 import
        import greeum
        print(f"✅ Greeum 버전: {greeum.__version__}")

        # 2. 핵심 컴포넌트
        from greeum.core.block_manager import BlockManager
        from greeum.core.database_manager import DatabaseManager
        from greeum.core.branch_manager import BranchManager
        print("✅ 핵심 컴포넌트 import 성공")

        # 3. 메모리 작업
        db = DatabaseManager(':memory:')
        bm = BlockManager(db)
        # v3.0.0 API: add_block requires context, keywords, tags, embedding, importance
        block_id = bm.add_block(
            context='테스트 콘텐츠',
            keywords=['테스트'],
            tags=['test'],
            embedding=[0.1] * 768,  # dummy embedding
            importance=0.5
        )
        print(f"✅ 메모리 블록 추가: #{block_id}")

        # 4. MCP 서버
        from greeum.mcp.production_mcp_server import NativeMCPServer
        server = NativeMCPServer()

        # tools/list 확인
        request = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}
        response = server.process_request(request)
        tools = response.get('result', {}).get('tools', [])
        tool_names = [t['name'] for t in tools]

        if 'search' in tool_names and 'fetch' in tool_names:
            print(f"✅ MCP 서버 정상 ({len(tools)} 도구)")
        else:
            print(f"❌ MCP 도구 문제: {tool_names}")
            return False

        # 5. merge_cli.py 수정 확인 - evaluate는 Click 커맨드이므로 직접 파일 읽기
        with open('greeum/cli/merge_cli.py', 'r') as f:
            source = f.read()
        if 'connection_string=' in source:
            print("✅ merge_cli.py 수정 확인")
        else:
            print("❌ merge_cli.py 수정 안됨")
            return False

        return True

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False

def test_import_errors():
    """삭제된 모듈 import 시도"""
    print("\n삭제된 모듈 import 테스트:")

    dead_modules = [
        'greeum.ai_memory_guidance',
        'greeum.core.neural_memory',
        'greeum.core.engram',
        'greeum.core.phase_three_coordinator',
        'greeum.mcp.claude_code_mcp_server',
        'greeum.mcp.working_mcp_server'
    ]

    for module in dead_modules:
        try:
            __import__(module)
            print(f"❌ {module} - import 성공 (삭제 안됨)")
            return False
        except ImportError:
            print(f"✅ {module} - import 실패 (정상)")

    return True

def main():
    print("="*50)
    print("Dead Code 정리 후 테스트")
    print("="*50)

    results = []

    # 1. 삭제 파일 확인
    results.append(("파일 삭제 확인", test_removed_files()))

    # 2. 핵심 기능 테스트
    results.append(("핵심 기능 테스트", test_core_functionality()))

    # 3. Import 에러 테스트
    results.append(("Import 에러 테스트", test_import_errors()))

    # 결과 요약
    print("\n" + "="*50)
    print("테스트 결과 요약")
    print("="*50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}")

    print(f"\n총 {passed}/{total} 테스트 통과")

    if passed == total:
        print("\n🎉 모든 테스트 통과! Dead code 정리 성공!")
        return 0
    else:
        print(f"\n⚠️ {total - passed}개 테스트 실패")
        return 1

if __name__ == "__main__":
    sys.exit(main())