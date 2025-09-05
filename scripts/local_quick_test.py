#!/usr/bin/env python3
"""
로컬 빠른 테스트 스크립트
- GitHub Actions와 동일한 검증을 로컬에서 빠르게 실행
- 30초 이내 결과 확인 가능
- CI/CD 파이프라인 실행 전 사전 검증용
"""

import sys
import time
import subprocess
import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager


class LocalQuickTest:
    """로컬 빠른 테스트 실행기"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = {}
        self.start_time = time.time()
        
    @contextmanager
    def test_phase(self, phase_name: str, target_seconds: int):
        """테스트 단계 실행 및 시간 측정"""
        print(f"\n{'='*50}")
        print(f"🔍 {phase_name} (목표: {target_seconds}초 이내)")
        print(f"{'='*50}")
        
        phase_start = time.time()
        success = True
        error_msg = None
        
        try:
            yield
        except Exception as e:
            success = False
            error_msg = str(e)
            print(f"❌ 오류: {e}")
        finally:
            phase_duration = time.time() - phase_start
            status = "✅ PASS" if success else "❌ FAIL"
            
            self.test_results[phase_name] = {
                "success": success,
                "duration": round(phase_duration, 1),
                "target": target_seconds,
                "error": error_msg
            }
            
            print(f"\n{status} {phase_name}: {phase_duration:.1f}초")
            if phase_duration > target_seconds:
                print(f"⚠️  목표 시간 {target_seconds}초 초과")
    
    def quick_syntax_check(self):
        """구문 검사 (5초 목표)"""
        with self.test_phase("Syntax Check", 5):
            key_files = [
                "greeum/__init__.py",
                "greeum/core/__init__.py", 
                "greeum/core/block_manager.py",
                "greeum/core/database_manager.py",
                "greeum/mcp/claude_code_mcp_server.py",
                "greeum/text_utils.py",
                "greeum/embedding_models.py"
            ]
            
            for file_path in key_files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    result = subprocess.run([
                        sys.executable, "-m", "py_compile", str(full_path)
                    ], capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        raise Exception(f"구문 오류: {file_path}\n{result.stderr}")
                    print(f"  ✓ {file_path}")
                else:
                    print(f"  ⚠️  파일 없음: {file_path}")
    
    def quick_import_test(self):
        """임포트 테스트 (5초 목표)"""
        with self.test_phase("Import Test", 5):
            import_tests = [
                ("import greeum", "기본 모듈"),
                ("from greeum.core import BlockManager, DatabaseManager", "핵심 클래스"),
                ("from greeum.text_utils import process_user_input", "텍스트 처리"),
                ("from greeum.embedding_models import get_embedding", "임베딩"),
                ("from greeum.mcp import claude_code_mcp_server", "MCP 서버")
            ]
            
            for import_code, description in import_tests:
                try:
                    result = subprocess.run([
                        sys.executable, "-c", import_code
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode != 0:
                        raise Exception(f"{description} 임포트 실패:\n{result.stderr}")
                    print(f"  ✓ {description}")
                except subprocess.TimeoutExpired:
                    raise Exception(f"{description} 임포트 타임아웃")
    
    def quick_function_test(self):
        """기본 기능 테스트 (10초 목표)"""
        with self.test_phase("Basic Function Test", 10):
            # 텍스트 처리 테스트
            test_code = '''
import sys
sys.path.insert(0, ".")

from greeum.text_utils import process_user_input

# 한글 텍스트 처리
result1 = process_user_input("안녕하세요 테스트입니다")
assert "keywords" in result1, "키워드 필드 없음"
assert "embedding" in result1, "임베딩 필드 없음"
print("✓ 한글 텍스트 처리")

# 영어 텍스트 처리
result2 = process_user_input("Hello world test")
assert "keywords" in result2, "키워드 필드 없음"
assert "embedding" in result2, "임베딩 필드 없음"
print("✓ 영어 텍스트 처리")

# 복합 텍스트 처리
result3 = process_user_input("복합 텍스트 Mixed language test 123")
assert "keywords" in result3, "키워드 필드 없음"
assert "embedding" in result3, "임베딩 필드 없음"
print("✓ 복합 텍스트 처리")

print("모든 기본 기능 테스트 통과")
'''
            
            result = subprocess.run([
                sys.executable, "-c", test_code
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                raise Exception(f"기능 테스트 실패:\n{result.stderr}")
            
            print("  ✓ 텍스트 처리 기능")
            print("  ✓ 키워드 추출")
            print("  ✓ 임베딩 생성")
    
    def quick_database_test(self):
        """데이터베이스 테스트 (10초 목표)"""
        with self.test_phase("Database Test", 10):
            test_code = '''
import sys
import tempfile
import shutil
from pathlib import Path
sys.path.insert(0, ".")

from greeum.core.database_manager import DatabaseManager
from greeum.text_utils import process_user_input

# 임시 데이터베이스
test_dir = Path(tempfile.mkdtemp())
db_path = test_dir / "test.db"

try:
    db = DatabaseManager(str(db_path))
    
    # 블록 추가 테스트
    content = "데이터베이스 테스트용 콘텐츠"
    result = process_user_input(content)
    
    block_data = {
        "block_index": 0,
        "timestamp": "2025-07-30T12:00:00",
        "context": content,
        "keywords": result.get("keywords", []),
        "tags": result.get("tags", []),
        "embedding": result.get("embedding", []),
        "importance": 0.5,
        "hash": "test_hash",
        "prev_hash": ""
    }
    
    db.add_block(block_data)
    print("✓ 블록 추가")
    
    # 블록 조회 테스트
    retrieved = db.get_block(0)
    assert retrieved is not None, "블록 조회 실패"
    assert retrieved["context"] == content, "블록 내용 불일치"
    print("✓ 블록 조회")
    
    # 키워드 검색 테스트
    search_results = db.search_blocks_by_keyword(["테스트"], limit=5)
    assert len(search_results) > 0, "키워드 검색 실패"
    print("✓ 키워드 검색")
    
    # 마지막 블록 정보
    last_info = db.get_last_block_info()
    assert last_info is not None, "마지막 블록 정보 조회 실패"
    print("✓ 마지막 블록 정보")
    
    print("모든 데이터베이스 테스트 통과")
    
finally:
    shutil.rmtree(test_dir)
'''
            
            result = subprocess.run([
                sys.executable, "-c", test_code
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                raise Exception(f"데이터베이스 테스트 실패:\n{result.stderr}")
            
            print("  ✓ SQLite 데이터베이스")
            print("  ✓ 블록 추가/조회")
            print("  ✓ 키워드 검색")
    
    def quick_security_check(self):
        """보안 빠른 체크 (5초 목표)"""
        with self.test_phase("Security Quick Check", 5):
            # 기본적인 보안 패턴 체크
            security_patterns = [
                ("eval(", "eval() 사용 금지"),
                ("exec(", "exec() 사용 금지"),
                ("__import__", "동적 import 주의"),
                ("subprocess.call", "subprocess.call 대신 subprocess.run 사용"),
                ("shell=True", "shell=True 사용 주의")
            ]
            
            python_files = list(self.project_root.rglob("*.py"))
            issues = []
            
            for py_file in python_files:
                if "test" in str(py_file) or ".git" in str(py_file):
                    continue
                    
                try:
                    content = py_file.read_text(encoding='utf-8')
                    for pattern, warning in security_patterns:
                        if pattern in content:
                            issues.append(f"{py_file.name}: {warning}")
                except Exception:
                    continue
            
            if issues:
                print("  ⚠️  보안 주의사항:")
                for issue in issues[:5]:  # 최대 5개만 표시
                    print(f"    - {issue}")
            else:
                print("  ✓ 기본 보안 패턴 검사 통과")
    
    def performance_quick_check(self):
        """성능 빠른 체크 (10초 목표)"""
        with self.test_phase("Performance Quick Check", 10):
            test_code = '''
import sys
import time
sys.path.insert(0, ".")

from greeum.text_utils import process_user_input

# 성능 측정
operations = 20  # 빠른 테스트용
start_time = time.time()

for i in range(operations):
    content = f"성능 테스트 {i}번째 텍스트 처리입니다. 한글과 영어가 포함되어 있습니다."
    result = process_user_input(content)

duration = time.time() - start_time
avg_ms = (duration / operations) * 1000

print(f"✓ {operations}개 처리: {duration:.2f}초")
print(f"✓ 평균 처리 시간: {avg_ms:.1f}ms")

# 성능 기준 체크 (1개당 100ms 이내)
if avg_ms > 100:
    print(f"⚠️  성능 기준 초과: {avg_ms:.1f}ms > 100ms")
    exit(1)
else:
    print("✓ 성능 기준 만족")
'''
            
            result = subprocess.run([
                sys.executable, "-c", test_code
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                raise Exception(f"성능 테스트 실패:\n{result.stderr}")
            
            # 출력에서 성능 정보 추출
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines:
                if "처리:" in line or "평균" in line or "기준" in line:
                    print(f"  {line}")
    
    def run_all_quick_tests(self):
        """모든 빠른 테스트 실행"""
        print("🚀 Greeum Local Quick Test 시작")
        print(f"프로젝트: {self.project_root}")
        print(f"Python: {sys.version.split()[0]}")
        
        # 모든 테스트 실행
        self.quick_syntax_check()
        self.quick_import_test()
        self.quick_function_test()
        self.quick_database_test()
        self.quick_security_check()
        self.performance_quick_check()
        
        # 최종 리포트
        self.generate_final_report()
    
    def generate_final_report(self):
        """최종 리포트 생성"""
        total_duration = time.time() - self.start_time
        
        print(f"\n{'='*60}")
        print("📊 최종 테스트 결과")
        print(f"{'='*60}")
        
        passed = 0
        failed = 0
        total_target = 0
        
        for phase_name, result_data in self.test_results.items():
            status = "✅ PASS" if result_data["success"] else "❌ FAIL"
            duration = result_data["duration"]
            target = result_data["target"]
            over_time = f" (목표 +{duration-target:.1f}초)" if duration > target else ""
            
            print(f"{status} {phase_name:25} {duration:5.1f}초{over_time}")
            
            if result_data["success"]:
                passed += 1
            else:
                failed += 1
                if result_data["error"]:
                    print(f"     오류: {result_data['error']}")
            
            total_target += target
        
        print(f"\n📈 요약:")
        print(f"   전체 소요시간: {total_duration:.1f}초 (목표: {total_target}초)")
        print(f"   통과: {passed}개")
        print(f"   실패: {failed}개")
        
        if failed == 0:
            print(f"\n🎉 모든 테스트 통과! GitHub Actions 실행 준비 완료")
            return True
        else:
            print(f"\n🚨 {failed}개 테스트 실패. 수정 후 재실행 필요")
            return False


def main():
    """메인 실행 함수"""
    tester = LocalQuickTest()
    success = tester.run_all_quick_tests()
    
    if success:
        print("\n💡 다음 단계:")
        print("   1. git add . && git commit -m 'your message'")
        print("   2. git push (GitHub Actions가 자동 실행됩니다)")
        print("   3. 또는 GitHub에서 'Fast Feedback Loop' 워크플로우 수동 실행")
    else:
        print("\n💡 수정 가이드:")
        print("   1. 실패한 테스트의 오류 메시지 확인")
        print("   2. 해당 코드 수정")
        print("   3. 다시 이 스크립트 실행: python scripts/local_quick_test.py")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()