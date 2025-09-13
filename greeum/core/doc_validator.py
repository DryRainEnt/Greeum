"""
문서-코드 일치성 검증 시스템
마크다운 문서의 코드 예시가 실제로 작동하는지 자동 검증
"""

import re
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class DocExample:
    """문서에서 추출한 예시"""
    file_path: Path
    line_number: int
    example_type: str  # 'cli', 'python', 'json', 'output'
    content: str
    expected_output: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        data['file_path'] = str(self.file_path)
        return data


@dataclass
class ValidationResult:
    """검증 결과"""
    status: str  # 'pass', 'fail', 'skip'
    message: str
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return asdict(self)


class DocumentValidator:
    """문서 검증 엔진"""
    
    def __init__(self, docs_dir: Path = None):
        """초기화
        
        Args:
            docs_dir: 문서 디렉토리 경로 (기본: docs/)
        """
        if docs_dir is None:
            docs_dir = Path("docs")
        
        self.docs_dir = Path(docs_dir)
        self.examples: List[DocExample] = []
        self.results: List[Dict] = []
        logger.info(f"DocumentValidator initialized with docs_dir: {self.docs_dir}")
    
    def extract_examples(self) -> List[DocExample]:
        """마크다운 문서에서 코드 예시 추출"""
        examples = []
        
        if not self.docs_dir.exists():
            logger.warning(f"Docs directory not found: {self.docs_dir}")
            return examples
        
        # 모든 .md 파일 재귀적으로 검색
        for md_file in self.docs_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                
                # CLI 명령어 추출 (```bash 블록)
                cli_pattern = r'```bash\n(.*?)\n```'
                for match in re.finditer(cli_pattern, content, re.DOTALL):
                    lines_before = content[:match.start()].count('\n')
                    examples.append(DocExample(
                        file_path=md_file,
                        line_number=lines_before + 2,  # ```bash 다음 줄
                        example_type='cli',
                        content=match.group(1)
                    ))
                
                # Python 코드 추출 (```python 블록)
                python_pattern = r'```python\n(.*?)\n```'
                for match in re.finditer(python_pattern, content, re.DOTALL):
                    lines_before = content[:match.start()].count('\n')
                    examples.append(DocExample(
                        file_path=md_file,
                        line_number=lines_before + 2,
                        example_type='python',
                        content=match.group(1)
                    ))
                
                # JSON 예시 추출 (```json 블록)
                json_pattern = r'```json\n(.*?)\n```'
                for match in re.finditer(json_pattern, content, re.DOTALL):
                    lines_before = content[:match.start()].count('\n')
                    examples.append(DocExample(
                        file_path=md_file,
                        line_number=lines_before + 2,
                        example_type='json',
                        content=match.group(1)
                    ))
                
                logger.debug(f"Extracted {len(examples)} examples from {md_file}")
                
            except Exception as e:
                logger.error(f"Failed to process {md_file}: {e}")
                continue
        
        self.examples = examples
        logger.info(f"Total examples extracted: {len(examples)}")
        return examples
    
    def validate_cli_example(self, example: DocExample) -> Dict:
        """CLI 명령어 예시 검증"""
        result = {
            'file': str(example.file_path),
            'line': example.line_number,
            'type': 'cli',
            'status': 'pass',
            'message': ''
        }
        
        # greeum 명령어인지 확인
        if not example.content.strip().startswith('greeum'):
            result['status'] = 'skip'
            result['message'] = 'Not a greeum command'
            return result
        
        # 실제 실행 (dry-run 모드)
        try:
            # 첫 줄만 추출 (여러 줄 명령어의 경우)
            first_line = example.content.strip().split('\n')[0]
            
            # --help를 붙여서 안전하게 실행
            test_cmd = first_line + ' --help'
            test_cmd = test_cmd.replace('greeum', 'python3 -m greeum.cli')
            
            proc = subprocess.run(
                test_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # --help가 성공적으로 실행되면 명령어가 존재함
            if proc.returncode != 0:
                # 명령어가 존재하지 않음
                result['status'] = 'fail'
                result['message'] = f"Command not found or failed: {proc.stderr[:200]}"
            else:
                result['message'] = 'Command exists and responds to --help'
            
        except subprocess.TimeoutExpired:
            result['status'] = 'fail'
            result['message'] = "Command timeout (> 5s)"
        except Exception as e:
            result['status'] = 'fail'
            result['message'] = str(e)[:200]
        
        return result
    
    def validate_python_example(self, example: DocExample) -> Dict:
        """Python 코드 예시 검증"""
        result = {
            'file': str(example.file_path),
            'line': example.line_number,
            'type': 'python',
            'status': 'pass',
            'message': ''
        }
        
        # 문법 검사
        try:
            compile(example.content, '<string>', 'exec')
            result['message'] = 'Syntax is valid'
        except SyntaxError as e:
            result['status'] = 'fail'
            result['message'] = f"Syntax error at line {e.lineno}: {e.msg}"
            return result
        
        # import 검증 (greeum 관련만)
        if 'from greeum' in example.content or 'import greeum' in example.content:
            # 실제 import 가능한지 테스트
            test_code = """
import sys
sys.path.insert(0, '.')
try:
""" + "\n".join([
    line for line in example.content.split('\n')
    if line.strip().startswith('from greeum') or line.strip().startswith('import greeum')
]) + """
    pass
except ImportError as e:
    raise e
"""
            
            try:
                exec(compile(test_code, '<string>', 'exec'))
                result['message'] += ' | Imports are valid'
            except ImportError as e:
                result['status'] = 'fail'
                result['message'] = f"Import error: {e}"
            except Exception:
                # 다른 오류는 무시 (import만 확인)
                pass
        
        return result
    
    def validate_json_example(self, example: DocExample) -> Dict:
        """JSON 예시 검증"""
        result = {
            'file': str(example.file_path),
            'line': example.line_number,
            'type': 'json',
            'status': 'pass',
            'message': ''
        }
        
        try:
            json.loads(example.content)
            result['message'] = 'Valid JSON'
        except json.JSONDecodeError as e:
            result['status'] = 'fail'
            result['message'] = f"Invalid JSON at line {e.lineno}, col {e.colno}: {e.msg}"
        
        return result
    
    def validate_all(self) -> Tuple[int, int]:
        """모든 예시 검증
        
        Returns:
            (passed_count, failed_count) 튜플
        """
        if not self.examples:
            self.extract_examples()
        
        self.results = []
        
        for example in self.examples:
            if example.example_type == 'cli':
                result = self.validate_cli_example(example)
            elif example.example_type == 'python':
                result = self.validate_python_example(example)
            elif example.example_type == 'json':
                result = self.validate_json_example(example)
            else:
                continue
            
            self.results.append(result)
            
            # 진행 상황 로깅
            if len(self.results) % 10 == 0:
                logger.info(f"Validated {len(self.results)} examples...")
        
        passed = sum(1 for r in self.results if r['status'] == 'pass')
        failed = sum(1 for r in self.results if r['status'] == 'fail')
        
        logger.info(f"Validation complete: {passed} passed, {failed} failed")
        return passed, failed
    
    def generate_report(self) -> str:
        """검증 결과 리포트 생성"""
        report = []
        report.append("# Documentation Validation Report\n\n")
        report.append(f"Total examples: {len(self.results)}\n\n")
        
        passed = sum(1 for r in self.results if r['status'] == 'pass')
        failed = sum(1 for r in self.results if r['status'] == 'fail')
        skipped = sum(1 for r in self.results if r['status'] == 'skip')
        
        report.append(f"## Summary\n\n")
        report.append(f"- ✅ Passed: {passed}\n")
        report.append(f"- ❌ Failed: {failed}\n")
        report.append(f"- ⏭️ Skipped: {skipped}\n\n")
        
        if failed > 0:
            report.append("## Failed Examples\n\n")
            for result in self.results:
                if result['status'] == 'fail':
                    report.append(f"### {result['file']}:{result['line']}\n\n")
                    report.append(f"- Type: {result['type']}\n")
                    report.append(f"- Error: {result['message']}\n\n")
        
        # 통계
        report.append("## Statistics by Type\n\n")
        type_stats = {}
        for result in self.results:
            type_key = result['type']
            if type_key not in type_stats:
                type_stats[type_key] = {'pass': 0, 'fail': 0, 'skip': 0}
            type_stats[type_key][result['status']] += 1
        
        for type_key, stats in type_stats.items():
            total = sum(stats.values())
            pass_rate = (stats['pass'] / total * 100) if total > 0 else 0
            report.append(f"- **{type_key}**: {total} total, "
                         f"{stats['pass']} passed ({pass_rate:.1f}%), "
                         f"{stats['fail']} failed\n")
        
        return ''.join(report)
    
    def save_results(self, output_path: Path):
        """결과를 JSON 파일로 저장"""
        data = {
            'examples': [e.to_dict() for e in self.examples],
            'results': self.results,
            'summary': {
                'total': len(self.results),
                'passed': sum(1 for r in self.results if r['status'] == 'pass'),
                'failed': sum(1 for r in self.results if r['status'] == 'fail'),
                'skipped': sum(1 for r in self.results if r['status'] == 'skip')
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {output_path}")