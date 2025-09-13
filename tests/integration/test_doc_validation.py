#!/usr/bin/env python3
"""
문서 검증 시스템 테스트
"""

from pathlib import Path
from greeum.core.doc_validator import DocumentationValidator

def test_doc_validation():
    print("=" * 60)
    print("Documentation Validation Test")
    print("=" * 60)
    
    # 검증기 초기화
    validator = DocumentationValidator(project_root=Path.cwd())
    
    # 검증 실행
    print("\n🔍 Running validation...")
    result = validator.validate_all()
    
    # 결과 출력
    print(f"\n📊 Overall Status: {'✅ VALID' if result.valid else '❌ INVALID'}")
    print(f"📈 Documentation Coverage: {result.coverage:.1%}")
    
    # 통계 출력
    print("\n📋 Statistics:")
    stats = validator.stats
    print(f"  Modules: {stats['documented_modules']}/{stats['total_modules']}")
    print(f"  Classes: {stats['documented_classes']}/{stats['total_classes']}")
    print(f"  Functions: {stats['documented_functions']}/{stats['total_functions']}")
    
    # 오류 출력 (처음 5개만)
    if result.errors:
        print(f"\n❌ Errors ({len(result.errors)}):")
        for error in result.errors[:5]:
            print(f"  - {error}")
        if len(result.errors) > 5:
            print(f"  ... and {len(result.errors) - 5} more")
    
    # 경고 출력 (처음 10개만)
    if result.warnings:
        print(f"\n⚠️ Warnings ({len(result.warnings)}):")
        for warning in result.warnings[:10]:
            print(f"  - {warning}")
        if len(result.warnings) > 10:
            print(f"  ... and {len(result.warnings) - 10} more")
    
    # 제안 출력 (처음 5개만)
    if result.suggestions:
        print(f"\n💡 Suggestions ({len(result.suggestions)}):")
        for suggestion in result.suggestions[:5]:
            print(f"  - {suggestion}")
    
    # 보고서 생성
    print("\n📝 Generating report...")
    report_path = Path("doc_validation_report.txt")
    report = validator.generate_report(report_path)
    print(f"✅ Report saved to: {report_path}")
    
    return result.valid

if __name__ == "__main__":
    is_valid = test_doc_validation()
    exit(0 if is_valid else 1)