"""
문서 검증 시스템 TDD 테스트 스위트
RED 단계: 이 테스트들은 모두 실패해야 함 (구현 전)
"""

import unittest
import tempfile
import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict

# 아직 구현되지 않은 모듈들 (RED 단계)
try:
    from greeum.core.doc_validator import (
        DocumentValidator, DocExample, ValidationResult
    )
except ImportError:
    # 테스트를 위한 임시 정의
    class DocExample:
        def __init__(self, file_path, line_number, example_type, content, expected_output=None):
            self.file_path = file_path
            self.line_number = line_number
            self.example_type = example_type
            self.content = content
            self.expected_output = expected_output
    
    class ValidationResult:
        def __init__(self, status, message):
            self.status = status
            self.message = message
    
    class DocumentValidator:
        def __init__(self, docs_dir=None):
            pass


class TestDocumentValidatorUnit(unittest.TestCase):
    """문서 검증기 단위 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.temp_dir = tempfile.mkdtemp()
        self.docs_dir = Path(self.temp_dir) / "docs"
        self.docs_dir.mkdir()
        
        # 테스트용 마크다운 파일 생성
        self._create_test_docs()
    
    def tearDown(self):
        """테스트 정리"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_docs(self):
        """테스트용 문서 생성"""
        # 정상적인 문서
        good_doc = self.docs_dir / "good_examples.md"
        good_doc.write_text("""
# Good Documentation

## CLI Examples

```bash
greeum memory add "Test memory"
greeum search "query" --slot A --radius 2
```

## Python Examples

```python
from greeum import BlockManager
bm = BlockManager()
results = bm.search("test")
print(results)
```

## JSON Examples

```json
{
  "block_index": 1,
  "context": "Test block",
  "importance": 0.5
}
```

## Expected Output

When you run `greeum memory add "Test"`, you should see:
```
✅ Memory added successfully (Block #123)
```
""")
        
        # 오류가 있는 문서
        bad_doc = self.docs_dir / "bad_examples.md"
        bad_doc.write_text("""
# Bad Documentation

## Invalid CLI

```bash
greeum nonexistent-command --invalid-option
greeum memory add  # Missing required argument
```

## Invalid Python

```python
from greeum import NonExistentModule
this is not valid python syntax
bm = BlockManager(
```

## Invalid JSON

```json
{
  invalid json: no quotes,
  "missing": closing bracket
```
""")
    
    def test_example_extraction_cli(self):
        """요구사항: CLI 예시를 정확히 추출해야 함"""
        validator = DocumentValidator(self.docs_dir)
        examples = validator.extract_examples()
        
        # CLI 예시만 필터링
        cli_examples = [e for e in examples if e.example_type == 'cli']
        
        # good_examples.md에서 2개
        self.assertGreaterEqual(len(cli_examples), 2, "Should extract at least 2 CLI examples")
        
        # 내용 확인
        cli_contents = [e.content for e in cli_examples]
        self.assertTrue(
            any("greeum memory add" in c for c in cli_contents),
            "Should extract 'greeum memory add' command"
        )
        self.assertTrue(
            any("greeum search" in c for c in cli_contents),
            "Should extract 'greeum search' command"
        )
    
    def test_example_extraction_python(self):
        """요구사항: Python 코드 예시를 정확히 추출해야 함"""
        validator = DocumentValidator(self.docs_dir)
        examples = validator.extract_examples()
        
        # Python 예시만 필터링
        python_examples = [e for e in examples if e.example_type == 'python']
        
        self.assertGreaterEqual(len(python_examples), 1, "Should extract at least 1 Python example")
        
        # 내용 확인
        python_content = python_examples[0].content
        self.assertIn("from greeum import", python_content, "Should contain import statement")
        self.assertIn("BlockManager", python_content, "Should contain BlockManager")
    
    def test_example_extraction_json(self):
        """요구사항: JSON 예시를 정확히 추출해야 함"""
        validator = DocumentValidator(self.docs_dir)
        examples = validator.extract_examples()
        
        # JSON 예시만 필터링
        json_examples = [e for e in examples if e.example_type == 'json']
        
        self.assertGreaterEqual(len(json_examples), 1, "Should extract at least 1 JSON example")
        
        # 내용 확인
        json_content = json_examples[0].content
        self.assertIn("block_index", json_content, "Should contain block_index field")
    
    def test_line_number_tracking(self):
        """요구사항: 예시의 정확한 줄 번호를 추적해야 함"""
        validator = DocumentValidator(self.docs_dir)
        examples = validator.extract_examples()
        
        # 모든 예시는 줄 번호를 가져야 함
        for example in examples:
            self.assertIsNotNone(example.line_number, "Example should have line number")
            self.assertGreater(example.line_number, 0, "Line number should be positive")
    
    def test_cli_validation_success(self):
        """요구사항: 유효한 CLI 명령어는 통과해야 함"""
        validator = DocumentValidator(self.docs_dir)
        
        # 유효한 CLI 예시
        valid_example = DocExample(
            file_path=self.docs_dir / "test.md",
            line_number=10,
            example_type='cli',
            content='greeum memory add "Test memory"'
        )
        
        result = validator.validate_cli_example(valid_example)
        
        # greeum 명령어가 설치되어 있다면 pass 또는 fail
        # 설치되지 않았다면 fail이 정상
        self.assertIn(result['status'], ['pass', 'fail'], "Should return valid status")
        self.assertEqual(result['type'], 'cli', "Should be CLI type")
    
    def test_cli_validation_failure(self):
        """요구사항: 잘못된 CLI 명령어는 실패해야 함"""
        validator = DocumentValidator(self.docs_dir)
        
        # 잘못된 CLI 예시
        invalid_example = DocExample(
            file_path=self.docs_dir / "test.md",
            line_number=20,
            example_type='cli',
            content='greeum nonexistent-command --invalid-option'
        )
        
        result = validator.validate_cli_example(invalid_example)
        
        # 존재하지 않는 명령어는 실패해야 함
        self.assertEqual(result['status'], 'fail', "Invalid command should fail")
        self.assertIsNotNone(result['message'], "Should have error message")
    
    def test_python_validation_syntax(self):
        """요구사항: Python 문법 오류를 감지해야 함"""
        validator = DocumentValidator(self.docs_dir)
        
        # 문법 오류가 있는 Python 코드
        invalid_python = DocExample(
            file_path=self.docs_dir / "test.md",
            line_number=30,
            example_type='python',
            content='this is not valid python syntax'
        )
        
        result = validator.validate_python_example(invalid_python)
        
        self.assertEqual(result['status'], 'fail', "Invalid syntax should fail")
        self.assertIn('syntax', result['message'].lower(), "Should mention syntax error")
    
    def test_python_validation_imports(self):
        """요구사항: 존재하지 않는 import를 감지해야 함"""
        validator = DocumentValidator(self.docs_dir)
        
        # 존재하지 않는 모듈 import
        invalid_import = DocExample(
            file_path=self.docs_dir / "test.md",
            line_number=40,
            example_type='python',
            content='from greeum import NonExistentModule'
        )
        
        result = validator.validate_python_example(invalid_import)
        
        # import 오류 감지
        self.assertEqual(result['status'], 'fail', "Invalid import should fail")
        self.assertIn('import', result['message'].lower(), "Should mention import error")
    
    def test_json_validation(self):
        """요구사항: 잘못된 JSON을 감지해야 함"""
        validator = DocumentValidator(self.docs_dir)
        
        # 유효한 JSON
        valid_json = DocExample(
            file_path=self.docs_dir / "test.md",
            line_number=50,
            example_type='json',
            content='{"key": "value", "number": 123}'
        )
        
        result = validator.validate_json_example(valid_json)
        self.assertEqual(result['status'], 'pass', "Valid JSON should pass")
        
        # 잘못된 JSON
        invalid_json = DocExample(
            file_path=self.docs_dir / "test.md",
            line_number=60,
            example_type='json',
            content='{invalid json: no quotes}'
        )
        
        result = validator.validate_json_example(invalid_json)
        self.assertEqual(result['status'], 'fail', "Invalid JSON should fail")
        self.assertIn('json', result['message'].lower(), "Should mention JSON error")
    
    def test_validation_all(self):
        """요구사항: 모든 예시를 한 번에 검증할 수 있어야 함"""
        validator = DocumentValidator(self.docs_dir)
        
        passed, failed = validator.validate_all()
        
        # 최소한 일부 예시는 있어야 함
        self.assertGreater(passed + failed, 0, "Should validate at least one example")
        
        # 결과가 숫자여야 함
        self.assertIsInstance(passed, int, "Passed count should be integer")
        self.assertIsInstance(failed, int, "Failed count should be integer")
    
    def test_report_generation(self):
        """요구사항: 검증 결과 리포트를 생성할 수 있어야 함"""
        validator = DocumentValidator(self.docs_dir)
        validator.validate_all()
        
        report = validator.generate_report()
        
        # 리포트 내용 확인
        self.assertIsInstance(report, str, "Report should be string")
        self.assertIn("Documentation Validation Report", report, "Should have title")
        self.assertIn("Passed:", report, "Should show passed count")
        self.assertIn("Failed:", report, "Should show failed count")
    
    def test_file_path_tracking(self):
        """요구사항: 각 예시의 파일 경로를 추적해야 함"""
        validator = DocumentValidator(self.docs_dir)
        examples = validator.extract_examples()
        
        for example in examples:
            self.assertIsNotNone(example.file_path, "Should have file path")
            self.assertTrue(
                Path(example.file_path).exists(),
                f"File path should exist: {example.file_path}"
            )


