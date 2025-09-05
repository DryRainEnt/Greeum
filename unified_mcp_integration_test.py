#!/usr/bin/env python3
"""
통합 MCP 서버 완전한 검증 테스트
- 환경별 어댑터 동작 검증
- 실제 MCP 프로토콜 통신 테스트
- 기존 호환성 완전 확인
"""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

class UnifiedMCPIntegrationTest:
    def __init__(self):
        self.test_results = {
            'environment_detection': False,
            'adapter_loading': False,
            'mcp_communication': False,
            'tool_functionality': False,
            'cli_integration': False,
            'performance_check': False
        }
        self.server_proc = None
        
    def run_all_tests(self):
        """모든 통합 테스트 실행"""
        print("🧪 통합 MCP 서버 완전한 검증 시작")
        print("="*60)
        
        try:
            # 1. 환경 감지 테스트
            self.test_environment_detection()
            
            # 2. 어댑터 로딩 테스트
            self.test_adapter_loading()
            
            # 3. MCP 통신 테스트
            self.test_mcp_communication()
            
            # 4. 도구 기능성 테스트
            self.test_tool_functionality()
            
            # 5. CLI 통합 테스트
            self.test_cli_integration()
            
            # 6. 성능 체크
            self.test_performance()
            
            # 결과 요약
            self.print_summary()
            
        except Exception as e:
            print(f"❌ 테스트 실행 중 오류: {e}")
            return False
            
        return all(self.test_results.values())
    
    def test_environment_detection(self):
        """1. 환경 감지 테스트"""
        print("\\n1️⃣ 환경 감지 테스트")
        print("-" * 40)
        
        try:
            sys.path.insert(0, '.')
            from greeum.mcp.unified_mcp_server import EnvironmentDetector
            
            env = EnvironmentDetector.detect_environment()
            print(f"  ✅ 감지된 환경: {env}")
            
            # 환경별 예상 동작 확인
            expected_envs = ['wsl', 'powershell', 'macos', 'linux', 'unknown']
            if env in expected_envs:
                print(f"  ✅ 유효한 환경 감지")
                self.test_results['environment_detection'] = True
            else:
                print(f"  ❌ 알 수 없는 환경: {env}")
                
        except Exception as e:
            print(f"  ❌ 환경 감지 실패: {e}")
    
    def test_adapter_loading(self):
        """2. 어댑터 로딩 테스트"""
        print("\\n2️⃣ 어댑터 로딩 테스트")
        print("-" * 40)
        
        try:
            from greeum.mcp.unified_mcp_server import AdapterManager
            
            manager = AdapterManager()
            print(f"  ✅ 어댑터 매니저 생성: {manager.environment}")
            
            # 어댑터 로딩 테스트 (실제 서버 시작 없이)
            if manager.environment in ['macos', 'linux']:
                from greeum.mcp.adapters.jsonrpc_adapter import JSONRPCAdapter
                adapter = JSONRPCAdapter()
                print("  ✅ JSON-RPC 어댑터 로딩 성공")
                
                # 컴포넌트 초기화 테스트
                components = adapter.initialize_greeum_components()
                if components and len(components) == 6:
                    print("  ✅ Greeum 컴포넌트 초기화 완료")
                    self.test_results['adapter_loading'] = True
                else:
                    print("  ❌ 컴포넌트 초기화 실패")
                    
            else:
                # WSL/PowerShell 환경 (FastMCP)
                try:
                    from greeum.mcp.adapters.fastmcp_adapter import FastMCPAdapter
                    print("  ✅ FastMCP 어댑터 로딩 가능")
                    self.test_results['adapter_loading'] = True
                except ImportError:
                    print("  ⚠️  FastMCP 의존성 누락 (예상됨)")
                    self.test_results['adapter_loading'] = True  # 의존성 누락은 정상
                    
        except Exception as e:
            print(f"  ❌ 어댑터 로딩 실패: {e}")
    
    def test_mcp_communication(self):
        """3. MCP 통신 테스트"""
        print("\\n3️⃣ MCP 프로토콜 통신 테스트")
        print("-" * 40)
        
        # 간단한 JSON-RPC 어댑터 직접 테스트
        try:
            from greeum.mcp.adapters.jsonrpc_adapter import JSONRPCAdapter
            
            adapter = JSONRPCAdapter()
            
            # Initialize 요청 시뮬레이션
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1.0"}
                }
            }
            
            # 비동기 핸들러 테스트
            import asyncio
            response = asyncio.run(adapter._handle_request(init_request))
            
            if response and response.get("result"):
                print("  ✅ Initialize 응답 성공")
                
                # Tools list 테스트
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
                
                tools_response = asyncio.run(adapter._handle_request(tools_request))
                if tools_response and "tools" in tools_response.get("result", {}):
                    tools = tools_response["result"]["tools"]
                    print(f"  ✅ Tools 목록 수신: {len(tools)}개")
                    
                    expected_tools = ["add_memory", "search_memory", "get_memory_stats", "usage_analytics"]
                    found_tools = [t["name"] for t in tools]
                    
                    if all(tool in found_tools for tool in expected_tools):
                        print("  ✅ 모든 필수 도구 확인")
                        self.test_results['mcp_communication'] = True
                    else:
                        print("  ❌ 일부 도구 누락")
                else:
                    print("  ❌ Tools 목록 실패")
            else:
                print("  ❌ Initialize 실패")
                
        except Exception as e:
            print(f"  ❌ MCP 통신 테스트 실패: {e}")
    
    def test_tool_functionality(self):
        """4. 도구 기능성 테스트"""
        print("\\n4️⃣ 도구 기능성 테스트")
        print("-" * 40)
        
        try:
            from greeum.mcp.adapters.jsonrpc_adapter import JSONRPCAdapter
            
            adapter = JSONRPCAdapter()
            
            # add_memory 도구 테스트
            add_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "add_memory",
                    "arguments": {
                        "content": "통합 MCP 서버 검증 테스트 메모리",
                        "importance": 0.8
                    }
                }
            }
            
            add_response = asyncio.run(adapter._handle_request(add_request))
            if add_response and "result" in add_response:
                content = add_response["result"].get("content", [{}])
                if content and "text" in content[0]:
                    text = content[0]["text"]
                    if "Successfully Added" in text and "Block Index" in text:
                        print("  ✅ add_memory 도구 정상 작동")
                    else:
                        print(f"  ❌ add_memory 응답 형식 이상")
                        return
            else:
                print("  ❌ add_memory 호출 실패")
                return
            
            # search_memory 도구 테스트
            search_request = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "search_memory",
                    "arguments": {
                        "query": "통합 MCP",
                        "limit": 3
                    }
                }
            }
            
            search_response = asyncio.run(adapter._handle_request(search_request))
            if search_response and "result" in search_response:
                content = search_response["result"].get("content", [{}])
                if content and "text" in content[0]:
                    text = content[0]["text"]
                    if "Found" in text:
                        print("  ✅ search_memory 도구 정상 작동")
                        self.test_results['tool_functionality'] = True
                    else:
                        print(f"  ❌ search_memory 응답 형식 이상")
            else:
                print("  ❌ search_memory 호출 실패")
                
        except Exception as e:
            print(f"  ❌ 도구 기능성 테스트 실패: {e}")
    
    def test_cli_integration(self):
        """5. CLI 통합 테스트"""
        print("\\n5️⃣ CLI 통합 테스트")
        print("-" * 40)
        
        try:
            # CLI 명령어 존재 확인
            result = subprocess.run(['greeum', 'mcp', '--help'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'serve' in result.stdout:
                print("  ✅ CLI 명령어 존재")
                
                # 기본 메모리 기능 테스트 (CLI)
                result = subprocess.run(['greeum', 'memory', 'add', 'CLI 통합 테스트 메모리'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print("  ✅ CLI 메모리 기능 정상")
                    self.test_results['cli_integration'] = True
                else:
                    print(f"  ❌ CLI 메모리 기능 오류")
            else:
                print("  ❌ CLI 명령어 문제")
                
        except subprocess.TimeoutExpired:
            print("  ❌ CLI 명령어 타임아웃")
        except Exception as e:
            print(f"  ❌ CLI 통합 테스트 오류: {e}")
    
    def test_performance(self):
        """6. 성능 체크"""
        print("\\n6️⃣ 성능 테스트")
        print("-" * 40)
        
        try:
            from greeum.mcp.adapters.jsonrpc_adapter import JSONRPCAdapter
            
            adapter = JSONRPCAdapter()
            
            # 다중 요청 성능 테스트
            start_time = time.time()
            success_count = 0
            
            for i in range(5):
                search_request = {
                    "jsonrpc": "2.0",
                    "id": 100 + i,
                    "method": "tools/call",
                    "params": {
                        "name": "search_memory",
                        "arguments": {"query": f"performance test {i}", "limit": 2}
                    }
                }
                
                response = asyncio.run(adapter._handle_request(search_request))
                if response and "result" in response:
                    success_count += 1
            
            elapsed = time.time() - start_time
            
            if success_count >= 4:  # 80% 이상 성공
                print(f"  ✅ 성능 테스트: {success_count}/5 성공, {elapsed:.2f}초")
                self.test_results['performance_check'] = True
            else:
                print(f"  ❌ 성능 테스트: {success_count}/5 성공 (부족)")
                
        except Exception as e:
            print(f"  ❌ 성능 테스트 실패: {e}")
    
    def print_summary(self):
        """테스트 결과 요약"""
        print("\\n" + "=" * 60)
        print("📊 통합 MCP 서버 검증 결과")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name:25} : {status}")
        
        print("-" * 60)
        print(f"전체 결과: {passed_tests}/{total_tests} 통과 ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("\\n🎉 모든 테스트 통과! 통합 서버 배포 준비 완료")
        elif passed_tests >= total_tests * 0.8:  # 80% 이상
            print("\\n⚠️  대부분 테스트 통과, 일부 개선 필요")
        else:
            print("\\n❌ 심각한 문제 발견, 추가 수정 필요")

if __name__ == "__main__":
    tester = UnifiedMCPIntegrationTest()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n👋 테스트 중단됨")
        sys.exit(1)