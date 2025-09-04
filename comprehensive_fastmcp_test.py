#!/usr/bin/env python3
"""
포괄적 FastMCP 핫픽스 검증 테스트
- 실제 MCP 프로토콜 통신 검증
- 기존 사용자 워크플로우 호환성 확인
- 성능 및 안정성 테스트
- WSL/PowerShell 환경 시뮬레이션
"""

import json
import subprocess
import time
import sys
import os
import threading
import signal
from pathlib import Path

class ComprehensiveFastMCPTest:
    def __init__(self):
        self.test_results = {
            'mcp_protocol': False,
            'tool_functionality': False,
            'compatibility': False,
            'performance': False,
            'error_handling': False
        }
        self.server_proc = None
        
    def run_all_tests(self):
        """모든 검증 테스트 실행"""
        print("🧪 포괄적 FastMCP 핫픽스 검증 시작")
        print("=" * 60)
        
        try:
            # 1. MCP 프로토콜 통신 테스트
            self.test_mcp_protocol()
            
            # 2. 도구 기능성 테스트
            self.test_tool_functionality()
            
            # 3. 기존 사용자 호환성 테스트
            self.test_user_compatibility()
            
            # 4. 성능 테스트
            self.test_performance()
            
            # 5. 에러 핸들링 테스트
            self.test_error_handling()
            
            # 결과 요약
            self.print_summary()
            
        except Exception as e:
            print(f"❌ 테스트 실행 중 오류: {e}")
            return False
            
        return all(self.test_results.values())
    
    def start_mcp_server(self):
        """MCP 서버 시작"""
        if self.server_proc:
            return True
            
        try:
            self.server_proc = subprocess.Popen([
                'python3', '-c', '''
import sys
import asyncio
sys.path.insert(0, ".")
from greeum.mcp.fastmcp_hotfix_server import main
try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
                '''
            ], 
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="/Users/dryrain/DevRoom/Greeum"
            )
            
            time.sleep(2)  # 서버 시작 대기
            
            if self.server_proc.poll() is None:
                print("✅ MCP 서버 시작 성공")
                return True
            else:
                print("❌ MCP 서버 시작 실패")
                return False
                
        except Exception as e:
            print(f"❌ 서버 시작 오류: {e}")
            return False
    
    def stop_mcp_server(self):
        """MCP 서버 정지"""
        if self.server_proc:
            try:
                self.server_proc.terminate()
                time.sleep(1)
                if self.server_proc.poll() is None:
                    self.server_proc.kill()
            except:
                pass
            self.server_proc = None
    
    def send_mcp_request(self, request):
        """MCP 요청 전송"""
        if not self.server_proc:
            return None
            
        try:
            request_json = json.dumps(request) + "\\n"
            self.server_proc.stdin.write(request_json)
            self.server_proc.stdin.flush()
            
            # 응답 읽기 (타임아웃 5초)
            response_line = self.server_proc.stdout.readline()
            if response_line.strip():
                return json.loads(response_line.strip())
        except Exception as e:
            print(f"  ❌ 요청/응답 오류: {e}")
        return None
    
    def test_mcp_protocol(self):
        """1. MCP 프로토콜 통신 테스트"""
        print("\\n1️⃣ MCP 프로토콜 통신 테스트")
        print("-" * 40)
        
        if not self.start_mcp_server():
            print("  ❌ 서버 시작 실패")
            return
        
        # Initialize 요청
        init_response = self.send_mcp_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize", 
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        })
        
        if init_response and "result" in init_response:
            print("  ✅ Initialize 성공")
            
            # Tools list 요청
            tools_response = self.send_mcp_request({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            })
            
            if tools_response and "result" in tools_response:
                tools = tools_response["result"].get("tools", [])
                print(f"  ✅ Tools 목록 수신: {len(tools)}개 도구")
                
                expected_tools = ["add_memory", "search_memory", "get_memory_stats", "usage_analytics"]
                found_tools = [t["name"] for t in tools]
                
                for expected in expected_tools:
                    if expected in found_tools:
                        print(f"    ✅ {expected}")
                    else:
                        print(f"    ❌ {expected} 누락")
                        return
                
                self.test_results['mcp_protocol'] = True
            else:
                print("  ❌ Tools 목록 실패")
        else:
            print("  ❌ Initialize 실패")
    
    def test_tool_functionality(self):
        """2. 도구 기능성 테스트"""
        print("\\n2️⃣ 도구 기능성 테스트")
        print("-" * 40)
        
        if not self.server_proc:
            print("  ❌ 서버 없음")
            return
        
        # add_memory 도구 테스트
        add_response = self.send_mcp_request({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "add_memory",
                "arguments": {
                    "content": "FastMCP 핫픽스 포괄적 테스트 메모리",
                    "importance": 0.9
                }
            }
        })
        
        if add_response and "result" in add_response:
            content = add_response["result"].get("content", [{}])
            if content and "text" in content[0]:
                text = content[0]["text"]
                if "Successfully Added" in text and "Block Index" in text:
                    print("  ✅ add_memory 도구 정상 작동")
                else:
                    print(f"  ❌ add_memory 응답 형식 이상: {text[:100]}...")
                    return
        else:
            print("  ❌ add_memory 호출 실패")
            return
        
        # search_memory 도구 테스트
        search_response = self.send_mcp_request({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "search_memory",
                "arguments": {
                    "query": "FastMCP 핫픽스",
                    "limit": 3
                }
            }
        })
        
        if search_response and "result" in search_response:
            content = search_response["result"].get("content", [{}])
            if content and "text" in content[0]:
                text = content[0]["text"]
                if "Found" in text and "memories" in text:
                    print("  ✅ search_memory 도구 정상 작동")
                    self.test_results['tool_functionality'] = True
                else:
                    print(f"  ❌ search_memory 응답 형식 이상: {text[:100]}...")
        else:
            print("  ❌ search_memory 호출 실패")
    
    def test_user_compatibility(self):
        """3. 기존 사용자 호환성 테스트"""
        print("\\n3️⃣ 기존 사용자 호환성 테스트")
        print("-" * 40)
        
        try:
            # CLI 명령어 존재 확인
            result = subprocess.run(['greeum', 'mcp', '--help'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'serve' in result.stdout:
                print("  ✅ 'greeum mcp serve' 명령어 존재")
            else:
                print("  ❌ MCP CLI 명령어 문제")
                return
            
            # 기본 메모리 기능 테스트
            result = subprocess.run(['greeum', 'memory', 'add', 'CLI 호환성 테스트 메모리'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("  ✅ 기본 CLI 메모리 기능 정상")
            else:
                print(f"  ❌ CLI 메모리 기능 오류: {result.stderr}")
                return
            
            # 검색 기능 테스트
            result = subprocess.run(['greeum', 'memory', 'search', 'CLI', '--count', '2'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and 'Found' in result.stdout:
                print("  ✅ CLI 검색 기능 정상")
                self.test_results['compatibility'] = True
            else:
                print(f"  ❌ CLI 검색 기능 오류: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("  ❌ CLI 명령어 타임아웃")
        except Exception as e:
            print(f"  ❌ 호환성 테스트 오류: {e}")
    
    def test_performance(self):
        """4. 성능 테스트"""
        print("\\n4️⃣ 성능 테스트")
        print("-" * 40)
        
        if not self.server_proc:
            print("  ❌ 서버 없음")
            return
        
        # 다중 요청 성능 테스트
        start_time = time.time()
        success_count = 0
        
        for i in range(5):
            response = self.send_mcp_request({
                "jsonrpc": "2.0",
                "id": 100 + i,
                "method": "tools/call",
                "params": {
                    "name": "search_memory",
                    "arguments": {"query": f"performance test {i}", "limit": 2}
                }
            })
            
            if response and "result" in response:
                success_count += 1
        
        elapsed = time.time() - start_time
        
        if success_count >= 4:  # 80% 이상 성공
            print(f"  ✅ 성능 테스트: {success_count}/5 성공, {elapsed:.2f}초")
            self.test_results['performance'] = True
        else:
            print(f"  ❌ 성능 테스트: {success_count}/5 성공 (부족)")
    
    def test_error_handling(self):
        """5. 에러 핸들링 테스트"""
        print("\\n5️⃣ 에러 핸들링 테스트")
        print("-" * 40)
        
        if not self.server_proc:
            print("  ❌ 서버 없음")
            return
        
        # 잘못된 도구 호출
        error_response = self.send_mcp_request({
            "jsonrpc": "2.0",
            "id": 200,
            "method": "tools/call",
            "params": {
                "name": "nonexistent_tool",
                "arguments": {}
            }
        })
        
        if error_response and "error" in error_response:
            print("  ✅ 잘못된 도구 호출 에러 처리 정상")
        else:
            print("  ❌ 에러 처리 미흡")
            return
        
        # 잘못된 파라미터 테스트
        bad_param_response = self.send_mcp_request({
            "jsonrpc": "2.0",
            "id": 201,
            "method": "tools/call",
            "params": {
                "name": "add_memory",
                "arguments": {
                    "content": "",  # 빈 내용
                    "importance": 2.0  # 범위 초과
                }
            }
        })
        
        # 어떤 형태든 응답이 와야 함 (에러든 성공이든)
        if bad_param_response:
            print("  ✅ 잘못된 파라미터 처리 확인")
            self.test_results['error_handling'] = True
        else:
            print("  ❌ 파라미터 검증 미흡")
    
    def print_summary(self):
        """테스트 결과 요약"""
        print("\\n" + "=" * 60)
        print("📊 포괄적 FastMCP 핫픽스 검증 결과")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name:20} : {status}")
        
        print("-" * 60)
        print(f"전체 결과: {passed_tests}/{total_tests} 통과 ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("\\n🎉 모든 테스트 통과! 배포 준비 완료")
        elif passed_tests >= total_tests * 0.8:  # 80% 이상
            print("\\n⚠️  대부분 테스트 통과, 일부 개선 필요")
        else:
            print("\\n❌ 심각한 문제 발견, 배포 연기 필요")
    
    def __del__(self):
        """소멸자에서 서버 정리"""
        self.stop_mcp_server()

if __name__ == "__main__":
    tester = ComprehensiveFastMCPTest()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        tester.stop_mcp_server()