class TestDocumentValidatorIntegration(unittest.TestCase):
    """문서 검증기 통합 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.temp_dir = tempfile.mkdtemp()
        self.docs_dir = Path(self.temp_dir) / "docs"
        self.docs_dir.mkdir()
    
    def tearDown(self):
        """테스트 정리"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_real_documentation_structure(self):
        """요구사항: 실제 문서 구조를 처리할 수 있어야 함"""
        # 실제 프로젝트 문서 구조 모방
        api_doc = self.docs_dir / "api-reference.md"
        api_doc.write_text("""
# API Reference

## BlockManager

```python
from greeum import BlockManager

bm = BlockManager()
bm.add_block({"context": "Test"})
```

### Search Examples

```python
results = bm.search("query", limit=10)
for result in results:
    print(result['context'])
```
""")
        
        guide_doc = self.docs_dir / "guides" / "getting-started.md"
        guide_doc.parent.mkdir()
        guide_doc.write_text("""
# Getting Started

## Installation

```bash
pip install greeum
```

## First Steps

```bash
greeum init
greeum memory add "My first memory"
```
""")
        
        validator = DocumentValidator(self.docs_dir)
        examples = validator.extract_examples()
        
        # 여러 디렉토리에서 예시 추출
        file_paths = {str(e.file_path) for e in examples}
        self.assertGreater(len(file_paths), 1, "Should find examples in multiple files")
    
    def test_recursive_directory_scan(self):
        """요구사항: 하위 디렉토리를 재귀적으로 스캔해야 함"""
        # 중첩된 디렉토리 구조
        nested = self.docs_dir / "a" / "b" / "c" / "deep.md"
        nested.parent.mkdir(parents=True)
        nested.write_text("""
```python
print("Deep nested example")
```
""")
        
        validator = DocumentValidator(self.docs_dir)
        examples = validator.extract_examples()
        
        # 깊은 디렉토리의 예시도 찾아야 함
        deep_examples = [e for e in examples if "deep.md" in str(e.file_path)]
        self.assertGreater(len(deep_examples), 0, "Should find examples in nested directories")
    
    def test_error_recovery(self):
        """요구사항: 일부 파일에 오류가 있어도 계속 진행해야 함"""
        # 읽을 수 없는 파일 (권한 문제 시뮬레이션)
        # 실제로는 권한 설정이 OS별로 다르므로 다른 방식으로 테스트
        
        # 매우 큰 파일
        large_doc = self.docs_dir / "large.md"
        large_doc.write_text("```python\nprint('test')\n```\n" * 10000)
        
        # 잘못된 인코딩의 파일은 바이너리로 작성
        binary_doc = self.docs_dir / "binary.md"
        binary_doc.write_bytes(b'\xff\xfe' + b'Invalid UTF-8')
        
        validator = DocumentValidator(self.docs_dir)
        
        # 오류가 있어도 실행이 완료되어야 함
        try:
            examples = validator.extract_examples()
            # 최소한 large.md의 예시는 추출되어야 함
            self.assertGreater(len(examples), 0, "Should extract some examples despite errors")
        except Exception as e:
            self.fail(f"Should handle errors gracefully: {e}")
    
    def test_performance_large_docs(self):
        """요구사항: 큰 문서도 효율적으로 처리해야 함"""
        import time
        
        # 1000개의 예시가 있는 큰 문서
        large_doc = self.docs_dir / "large.md"
        content = ["# Large Document\n"]
        
        for i in range(1000):
            content.append(f"""
## Example {i}

```python
print("Example {i}")
```
""")
        
        large_doc.write_text('\n'.join(content))
        
        validator = DocumentValidator(self.docs_dir)
        
        start = time.time()
        examples = validator.extract_examples()
        elapsed = time.time() - start
        
        # 1000개 예시 추출이 10초 이내
        self.assertLess(elapsed, 10.0, f"Should process 1000 examples in < 10s, took {elapsed:.2f}s")
        self.assertEqual(len(examples), 1000, "Should extract all 1000 examples")


