#!/usr/bin/env python3
"""
Semantic validation of Actant Parser
Tests if the parser actually preserves meaning
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from greeum.core.database_manager import DatabaseManager
from greeum.core.actant_parser import ActantParser
from greeum.core.actant_parser_v2 import ImprovedActantParser

def validate_semantic_accuracy():
    """Validate semantic accuracy of parsing"""
    
    print("Semantic Validation of Actant Parser")
    print("=" * 50)
    
    db_manager = DatabaseManager(connection_string="data/test_semantic.db")
    # Test both parsers
    parser_v1 = ActantParser(db_manager)
    parser = ImprovedActantParser(db_manager)
    
    print("\n🆚 Testing IMPROVED Parser (v2):\n")
    
    # Test cases with expected results
    test_cases = [
        {
            "text": "사용자가 버그 수정을 요청했다",
            "expected": {
                "subject": "사용자",
                "action": "요청",
                "object": "버그 수정"  # Should be "버그 수정" not just "수정"
            }
        },
        {
            "text": "Claude가 문제를 해결했고 사용자가 만족했다",
            "expected": [
                {"subject": "Claude", "action": "해결", "object": "문제"},
                {"subject": "사용자", "action": "만족", "object": None}
            ]
        },
        {
            "text": "버그를 수정한 후 배포를 완료했다",
            "expected": [
                {"subject": None, "action": "수정", "object": "버그"},  # Implicit subject
                {"subject": None, "action": "완료", "object": "배포"}
            ]
        },
        {
            "text": "팀이 새로운 기능을 개발했다",
            "expected": {
                "subject": "팀",
                "action": "개발",
                "object": "새로운 기능"  # Should include "새로운"
            }
        },
        {
            "text": "시스템이 오류를 발견했고 개발자가 수정했다",
            "expected": [
                {"subject": "시스템", "action": "발견", "object": "오류"},
                {"subject": "개발자", "action": "수정", "object": "오류"}  # Object should be inferred
            ]
        }
    ]
    
    print("\n🔍 Detailed Semantic Analysis:\n")
    
    total_tests = 0
    passed_tests = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: '{test['text']}'")
        print("-" * 40)
        
        actants = parser.parse(test['text'])
        
        # Check if parsing matches expectations
        if isinstance(test['expected'], list):
            # Multiple expected actants
            for j, expected in enumerate(test['expected']):
                total_tests += 1
                if j < len(actants):
                    actual = actants[j]
                    print(f"\nActant {j+1}:")
                    print(f"  Expected: S={expected.get('subject')}, A={expected.get('action')}, O={expected.get('object')}")
                    print(f"  Actual:   S={actual.subject_raw}, A={actual.action_raw}, O={actual.object_raw}")
                    
                    # Check each component
                    issues = []
                    if expected.get('subject') != actual.subject_raw:
                        issues.append(f"Subject mismatch")
                    if expected.get('action') != actual.action_raw:
                        issues.append(f"Action mismatch")
                    if expected.get('object') != actual.object_raw:
                        issues.append(f"Object mismatch")
                    
                    if issues:
                        print(f"  ❌ FAILED: {', '.join(issues)}")
                    else:
                        print(f"  ✅ PASSED")
                        passed_tests += 1
                else:
                    print(f"\nActant {j+1}: ❌ MISSING")
        else:
            # Single expected actant
            total_tests += 1
            expected = test['expected']
            if actants:
                actual = actants[0]
                print(f"\nExpected: S={expected.get('subject')}, A={expected.get('action')}, O={expected.get('object')}")
                print(f"Actual:   S={actual.subject_raw}, A={actual.action_raw}, O={actual.object_raw}")
                
                issues = []
                if expected.get('subject') != actual.subject_raw:
                    issues.append(f"Subject: expected '{expected.get('subject')}' got '{actual.subject_raw}'")
                if expected.get('action') != actual.action_raw:
                    issues.append(f"Action: expected '{expected.get('action')}' got '{actual.action_raw}'")
                if expected.get('object') != actual.object_raw:
                    issues.append(f"Object: expected '{expected.get('object')}' got '{actual.object_raw}'")
                
                if issues:
                    print(f"❌ FAILED:")
                    for issue in issues:
                        print(f"  - {issue}")
                else:
                    print(f"✅ PASSED")
                    passed_tests += 1
            else:
                print(f"❌ No actants parsed")
        
        print()
    
    # Additional problematic cases
    print("\n" + "=" * 50)
    print("🚨 Known Problematic Cases:\n")
    
    problematic = [
        "프로젝트가 성공해서 팀이 보너스를 받았다",  # Causal relationship
        "사용자의 요청으로 새 기능이 추가되었다",     # Passive voice
        "버그 수정 작업을 완료했습니다",              # Formal ending
        "이슈를 확인하고 해결 방안을 제시했다",       # Multiple objects
        "고객이 제품을 구매하려고 했으나 실패했다",   # Intention + failure
    ]
    
    for text in problematic:
        print(f"Text: '{text}'")
        actants = parser.parse(text)
        for j, actant in enumerate(actants, 1):
            print(f"  Parsed {j}: S={actant.subject_raw}, A={actant.action_raw}, O={actant.object_raw}")
        print(f"  💭 Issues: Likely incorrect parsing\n")
    
    print("=" * 50)
    print(f"\n📊 Accuracy Score: {passed_tests}/{total_tests} ({100*passed_tests/total_tests:.1f}%)")
    
    if passed_tests < total_tests * 0.7:
        print("\n⚠️  WARNING: Parser accuracy is below 70%!")
        print("Major issues identified:")
        print("1. Object extraction is too simplistic (single word)")
        print("2. Multiple clauses not properly separated")
        print("3. Implicit subjects/objects not inferred")
        print("4. Korean particles not properly handled")
    
    # Cleanup
    db_manager.close()
    if os.path.exists("data/test_semantic.db"):
        os.remove("data/test_semantic.db")

if __name__ == "__main__":
    validate_semantic_accuracy()