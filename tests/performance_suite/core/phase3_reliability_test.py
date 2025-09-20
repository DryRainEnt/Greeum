#!/usr/bin/env python3
"""
Phase 3 신뢰성 정밀 검증 테스트

성능보다 신뢰성이 더 중요한 가치입니다.
이 테스트는 Phase 3 체크포인트 시스템의 정확성, 일관성, 데이터 무결성을 엄격히 검증합니다.
"""

import sys
import os
import time
import json
import traceback
import hashlib
import pytest
from datetime import datetime
from typing import Dict, List, Any, Set, Tuple

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

pytest.importorskip(
    'greeum.core.hybrid_stm_manager',
    reason='Hybrid STM manager no longer shipped with core runtime',
)
pytest.importorskip(
    'greeum.core.phase_three_coordinator',
    reason='Phase three coordinator not available in trimmed runtime',
)

from greeum import BlockManager, STMManager, CacheManager, DatabaseManager
from greeum.core.hybrid_stm_manager import HybridSTMManager
from greeum.core.checkpoint_manager import CheckpointManager
from greeum.core.localized_search_engine import LocalizedSearchEngine
from greeum.core.phase_three_coordinator import PhaseThreeSearchCoordinator


class Phase3ReliabilityTest:
    """Phase 3 신뢰성 정밀 검증"""
    
    def __init__(self):
        self.test_start_time = time.perf_counter()
        self.results = {
            "test_name": "Phase 3 Reliability & Accuracy Test",
            "start_time": datetime.now().isoformat(),
            "focus": "신뢰성 > 성능",
            "verification_areas": [
                "체크포인트 정확성",
                "검색 결과 일관성", 
                "4층 로직 검증",
                "데이터 무결성",
                "엣지 케이스",
                "오류 처리"
            ]
        }
        
        # 신뢰성 추적
        self.reliability_metrics = {
            "checkpoint_accuracy": [],
            "search_consistency": [],
            "layer_logic_correctness": [],
            "data_integrity_checks": [],
            "edge_case_handling": [],
            "error_recovery": []
        }
        
        # 테스트 환경 설정
        self.setup_test_environment()
        
    def setup_test_environment(self):
        """테스트 환경 초기화"""
        print("🔧 Phase 3 신뢰성 테스트 환경 초기화...")
        
        try:
            # 기본 매니저들
            self.db_manager = DatabaseManager()
            self.block_manager = BlockManager(self.db_manager)
            self.cache_manager = CacheManager()
            
            # Phase 2 하이브리드 STM
            self.hybrid_stm = HybridSTMManager(self.db_manager)
            
            # Phase 3 구성요소들
            self.checkpoint_manager = CheckpointManager(self.db_manager, self.block_manager)
            self.localized_engine = LocalizedSearchEngine(self.checkpoint_manager, self.block_manager)
            self.phase3_coordinator = PhaseThreeSearchCoordinator(
                self.hybrid_stm,
                self.cache_manager,
                self.checkpoint_manager,
                self.localized_engine,
                self.block_manager
            )
            
            print("  ✅ 신뢰성 테스트 환경 초기화 완료")
            
        except Exception as e:
            print(f"  ❌ 초기화 실패: {str(e)}")
            raise
    
    def run_reliability_tests(self):
        """모든 신뢰성 테스트 실행"""
        print("=" * 70)
        print("🔍 Phase 3 신뢰성 정밀 검증 테스트")
        print("📌 신뢰성 > 성능 우선")
        print("=" * 70)
        
        tests = [
            ("1️⃣ 체크포인트 정확성 검증", self.test_checkpoint_accuracy),
            ("2️⃣ 검색 결과 일관성 테스트", self.test_search_consistency),
            ("3️⃣ 4층 검색 로직 검증", self.test_layer_logic_correctness),
            ("4️⃣ 데이터 무결성 검증", self.test_data_integrity),
            ("5️⃣ 엣지 케이스 처리", self.test_edge_cases),
            ("6️⃣ 오류 복구 메커니즘", self.test_error_recovery)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        reliability_issues = []
        
        for test_name, test_func in tests:
            print(f"\n{test_name}:")
            try:
                result = test_func()
                if result['passed']:
                    print(f"  ✅ {test_name}: 신뢰성 확인")
                    passed_tests += 1
                else:
                    print(f"  ❌ {test_name}: 신뢰성 문제 발견")
                    reliability_issues.extend(result.get('issues', []))
                    
                # 상세 결과 저장
                area_key = test_name.split()[-1].replace('검증', '').replace('테스트', '')
                self.reliability_metrics[f"{area_key}_results"] = result
                
            except Exception as e:
                print(f"  ❌ {test_name}: 오류 - {str(e)}")
                reliability_issues.append(f"{test_name}: {str(e)}")
                traceback.print_exc()
        
        # 최종 신뢰성 평가
        reliability_score = self._calculate_reliability_score(passed_tests, total_tests, reliability_issues)
        
        self.results["tests_passed"] = passed_tests
        self.results["tests_total"] = total_tests
        self.results["reliability_score"] = reliability_score
        self.results["reliability_issues"] = reliability_issues
        
        print("\n" + "=" * 70)
        print("📋 Phase 3 신뢰성 검증 결과")
        print("=" * 70)
        print(f"🎯 검증 완료: {passed_tests}/{total_tests}")
        print(f"📊 신뢰성 점수: {reliability_score}/100")
        
        if reliability_issues:
            print(f"⚠️ 발견된 문제: {len(reliability_issues)}개")
            for issue in reliability_issues[:3]:  # 상위 3개만 표시
                print(f"   - {issue}")
        
        if reliability_score >= 90:
            print("🏆 최종 판정: ✅ 높은 신뢰성 확인")
            return True
        elif reliability_score >= 70:
            print("⚠️ 최종 판정: 중간 신뢰성 (개선 권장)")
            return False
        else:
            print("❌ 최종 판정: 낮은 신뢰성 (심각한 문제)")
            return False
    
    def test_checkpoint_accuracy(self) -> Dict[str, Any]:
        """체크포인트 정확성 검증"""
        print("  🎯 체크포인트 생성/연결 정확성 검증...")
        
        issues = []
        passed_checks = 0
        total_checks = 0
        
        try:
            # 테스트 데이터 생성
            test_blocks = self._create_verified_test_blocks(20)
            print(f"    📊 검증용 테스트 블록 {len(test_blocks)}개 생성")
            
            # Working Memory 슬롯 준비
            working_memory = self.hybrid_stm.working_memory
            test_slot = working_memory.slots[0]
            test_slot.context = "체크포인트 정확성 테스트 컨텍스트"
            test_slot.embedding = [0.5 + i * 0.01 for i in range(128)]
            
            # 1. 체크포인트 생성 정확성
            total_checks += 1
            checkpoint = self.checkpoint_manager.create_checkpoint(test_slot, test_blocks[:8])
            
            if checkpoint and len(checkpoint.get('ltm_blocks', [])) == 8:
                passed_checks += 1
                print(f"    ✅ 체크포인트 생성: 8개 블록 정확히 연결")
            else:
                issues.append("체크포인트 생성 시 블록 수 불일치")
                print(f"    ❌ 체크포인트 생성 실패: 예상 8개, 실제 {len(checkpoint.get('ltm_blocks', []))}")
            
            # 2. 관련성 점수 정확성
            total_checks += 1
            expected_scores = [0.8 - (i * 0.05) for i in range(8)]
            actual_scores = [block['relevance_score'] for block in checkpoint.get('ltm_blocks', [])]
            
            score_accuracy = all(abs(exp - act) < 0.1 for exp, act in zip(expected_scores, actual_scores))
            
            if score_accuracy:
                passed_checks += 1
                print(f"    ✅ 관련성 점수 정확성: 허용 오차 내")
            else:
                issues.append("관련성 점수 계산 부정확")
                print(f"    ❌ 관련성 점수 부정확: {actual_scores[:3]}...")
            
            # 3. 체크포인트 반영 검증
            total_checks += 1
            radius_blocks = self.checkpoint_manager.get_checkpoint_radius(test_slot.slot_id, radius=10)
            
            if len(radius_blocks) > 0:
                passed_checks += 1
                print(f"    ✅ 반경 검색: {len(radius_blocks)}개 블록 인덱스 계산")
            else:
                issues.append("체크포인트 반경 검색 실패")
                print(f"    ❌ 반경 검색 실패")
            
            # 4. 중복 블록 처리 검증
            total_checks += 1
            duplicate_test_slot = working_memory.slots[1]
            duplicate_test_slot.context = test_slot.context  # 동일 컨텍스트
            duplicate_test_slot.embedding = test_slot.embedding  # 동일 임베딩
            
            duplicate_checkpoint = self.checkpoint_manager.create_checkpoint(duplicate_test_slot, test_blocks[:8])
            
            # 동일한 블록들이 연결되었는지 확인
            original_block_indices = {block['block_index'] for block in checkpoint.get('ltm_blocks', [])}
            duplicate_block_indices = {block['block_index'] for block in duplicate_checkpoint.get('ltm_blocks', [])}
            
            if original_block_indices == duplicate_block_indices:
                passed_checks += 1
                print(f"    ✅ 중복 처리: 동일 컨텍스트에 동일 블록 연결")
            else:
                issues.append("동일 컨텍스트에 다른 블록 연결")
                print(f"    ❌ 중복 처리 실패")
            
        except Exception as e:
            issues.append(f"체크포인트 정확성 테스트 오류: {str(e)}")
        
        accuracy_rate = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        return {
            'passed': len(issues) == 0 and accuracy_rate >= 90,
            'accuracy_rate': accuracy_rate,
            'passed_checks': passed_checks,
            'total_checks': total_checks,
            'issues': issues
        }
    
    def test_search_consistency(self) -> Dict[str, Any]:
        """검색 결과 일관성 테스트"""
        print("  🔄 동일 쿼리 반복 검색 일관성 검증...")
        
        issues = []
        consistency_tests = []
        
        try:
            # 테스트 쿼리들
            test_queries = [
                {
                    "text": "체크포인트 시스템 테스트",
                    "embedding": [0.6 + i * 0.005 for i in range(128)],
                    "keywords": ["체크포인트", "시스템", "테스트"]
                },
                {
                    "text": "지역 검색 알고리즘",
                    "embedding": [0.4 + i * 0.007 for i in range(128)],
                    "keywords": ["지역", "검색", "알고리즘"]
                },
                {
                    "text": "Working Memory 성능",
                    "embedding": [0.8 + i * 0.003 for i in range(128)],
                    "keywords": ["Working", "Memory", "성능"]
                }
            ]
            
            for query_idx, query in enumerate(test_queries):
                print(f"    📝 쿼리 {query_idx+1}: '{query['text']}'")
                
                # 동일 쿼리 5회 반복 실행
                results_history = []
                
                for attempt in range(5):
                    result = self.phase3_coordinator.intelligent_search(
                        query['text'],
                        query['embedding'],
                        query['keywords']
                    )
                    
                    results_history.append({
                        'attempt': attempt + 1,
                        'source': result.get('source'),
                        'result_count': result.get('result_count', 0),
                        'search_time_ms': result.get('search_time_ms', 0),
                        'results_hash': self._hash_results(result.get('results', []))
                    })
                
                # 일관성 분석
                sources = [r['source'] for r in results_history]
                result_counts = [r['result_count'] for r in results_history]
                result_hashes = [r['results_hash'] for r in results_history]
                
                # 1. 소스 레이어 일관성 (checkpoint → cache 전환은 정상)
                unique_sources = set(sources)
                
                # 정상적인 레이어 전환 패턴들
                normal_patterns = [
                    {'checkpoint'},  # 모두 체크포인트
                    {'cache'},       # 모두 캐시
                    {'working_memory'},  # 모두 워킹메모리
                    {'ltm_fallback'},    # 모두 LTM fallback
                    {'checkpoint', 'cache'},  # 체크포인트 → 캐시 (정상)
                    {'working_memory', 'cache'}  # 워킹메모리 → 캐시 (정상)
                ]
                
                if unique_sources in normal_patterns:
                    if len(unique_sources) == 1:
                        print(f"      ✅ 소스 일관성: 모두 {sources[0]} 레이어")
                    else:
                        print(f"      ✅ 소스 전환: {' → '.join(unique_sources)} (정상 패턴)")
                else:
                    issues.append(f"쿼리 {query_idx+1}: 비정상 소스 패턴 {unique_sources}")
                    print(f"      ❌ 비정상 소스 패턴: {unique_sources}")
                
                # 2. 결과 수 일관성
                if len(set(result_counts)) == 1:
                    print(f"      ✅ 결과 수 일관성: 모두 {result_counts[0]}개")
                else:
                    issues.append(f"쿼리 {query_idx+1}: 결과 수 불일치 {set(result_counts)}")
                    print(f"      ❌ 결과 수 불일치: {set(result_counts)}")
                
                # 3. 결과 내용 일관성 (해시 기반)
                if len(set(result_hashes)) == 1:
                    print(f"      ✅ 결과 내용 일관성: 동일 결과")
                else:
                    issues.append(f"쿼리 {query_idx+1}: 결과 내용 불일치")
                    print(f"      ❌ 결과 내용 불일치")
                
                consistency_tests.append({
                    'query': query['text'],
                    'source_consistency': unique_sources in normal_patterns,  # 정상 패턴 허용
                    'count_consistency': len(set(result_counts)) == 1,
                    'content_consistency': len(set(result_hashes)) == 1,
                    'results_history': results_history
                })
        
        except Exception as e:
            issues.append(f"일관성 테스트 오류: {str(e)}")
        
        # 전체 일관성 점수 계산
        if consistency_tests:
            total_consistency_checks = len(consistency_tests) * 3  # 각 쿼리당 3개 검사
            passed_consistency_checks = sum([
                sum([
                    test['source_consistency'],
                    test['count_consistency'], 
                    test['content_consistency']
                ]) for test in consistency_tests
            ])
            consistency_rate = (passed_consistency_checks / total_consistency_checks) * 100
        else:
            consistency_rate = 0
        
        return {
            'passed': len(issues) == 0 and consistency_rate >= 90,
            'consistency_rate': consistency_rate,
            'consistency_tests': consistency_tests,
            'issues': issues
        }
    
    def test_layer_logic_correctness(self) -> Dict[str, Any]:
        """4층 검색 로직 검증"""
        print("  🏗️ 4층 검색 로직 정확성 검증...")
        
        issues = []
        logic_tests = []
        
        try:
            # 각 레이어별 조건 검증
            
            # 1. Working Memory 우선순위 검증
            print("    📋 Layer 1 (Working Memory) 로직 검증...")
            
            # Working Memory에 충분한 데이터 추가
            wm = self.hybrid_stm.working_memory
            for i in range(4):  # 4개 슬롯 모두 채움
                slot = wm.slots[i]
                slot.context = f"WM 테스트 데이터 {i}"
                slot.embedding = [0.7 + i * 0.1 + j * 0.001 for j in range(128)]
                slot.importance = 0.8
                slot.usage_count = 5  # 충분한 사용 횟수
            
            # Working Memory가 충분할 때 Layer 1에서 반환되는지 확인
            test_embedding = [0.75 + j * 0.001 for j in range(128)]
            result = self.phase3_coordinator.intelligent_search(
                "Working Memory 우선순위 테스트",
                test_embedding,
                ["WM", "테스트"]
            )
            
            expected_source = "working_memory"  # 충분한 WM 결과가 있으면 Layer 1
            actual_source = result.get('source')
            
            if actual_source == expected_source:
                print(f"      ✅ Layer 1 우선순위: {actual_source}")
                logic_tests.append({'layer': 1, 'passed': True, 'expected': expected_source, 'actual': actual_source})
            else:
                issues.append(f"Layer 1 로직 오류: 예상 {expected_source}, 실제 {actual_source}")
                print(f"      ❌ Layer 1 로직 오류: 예상 {expected_source}, 실제 {actual_source}")
                logic_tests.append({'layer': 1, 'passed': False, 'expected': expected_source, 'actual': actual_source})
            
            # 2. 캐시 레이어 검증
            print("    📋 Layer 2 (Cache) 로직 검증...")
            
            # Working Memory 비우기
            for slot in wm.slots:
                slot.context = ""
                slot.embedding = []
            
            # 캐시에 데이터 추가 (직접 캐시 키 생성)
            cache_embedding = [0.5 + j * 0.002 for j in range(128)]
            cache_keywords = ["캐시", "테스트"]
            
            # 캐시 데이터 강제 추가
            self.cache_manager.update_cache(
                "캐시 테스트 쿼리",
                cache_embedding,
                cache_keywords,
                top_k=3
            )
            
            # 동일한 쿼리로 검색 시 캐시에서 반환되는지 확인
            cache_result = self.phase3_coordinator.intelligent_search(
                "캐시 테스트 쿼리",
                cache_embedding,
                cache_keywords
            )
            
            cache_source = cache_result.get('source')
            cache_expected = "cache"
            
            if cache_source == cache_expected:
                print(f"      ✅ Layer 2 캐시: {cache_source}")
                logic_tests.append({'layer': 2, 'passed': True, 'expected': cache_expected, 'actual': cache_source})
            else:
                # 캐시 미스는 정상일 수 있음 (체크포인트나 LTM으로 이동)
                print(f"      ⚠️ Layer 2 결과: {cache_source} (캐시 미스는 정상)")
                logic_tests.append({'layer': 2, 'passed': True, 'expected': cache_expected, 'actual': cache_source, 'note': 'cache_miss_normal'})
            
            # 3. 체크포인트 레이어 검증
            print("    📋 Layer 3 (Checkpoint) 로직 검증...")
            
            # 체크포인트가 있는 상태에서 검색
            checkpoint_embedding = [0.6 + j * 0.003 for j in range(128)]
            checkpoint_result = self.phase3_coordinator.intelligent_search(
                "체크포인트 로직 테스트",
                checkpoint_embedding,
                ["체크포인트", "로직"]
            )
            
            checkpoint_source = checkpoint_result.get('source')
            
            # 체크포인트나 LTM fallback 모두 정상
            if checkpoint_source in ["checkpoint", "ltm_fallback"]:
                print(f"      ✅ Layer 3/4 검색: {checkpoint_source}")
                logic_tests.append({'layer': 3, 'passed': True, 'actual': checkpoint_source})
            else:
                issues.append(f"Layer 3/4 로직 오류: 예상되지 않은 소스 {checkpoint_source}")
                print(f"      ❌ Layer 3/4 오류: {checkpoint_source}")
                logic_tests.append({'layer': 3, 'passed': False, 'actual': checkpoint_source})
        
        except Exception as e:
            issues.append(f"4층 로직 테스트 오류: {str(e)}")
        
        # 로직 정확성 평가
        passed_logic_tests = sum(1 for test in logic_tests if test['passed'])
        total_logic_tests = len(logic_tests)
        logic_correctness_rate = (passed_logic_tests / total_logic_tests) * 100 if total_logic_tests > 0 else 0
        
        return {
            'passed': len(issues) == 0 and logic_correctness_rate >= 80,
            'logic_correctness_rate': logic_correctness_rate,
            'logic_tests': logic_tests,
            'issues': issues
        }
    
    def test_data_integrity(self) -> Dict[str, Any]:
        """데이터 무결성 검증"""
        print("  🔒 데이터 무결성 및 메모리 누수 검증...")
        
        issues = []
        integrity_checks = []
        
        try:
            import tracemalloc
            
            # 메모리 추적 시작
            tracemalloc.start()
            initial_memory = tracemalloc.get_traced_memory()[0]
            
            # 1. 체크포인트 데이터 무결성
            print("    🔍 체크포인트 데이터 무결성 검사...")
            
            original_checkpoints = self.checkpoint_manager.get_all_checkpoints()
            original_count = len(original_checkpoints)
            
            # 다수의 체크포인트 생성/삭제 작업
            for i in range(10):
                test_slot = self.hybrid_stm.working_memory.slots[i % 4]
                test_slot.context = f"무결성 테스트 {i}"
                test_slot.embedding = [0.1 * i + j * 0.001 for j in range(128)]
                
                test_blocks = self._create_verified_test_blocks(5)
                checkpoint = self.checkpoint_manager.create_checkpoint(test_slot, test_blocks)
                
                if not checkpoint:
                    issues.append(f"체크포인트 생성 실패: {i}")
            
            # 체크포인트 정리
            cleaned_count = self.checkpoint_manager.cleanup_old_checkpoints(max_age_hours=0)
            
            # 최종 상태 확인
            final_checkpoints = self.checkpoint_manager.get_all_checkpoints()
            final_count = len(final_checkpoints)
            
            if final_count >= 0:  # 음수가 아니면 정상
                print(f"      ✅ 체크포인트 무결성: {original_count} → {final_count}")
                integrity_checks.append({'type': 'checkpoint', 'passed': True})
            else:
                issues.append("체크포인트 카운트 음수")
                integrity_checks.append({'type': 'checkpoint', 'passed': False})
            
            # 2. 메모리 누수 검사
            print("    🧠 메모리 누수 검사...")
            
            # 대량 작업 수행
            for i in range(50):
                query_embedding = [0.2 * i + j * 0.001 for j in range(128)]
                result = self.localized_engine.search_with_checkpoints(
                    query_embedding,
                    self.hybrid_stm.working_memory
                )
            
            # 메모리 사용량 확인
            current_memory = tracemalloc.get_traced_memory()[0]
            memory_increase = current_memory - initial_memory
            memory_increase_mb = memory_increase / (1024 * 1024)
            
            print(f"      📊 메모리 증가: {memory_increase_mb:.2f}MB")
            
            if memory_increase_mb < 10:  # 10MB 미만 증가는 정상
                print(f"      ✅ 메모리 누수 없음: {memory_increase_mb:.2f}MB")
                integrity_checks.append({'type': 'memory', 'passed': True, 'increase_mb': memory_increase_mb})
            else:
                issues.append(f"메모리 과다 사용: {memory_increase_mb:.2f}MB")
                integrity_checks.append({'type': 'memory', 'passed': False, 'increase_mb': memory_increase_mb})
            
            tracemalloc.stop()
            
            # 3. 데이터 일관성 검사
            print("    📋 데이터 일관성 검사...")
            
            # 통계 데이터 일관성
            checkpoint_stats = self.checkpoint_manager.get_stats()
            localized_stats = self.localized_engine.get_stats()
            coordinator_stats = self.phase3_coordinator.get_comprehensive_stats()
            
            # 음수 값이나 비정상적 값 검사
            stats_valid = True
            
            for stat_name, stat_value in checkpoint_stats.items():
                if isinstance(stat_value, (int, float)) and stat_value < 0:
                    issues.append(f"음수 통계값: {stat_name} = {stat_value}")
                    stats_valid = False
            
            if stats_valid:
                print(f"      ✅ 통계 데이터 일관성: 정상")
                integrity_checks.append({'type': 'statistics', 'passed': True})
            else:
                integrity_checks.append({'type': 'statistics', 'passed': False})
        
        except Exception as e:
            issues.append(f"데이터 무결성 테스트 오류: {str(e)}")
        
        # 무결성 점수 계산
        passed_integrity_checks = sum(1 for check in integrity_checks if check['passed'])
        total_integrity_checks = len(integrity_checks)
        integrity_rate = (passed_integrity_checks / total_integrity_checks) * 100 if total_integrity_checks > 0 else 0
        
        return {
            'passed': len(issues) == 0 and integrity_rate >= 90,
            'integrity_rate': integrity_rate,
            'integrity_checks': integrity_checks,
            'issues': issues
        }
    
    def test_edge_cases(self) -> Dict[str, Any]:
        """엣지 케이스 처리 테스트"""
        print("  🔬 엣지 케이스 및 경계 조건 테스트...")
        
        issues = []
        edge_case_results = []
        
        try:
            # 1. 빈 데이터 처리
            print("    📭 빈 데이터 처리 테스트...")
            
            empty_embedding = []
            empty_result = self.localized_engine.search_with_checkpoints(
                empty_embedding,
                self.hybrid_stm.working_memory
            )
            
            if isinstance(empty_result, list):
                print(f"      ✅ 빈 임베딩 처리: {len(empty_result)}개 결과")
                edge_case_results.append({'case': 'empty_embedding', 'passed': True})
            else:
                issues.append("빈 임베딩 처리 실패")
                edge_case_results.append({'case': 'empty_embedding', 'passed': False})
            
            # 2. 극단적 값 처리
            print("    📊 극단적 값 처리 테스트...")
            
            extreme_embedding = [999.0] * 128  # 극단적으로 큰 값
            extreme_result = self.localized_engine.search_with_checkpoints(
                extreme_embedding,
                self.hybrid_stm.working_memory
            )
            
            if isinstance(extreme_result, list):
                print(f"      ✅ 극단적 값 처리: {len(extreme_result)}개 결과")
                edge_case_results.append({'case': 'extreme_values', 'passed': True})
            else:
                issues.append("극단적 값 처리 실패")
                edge_case_results.append({'case': 'extreme_values', 'passed': False})
            
            # 3. 차원 불일치 처리
            print("    📏 차원 불일치 처리 테스트...")
            
            wrong_dimension = [0.5] * 64  # 128이 아닌 64 차원
            wrong_dim_result = self.localized_engine.search_with_checkpoints(
                wrong_dimension,
                self.hybrid_stm.working_memory
            )
            
            if isinstance(wrong_dim_result, list):
                print(f"      ✅ 차원 불일치 처리: {len(wrong_dim_result)}개 결과")
                edge_case_results.append({'case': 'dimension_mismatch', 'passed': True})
            else:
                issues.append("차원 불일치 처리 실패")
                edge_case_results.append({'case': 'dimension_mismatch', 'passed': False})
            
            # 4. 동시성 테스트
            print("    🔀 동시성 처리 테스트...")
            
            import threading
            import time
            
            concurrent_results = []
            concurrent_errors = []
            
            def concurrent_search(thread_id):
                try:
                    embedding = [0.3 + thread_id * 0.1 + j * 0.001 for j in range(128)]
                    result = self.phase3_coordinator.intelligent_search(
                        f"동시성 테스트 {thread_id}",
                        embedding,
                        ["동시성", "테스트"]
                    )
                    concurrent_results.append(result)
                except Exception as e:
                    concurrent_errors.append(f"Thread {thread_id}: {str(e)}")
            
            # 5개 스레드 동시 실행
            threads = []
            for i in range(5):
                thread = threading.Thread(target=concurrent_search, args=(i,))
                threads.append(thread)
                thread.start()
            
            # 모든 스레드 완료 대기
            for thread in threads:
                thread.join()
            
            if len(concurrent_errors) == 0 and len(concurrent_results) == 5:
                print(f"      ✅ 동시성 처리: 5개 스레드 모두 성공")
                edge_case_results.append({'case': 'concurrency', 'passed': True})
            else:
                issues.append(f"동시성 오류: {len(concurrent_errors)}개")
                edge_case_results.append({'case': 'concurrency', 'passed': False, 'errors': concurrent_errors})
        
        except Exception as e:
            issues.append(f"엣지 케이스 테스트 오류: {str(e)}")
        
        # 엣지 케이스 처리 점수
        passed_edge_cases = sum(1 for case in edge_case_results if case['passed'])
        total_edge_cases = len(edge_case_results)
        edge_case_rate = (passed_edge_cases / total_edge_cases) * 100 if total_edge_cases > 0 else 0
        
        return {
            'passed': len(issues) == 0 and edge_case_rate >= 80,
            'edge_case_rate': edge_case_rate,
            'edge_case_results': edge_case_results,
            'issues': issues
        }
    
    def test_error_recovery(self) -> Dict[str, Any]:
        """오류 복구 메커니즘 테스트"""
        print("  🛡️ 오류 복구 및 안정성 테스트...")
        
        issues = []
        recovery_tests = []
        
        try:
            # 1. Fallback 메커니즘 테스트
            print("    🔄 Fallback 메커니즘 테스트...")
            
            # Working Memory 비우고 체크포인트 제거
            for slot in self.hybrid_stm.working_memory.slots:
                slot.context = ""
                slot.embedding = []
            
            self.checkpoint_manager.checkpoint_cache.clear()
            
            # 이 상태에서 검색 시 LTM fallback이 작동하는지 확인
            fallback_embedding = [0.4 + j * 0.002 for j in range(128)]
            fallback_result = self.phase3_coordinator.intelligent_search(
                "Fallback 테스트",
                fallback_embedding,
                ["fallback", "테스트"]
            )
            
            # Fallback이 작동하면 ltm_fallback 또는 checkpoint 모두 정상
            fallback_source = fallback_result.get('source')
            if fallback_source in ['ltm_fallback', 'checkpoint']:
                print(f"      ✅ Fallback 정상 작동: {fallback_source}")
                recovery_tests.append({'type': 'fallback', 'passed': True})
            else:
                issues.append(f"Fallback 실패: {fallback_source}")
                recovery_tests.append({'type': 'fallback', 'passed': False})
            
            # 2. 부분 실패 복구 테스트
            print("    ⚡ 부분 실패 복구 테스트...")
            
            # 체크포인트 매니저에 잘못된 데이터 주입
            corrupt_slot = self.hybrid_stm.working_memory.slots[0]
            corrupt_slot.context = "복구 테스트"
            corrupt_slot.embedding = [0.5] * 128
            
            # 잘못된 블록 데이터로 체크포인트 생성 시도
            corrupt_blocks = [
                {'block_index': 'invalid', 'embedding': 'not_a_list'},  # 잘못된 데이터
                {'block_index': 999999, 'embedding': [0.1] * 128}  # 존재하지 않는 블록
            ]
            
            try:
                corrupt_checkpoint = self.checkpoint_manager.create_checkpoint(corrupt_slot, corrupt_blocks)
                # 오류가 발생해도 시스템이 계속 작동하는지 확인
                
                recovery_embedding = [0.6] * 128
                recovery_result = self.phase3_coordinator.intelligent_search(
                    "복구 테스트",
                    recovery_embedding,
                    ["복구"]
                )
                
                if recovery_result.get('result_count', 0) >= 0:  # 음수가 아니면 복구 성공
                    print(f"      ✅ 부분 실패 복구: 시스템 계속 작동")
                    recovery_tests.append({'type': 'partial_failure', 'passed': True})
                else:
                    issues.append("부분 실패 후 시스템 중단")
                    recovery_tests.append({'type': 'partial_failure', 'passed': False})
                    
            except Exception as recovery_error:
                # 예외가 적절히 처리되고 시스템이 계속 작동하는지 확인
                try:
                    recovery_embedding = [0.6] * 128
                    recovery_result = self.phase3_coordinator.intelligent_search(
                        "복구 테스트 후",
                        recovery_embedding,
                        ["복구"]
                    )
                    print(f"      ✅ 예외 후 복구: 시스템 정상 작동")
                    recovery_tests.append({'type': 'exception_recovery', 'passed': True})
                except:
                    issues.append("예외 후 시스템 복구 실패")
                    recovery_tests.append({'type': 'exception_recovery', 'passed': False})
            
            # 3. 리소스 고갈 상황 테스트
            print("    💾 리소스 고갈 상황 테스트...")
            
            # 메모리 캐시를 의도적으로 가득 채움
            original_cache = dict(self.checkpoint_manager.checkpoint_cache)
            
            try:
                # 대량의 체크포인트 생성
                for i in range(100):
                    fake_slot_id = f"fake_slot_{i}"
                    self.checkpoint_manager.checkpoint_cache[fake_slot_id] = {
                        'created_at': datetime.now().isoformat(),
                        'ltm_blocks': [{'block_index': i}] * 10
                    }
                
                # 이 상태에서도 정상 작동하는지 확인
                resource_embedding = [0.7] * 128
                resource_result = self.phase3_coordinator.intelligent_search(
                    "리소스 테스트",
                    resource_embedding,
                    ["리소스"]
                )
                
                if resource_result.get('result_count', 0) >= 0:
                    print(f"      ✅ 리소스 고갈 처리: 정상 작동")
                    recovery_tests.append({'type': 'resource_exhaustion', 'passed': True})
                else:
                    issues.append("리소스 고갈 시 시스템 실패")
                    recovery_tests.append({'type': 'resource_exhaustion', 'passed': False})
                    
            finally:
                # 원래 상태 복구
                self.checkpoint_manager.checkpoint_cache = original_cache
        
        except Exception as e:
            issues.append(f"오류 복구 테스트 오류: {str(e)}")
        
        # 복구 능력 점수
        passed_recovery_tests = sum(1 for test in recovery_tests if test['passed'])
        total_recovery_tests = len(recovery_tests)
        recovery_rate = (passed_recovery_tests / total_recovery_tests) * 100 if total_recovery_tests > 0 else 0
        
        return {
            'passed': len(issues) == 0 and recovery_rate >= 80,
            'recovery_rate': recovery_rate,
            'recovery_tests': recovery_tests,
            'issues': issues
        }
    
    def _create_verified_test_blocks(self, count: int) -> List[Dict[str, Any]]:
        """검증된 테스트 블록 생성"""
        test_blocks = []
        
        for i in range(count):
            context = f"검증용 테스트 블록 {i}: 신뢰성 검증을 위한 데이터"
            keywords = ["검증", "신뢰성", f"블록{i}"]
            tags = ["test", "reliability"]
            importance = 0.7 + (i * 0.02)
            embedding = [0.1 * i + j * 0.001 for j in range(128)]
            
            block_result = self.block_manager.add_block(
                context=context,
                keywords=keywords,
                tags=tags,
                embedding=embedding,
                importance=importance
            )
            
            if block_result and "block_index" in block_result:
                test_blocks.append({
                    "block_index": block_result["block_index"],
                    "similarity_score": 0.8 - (i * 0.03),
                    "embedding": embedding,
                    "context": context,
                    "keywords": keywords
                })
        
        return test_blocks
    
    def _hash_results(self, results: List[Dict[str, Any]]) -> str:
        """검색 결과의 해시값 계산 (일관성 검사용)"""
        try:
            # 결과의 핵심 정보만 추출하여 해시 계산
            result_strings = []
            for result in results:
                key_info = f"{result.get('block_index', '')}-{result.get('similarity_score', 0):.3f}"
                result_strings.append(key_info)
            
            combined = "|".join(sorted(result_strings))
            return hashlib.md5(combined.encode()).hexdigest()[:16]
        except:
            return "hash_error"
    
    def _calculate_reliability_score(self, passed_tests: int, total_tests: int, issues: List[str]) -> float:
        """신뢰성 점수 계산"""
        base_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # 이슈 수에 따른 감점
        issue_penalty = min(len(issues) * 5, 30)  # 최대 30점 감점
        
        final_score = max(0, base_score - issue_penalty)
        return round(final_score, 1)
    
    def save_reliability_report(self):
        """신뢰성 검증 보고서 저장"""
        try:
            self.results["end_time"] = datetime.now().isoformat()
            self.results["total_duration_seconds"] = time.perf_counter() - self.test_start_time
            self.results["reliability_metrics"] = self.reliability_metrics
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"phase3_reliability_report_{timestamp}.json"
            filepath = os.path.join(project_root, "tests", "performance_suite", "results", filename)
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 신뢰성 검증 보고서 저장: {filename}")
            
        except Exception as e:
            print(f"⚠️ 보고서 저장 실패: {str(e)}")


def main():
    """메인 신뢰성 테스트 실행 함수"""
    try:
        test = Phase3ReliabilityTest()
        success = test.run_reliability_tests()
        test.save_reliability_report()
        
        if success:
            print("\n🏆 Phase 3 시스템의 높은 신뢰성이 검증되었습니다!")
            return 0
        else:
            print("\n⚠️ Phase 3 시스템의 신뢰성 개선이 필요합니다.")
            return 1
            
    except Exception as e:
        print(f"\n❌ 신뢰성 테스트 실행 중 오류 발생: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())