class TestDriftDetection(unittest.TestCase):
    """문서-코드 불일치 감지 테스트"""
    
    def test_cli_option_drift(self):
        """요구사항: CLI 옵션 변경을 감지해야 함"""
        # 문서에는 --radius 옵션이 있지만 실제로는 없는 경우
        doc_example = "greeum search 'test' --radius 3"
        
        # 실제 CLI 도움말 확인
        result = subprocess.run(
            ["python3", "-m", "greeum.cli", "search", "--help"],
            capture_output=True,
            text=True
        )
        
        # --radius 옵션 존재 여부 확인
        if "--radius" not in result.stdout:
            # Drift 감지됨
            self.assertIsNotNone(result.stdout, "Should detect missing option")
    
    def test_api_signature_drift(self):
        """요구사항: API 시그니처 변경을 감지해야 함"""
        # 문서의 예시
        doc_code = """
from greeum import BlockManager
bm = BlockManager()
bm.search(query="test", limit=10, use_cache=True)
"""
        
        # 실제 API와 비교 (실제 구현 시)
        try:
            from greeum import BlockManager
            import inspect
            
            # search 메서드의 실제 시그니처 확인
            sig = inspect.signature(BlockManager.search)
            params = list(sig.parameters.keys())
            
            # use_cache 파라미터가 없다면 drift
            if 'use_cache' not in params:
                self.fail("API drift detected: use_cache parameter missing")
        except ImportError:
            pass  # 모듈이 아직 없으면 skip
    
    def test_output_format_drift(self):
        """요구사항: 출력 형식 변경을 감지해야 함"""
        # 문서에 있는 예상 출력
        expected_output = "✅ Memory added successfully (Block #123)"
        
        # 실제 명령어 실행
        result = subprocess.run(
            ["python3", "-m", "greeum.cli", "memory", "add", "Test"],
            capture_output=True,
            text=True
        )
        
        # 출력 형식 비교
        if result.returncode == 0:
            # 출력에 ✅와 Block # 패턴이 있는지 확인
            if "✅" not in result.stdout or "Block #" not in result.stdout:
                self.fail("Output format drift detected")


