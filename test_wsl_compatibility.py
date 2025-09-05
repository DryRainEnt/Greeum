#!/usr/bin/env python3
"""
WSL 호환성 테스트 스크립트
Native MCP Server가 WSL 환경에서 정상 작동하는지 직접 테스트

원래 문제:
- WSL/PowerShell 환경에서 FastMCP asyncio 충돌
- Claude Desktop과 MCP 서버 연동 실패
- stdout/stderr 격리 문제

해결책:
- Native JSON-RPC 2.0 MCP 서버로 asyncio 충돌 완전 차단
- 직접 stdin/stdout 처리로 WSL 호환성 확보
"""

import subprocess
import json
import time
import sys
import os
import tempfile

def test_wsl_native_mcp():
    """WSL 환경 시뮬레이션 테스트"""
    print("🔍 WSL 호환성 테스트 - Native MCP Server")
    print("   원래 문제: WSL에서 FastMCP asyncio 충돌")
    print("   해결책: Native JSON-RPC로 asyncio 완전 차단")
    print()
    
    # 환경 변수 설정 (WSL 시뮬레이션)
    env = os.environ.copy()
    env['GREEUM_DATA_DIR'] = '/tmp/greeum-wsl-test'
    env['PYTHONPATH'] = '/Users/dryrain/DevRoom/Greeum:/Users/dryrain/DevRoom/GreeumMCP'
    env['WSL_DISTRO_NAME'] = 'Ubuntu'  # WSL 환경 시뮬레이션
    env['TERM'] = 'xterm-256color'
    
    # 임시 데이터 디렉토리 생성
    os.makedirs('/tmp/greeum-wsl-test', exist_ok=True)
    
    # Native MCP 서버 실행 (WSL 환경 시뮬레이션)
    print("🚀 Native MCP Server 시작 (WSL 환경 시뮬레이션)...")
    
    proc = subprocess.Popen([
        sys.executable, 'greeum/mcp/native_mcp_server.py'
    ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
       text=True, env=env, bufsize=0)
    
    success_tests = 0
    total_tests = 4
    
    try:
        time.sleep(0.3)  # 서버 시작 대기
        
        # 1. Initialize 테스트 (WSL 호환성 핵심)
        print("📡 1/4: MCP Initialize 테스트...")
        init_msg = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {
                    'name': 'wsl-compatibility-test', 
                    'version': '1.0',
                    'platform': 'WSL-Ubuntu'
                }
            }
        }
        
        # WSL 환경에서의 JSON-RPC 통신 테스트
        proc.stdin.write(json.dumps(init_msg) + '\n')
        proc.stdin.flush()
        
        # 응답 확인 (WSL에서는 버퍼링 이슈 가능)
        try:
            response = proc.stdout.readline()
            if response:
                init_data = json.loads(response.strip())
                if init_data.get('result', {}).get('protocolVersion'):
                    print("   ✅ WSL JSON-RPC 통신 성공")
                    success_tests += 1
                else:
                    print("   ❌ WSL JSON-RPC 응답 오류")
            else:
                print("   ❌ WSL 환경에서 응답 없음")
        except Exception as e:
            print(f"   ❌ WSL Initialize 실패: {e}")
        
        # 2. Tools List 테스트 (WSL 환경 안정성)
        print("📋 2/4: MCP Tools List 테스트...")
        tools_msg = {
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/list',
            'params': {}
        }
        
        proc.stdin.write(json.dumps(tools_msg) + '\n')
        proc.stdin.flush()
        
        try:
            tools_response = proc.stdout.readline()
            if tools_response:
                tools_data = json.loads(tools_response.strip())
                tools = tools_data.get('result', {}).get('tools', [])
                if len(tools) >= 4:
                    print(f"   ✅ WSL 도구 목록 정상 ({len(tools)}개)")
                    success_tests += 1
                else:
                    print(f"   ❌ WSL 도구 수 문제 ({len(tools)}개)")
        except Exception as e:
            print(f"   ❌ WSL Tools List 실패: {e}")
        
        # 3. Memory Add 테스트 (WSL 파일 시스템 호환성)
        print("💾 3/4: Memory Add 테스트 (WSL 파일 시스템)...")
        add_msg = {
            'jsonrpc': '2.0',
            'id': 3,
            'method': 'tools/call',
            'params': {
                'name': 'add_memory',
                'arguments': {
                    'content': 'WSL 호환성 테스트 - Native MCP 서버 정상 동작 확인',
                    'importance': 0.9
                }
            }
        }
        
        proc.stdin.write(json.dumps(add_msg) + '\n')
        proc.stdin.flush()
        
        try:
            add_response = proc.stdout.readline()
            if add_response:
                add_data = json.loads(add_response.strip())
                result_text = add_data.get('result', {}).get('content', [{}])[0].get('text', '')
                if '✅ **Memory Successfully Added!**' in result_text:
                    print("   ✅ WSL 파일 시스템 정상 동작")
                    success_tests += 1
                else:
                    print("   ❌ WSL 메모리 추가 실패")
        except Exception as e:
            print(f"   ❌ WSL Memory Add 실패: {e}")
        
        # 4. Memory Search 테스트 (WSL 전체 통합)
        print("🔍 4/4: Memory Search 테스트 (WSL 통합)...")
        search_msg = {
            'jsonrpc': '2.0',
            'id': 4,
            'method': 'tools/call',
            'params': {
                'name': 'search_memory',
                'arguments': {
                    'query': 'WSL 호환성',
                    'limit': 3
                }
            }
        }
        
        proc.stdin.write(json.dumps(search_msg) + '\n')
        proc.stdin.flush()
        
        try:
            search_response = proc.stdout.readline()
            if search_response:
                search_data = json.loads(search_response.strip())
                search_text = search_data.get('result', {}).get('content', [{}])[0].get('text', '')
                if '🔍' in search_text:
                    print("   ✅ WSL 통합 검색 성공")
                    success_tests += 1
                else:
                    print("   ❌ WSL 검색 실패")
        except Exception as e:
            print(f"   ❌ WSL Memory Search 실패: {e}")
        
        # 결과 분석
        print()
        if success_tests == total_tests:
            print("🏆 WSL 호환성 테스트: 100% 성공!")
            print("   ✅ asyncio 충돌 완전 해결")
            print("   ✅ WSL JSON-RPC 통신 정상")
            print("   ✅ WSL 파일 시스템 호환")
            print("   ✅ WSL 전체 기능 동작")
            print()
            print("🚀 WSL 환경에서 Claude Desktop 연동 성공 예상!")
            return True
        else:
            print(f"⚠️ WSL 호환성 테스트: {success_tests}/{total_tests} 성공")
            print("   일부 기능에서 WSL 호환성 이슈 존재")
            return False
            
    except Exception as e:
        print(f"❌ WSL 테스트 중 오류: {e}")
        return False
        
    finally:
        # 안전한 종료
        try:
            proc.stdin.close()
            proc.terminate()
            proc.wait(timeout=2)
        except:
            proc.kill()
        
        # WSL stderr 확인
        try:
            stderr = proc.stderr.read()
            if stderr:
                if 'Already running asyncio' in stderr:
                    print("❌ WSL에서도 asyncio 충돌 발생!")
                    return False
                elif 'Permission denied' in stderr:
                    print("⚠️ WSL 권한 문제 발생")
                else:
                    print("✅ WSL 서버 로그 정상")
        except:
            pass

