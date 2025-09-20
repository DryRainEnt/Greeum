
#!/usr/bin/env python3
"""
문서 검증 시스템 테스트
"""

from pathlib import Path

import pytest

from greeum.core.doc_validator import DocumentValidator


def test_doc_validator_handles_sample_markdown(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    sample = docs_dir / "sample.md"
    sample.write_text(
        '''# Sample Documentation

```python
print('hello world')
```

```json
{"status": "ok"}
```
'''
    )

    validator = DocumentValidator(docs_dir=docs_dir)
    examples = validator.extract_examples()
    assert len(examples) == 2

    passed, failed = validator.validate_all()
    assert failed == 0
    assert passed == 2

    report = validator.generate_report()
    assert "Total examples: 2" in report
    assert "✅ Passed" in report


@pytest.mark.parametrize(
    "content, expected_failures",
    [
        ("```json\n{bad json}\n```", 1),
        ("```python\nnot valid python code@@@\n```", 1),
    ],
)
def test_doc_validator_reports_failures(
    tmp_path: Path, content: str, expected_failures: int
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    sample = docs_dir / "sample.md"
    sample.write_text(content)

    validator = DocumentValidator(docs_dir=docs_dir)
    validator.extract_examples()
    passed, failed = validator.validate_all()

    assert failed >= expected_failures