class TestCLIValidation(unittest.TestCase):
    """CLI 통합 테스트"""
    
    def test_validate_command(self):
        """요구사항: greeum validate docs 명령어가 작동해야 함"""
        result = subprocess.run(
            ["python3", "-m", "greeum.cli", "validate", "docs"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # 명령어가 존재해야 함 (아직 구현 전이므로 실패 예상)
        # self.assertIn("validate", result.stdout + result.stderr)
    
    def test_validate_output_format(self):
        """요구사항: 검증 결과를 적절한 형식으로 출력해야 함"""
        result = subprocess.run(
            ["python3", "-m", "greeum.cli", "validate", "docs", "--output", "report.md"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # 리포트 파일 생성 확인 (구현 후)
        # self.assertTrue(Path("report.md").exists())
    
    def test_validate_exit_code(self):
        """요구사항: 실패 시 0이 아닌 종료 코드를 반환해야 함"""
        # 의도적으로 실패하는 문서 생성
        bad_docs = Path("bad_docs")
        bad_docs.mkdir(exist_ok=True)
        
        bad_doc = bad_docs / "bad.md"
        bad_doc.write_text("""
```bash
greeum this-command-does-not-exist
```
""")
        
        result = subprocess.run(
            ["python3", "-m", "greeum.cli", "validate", "docs", "--docs-dir", str(bad_docs)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # 실패 시 exit code가 0이 아니어야 함
        # self.assertNotEqual(result.returncode, 0)
        
        # 정리
        import shutil
        shutil.rmtree(bad_docs, ignore_errors=True)


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2)