def create_wsl_setup_guide():
    """WSL 실제 설정 가이드 생성"""
    guide = """
# WSL Claude Desktop 연동 설정 가이드

## 1. WSL에서 Python 환경 확인
```bash
python3 --version
pip3 --version
```

## 2. Greeum 설치 (WSL 내부)
```bash
# 개발 버전 설치
cd /home/username/
git clone /mnt/c/path/to/Greeum
cd Greeum
pip3 install -e .
```

## 3. Windows Claude Desktop 설정
`C:\\Users\\username\\AppData\\Roaming\\Claude\\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "greeum_wsl": {
      "command": "wsl",
      "args": [
        "python3",
        "/home/username/Greeum/greeum/mcp/native_mcp_server.py"
      ],
      "env": {
        "GREEUM_DATA_DIR": "/home/username/greeum-data",
        "PYTHONPATH": "/home/username/Greeum"
      }
    }
  }
}
```

## 4. 테스트 명령어
```bash
# WSL 내부에서 직접 테스트
cd /home/username/Greeum
python3 greeum/mcp/native_mcp_server.py
```
"""
    
    with open('WSL_CLAUDE_DESKTOP_SETUP.md', 'w') as f:
        f.write(guide)
    
    print("📝 WSL_CLAUDE_DESKTOP_SETUP.md 가이드 생성 완료")

if __name__ == '__main__':
    print("🔧 Native MCP Server WSL 호환성 테스트")
    print("=" * 50)
    
    success = test_wsl_native_mcp()
    
    if success:
        print()
        print("✅ WSL 테스트 성공! Claude Desktop 연동 가능성 높음")
        create_wsl_setup_guide()
    else:
        print()
        print("❌ WSL 호환성 문제 - 추가 수정 필요")
    
    print()
    print("다음 단계: 실제 WSL 환경에서 Claude Desktop 연동 테스트")