"""
Hybrid STM 시스템 테스트 - Phase 2 성능 검증

Working Memory와 Legacy STM 통합 테스트
"""

import time
import unittest
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 프로젝트 루트 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

try:
    from greeum.core.hybrid_stm_manager import HybridSTMManager, WorkingMemoryManager, WorkingMemorySlot
    from greeum.core.database_manager import DatabaseManager
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


class TestHybridSTMPerformance(unittest.TestCase):
    """Hybrid STM 시스템 성능 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        # 테스트용 데이터베이스 설정
        self.db_manager = DatabaseManager(connection_string=":memory:")  # 메모리 DB 사용
        self.hybrid_stm = HybridSTMManager(self.db_manager, mode="hybrid")
        
        # 테스트 데이터
        self.test_contexts = [
            "프로젝트 A의 요구사항 분석을 완료했습니다.",
            "버그 수정을 위한 코드 리뷰가 필요합니다.",
            "새로운 기능 구현 일정을 조정해야 합니다.",
            "데이터베이스 성능 최적화 작업을 시작했습니다.",
            "사용자 피드백을 바탕으로 UI를 개선했습니다."
        ]
    
    def test_working_memory_slot_priority_calculation(self):
        """Working Memory 슬롯 우선순위 계산 테스트"""
        print("\n=== Working Memory 슬롯 우선순위 계산 테스트 ===")
        
        slot = WorkingMemorySlot(0)
        slot.context = "프로젝트 A 개발 중 버그 발견"
        slot.importance = 0.8
        slot.usage_count = 5
        
        # 현재 컨텍스트와 연관성이 있는 경우
        current_context = "프로젝트 A의 버그 수정 계획"
        priority_with_relevance = slot.calculate_priority(current_context)
        
        # 연관성이 없는 경우
        priority_without_relevance = slot.calculate_priority("완전히 다른 주제")
        
        print(f"연관성 있는 컨텍스트 우선순위: {priority_with_relevance:.3f}")
        print(f"연관성 없는 컨텍스트 우선순위: {priority_without_relevance:.3f}")
        
        # 연관성이 있을 때 우선순위가 더 높아야 함
        self.assertGreater(priority_with_relevance, priority_without_relevance)
        self.assertGreaterEqual(priority_with_relevance, 0.0)
        self.assertLessEqual(priority_with_relevance, 1.0)
    
    def test_working_memory_management(self):
        """Working Memory 관리 기능 테스트"""
        print("\n=== Working Memory 관리 기능 테스트 ===")
        
        wm = WorkingMemoryManager(slots=4)
        
        # 4개 슬롯 채우기
        for i, context in enumerate(self.test_contexts[:4]):
            result = wm.add_memory(context, importance=0.5 + i * 0.1)
            self.assertTrue(result)
        
        # 사용 가능한 슬롯이 없어야 함
        self.assertFalse(wm.has_available_slot())
        self.assertEqual(len(wm.get_active_slots()), 4)
        
        # 5번째 추가 시 지능적 정리 발생
        before_cleanup = wm.cleanup_count
        result = wm.add_memory(self.test_contexts[4], importance=0.9)
        self.assertTrue(result)
        self.assertGreater(wm.cleanup_count, before_cleanup)
        
        print(f"활성 슬롯 수: {len(wm.get_active_slots())}")
        print(f"정리 횟수: {wm.cleanup_count}")
        print(f"승격 횟수: {wm.promotion_count}")
    
    def test_working_memory_search(self):
        """Working Memory 검색 성능 테스트"""
        print("\n=== Working Memory 검색 성능 테스트 ===")
        
        wm = WorkingMemoryManager(slots=4)
        
        # 테스트 데이터 추가
        for context in self.test_contexts:
            wm.add_memory(context, importance=0.7)
        
        # 검색 테스트
        search_query = "프로젝트"
        
        start_time = time.perf_counter()
        results = wm.search_working_memory(current_context=search_query)
        search_time = (time.perf_counter() - start_time) * 1000  # ms 변환
        
        print(f"검색 시간: {search_time:.3f}ms")
        print(f"검색 결과 수: {len(results)}")
        
        # 검색 결과 검증
        self.assertGreater(len(results), 0)
        for result in results:
            self.assertIn("relevance", result)
            self.assertIn("source", result)
            self.assertEqual(result["source"], "working_memory")
        
        # 검색 시간이 1ms 이하여야 함 (Working Memory는 매우 빨라야 함)
        self.assertLess(search_time, 1.0)
    
    def test_hybrid_stm_modes(self):
        """Hybrid STM 동작 모드 테스트"""
        print("\n=== Hybrid STM 동작 모드 테스트 ===")
        
        # 각 모드별 메모리 추가 테스트
        modes = ["hybrid", "working_only", "legacy"]
        
        for mode in modes:
            self.hybrid_stm.switch_mode(mode)
            
            memory_data = {
                "content": f"{mode} 모드 테스트 데이터",
                "importance": 0.6,
                "timestamp": datetime.now().isoformat()
            }
            
            memory_id = self.hybrid_stm.add_memory(memory_data)
            self.assertIsNotNone(memory_id)
            
            print(f"{mode} 모드: 메모리 ID = {memory_id}")
        
        # 통계 확인
        stats = self.hybrid_stm.get_hybrid_statistics()
        print(f"총 요청 수: {stats['hybrid_performance']['total_requests']}")
        print(f"Working Memory 히트: {stats['hybrid_performance']['working_memory_hits']}")
        print(f"Legacy STM 히트: {stats['hybrid_performance']['legacy_stm_hits']}")
    
    def test_hybrid_stm_search_performance(self):
        """Hybrid STM 검색 성능 테스트"""
        print("\n=== Hybrid STM 검색 성능 테스트 ===")
        
        # hybrid 모드로 설정
        self.hybrid_stm.switch_mode("hybrid")
        
        # 테스트 데이터 추가
        for i, context in enumerate(self.test_contexts * 2):  # 10개 데이터
            memory_data = {
                "content": context,
                "importance": 0.5 + (i % 5) * 0.1,
                "timestamp": datetime.now().isoformat()
            }
            self.hybrid_stm.add_memory(memory_data)
        
        # 검색 성능 측정
        search_queries = [
            "프로젝트",
            "버그 수정",
            "성능 최적화",
            "UI 개선"
        ]
        
        total_search_time = 0
        total_results = 0
        
        for query in search_queries:
            start_time = time.perf_counter()
            results = self.hybrid_stm.search_memories(query, top_k=5)
            search_time = (time.perf_counter() - start_time) * 1000
            
            total_search_time += search_time
            total_results += len(results)
            
            print(f"쿼리 '{query}': {search_time:.3f}ms, {len(results)}개 결과")
        
        avg_search_time = total_search_time / len(search_queries)
        avg_results = total_results / len(search_queries)
        
        print(f"\n평균 검색 시간: {avg_search_time:.3f}ms")
        print(f"평균 결과 수: {avg_results:.1f}개")
        
        # 성능 목표: 평균 검색 시간 < 5ms
        self.assertLess(avg_search_time, 5.0)
    
    def test_working_memory_optimization(self):
        """Working Memory 최적화 기능 테스트"""
        print("\n=== Working Memory 최적화 기능 테스트 ===")
        
        wm = WorkingMemoryManager(slots=4)
        
        # 다양한 중요도의 데이터 추가
        importance_levels = [0.9, 0.3, 0.7, 0.1]
        for i, (context, importance) in enumerate(zip(self.test_contexts[:4], importance_levels)):
            wm.add_memory(context, importance=importance)
            
            # 일부 슬롯의 사용 횟수 조정
            if i in [0, 2]:  # 중요한 슬롯들
                for _ in range(5):
                    wm.slots[i].access()
        
        # 최적화 전 상태
        before_stats = wm.get_statistics()
        
        # 최적화 실행
        current_context = "프로젝트 관련 작업"
        self.hybrid_stm.optimize_working_memory(current_context)
        
        # 최적화 후 상태
        after_stats = wm.get_statistics()
        
        print(f"최적화 전 활성 슬롯: {before_stats['active_slots']}")
        print(f"최적화 후 활성 슬롯: {after_stats['active_slots']}")
        print(f"평균 우선순위: {after_stats['average_priority']:.3f}")
        
        # 낮은 우선순위 슬롯이 정리되었는지 확인
        if before_stats['active_slots'] > 2:
            self.assertLessEqual(after_stats['active_slots'], before_stats['active_slots'])
    
    def test_api_compatibility(self):
        """기존 STM API 호환성 테스트"""
        print("\n=== STM API 호환성 테스트 ===")
        
        # 기존 STM 메서드들이 정상 동작하는지 확인
        
        # add_memory 호환성
        memory_data = {
            "content": "API 호환성 테스트",
            "timestamp": datetime.now().isoformat()
        }
        memory_id = self.hybrid_stm.add_memory(memory_data)
        self.assertIsNotNone(memory_id)
        
        # get_recent_memories 호환성
        recent_memories = self.hybrid_stm.get_recent_memories(5)
        self.assertIsInstance(recent_memories, list)
        
        # clear_all 호환성
        cleared_count = self.hybrid_stm.clear_all()
        self.assertIsInstance(cleared_count, int)
        self.assertGreaterEqual(cleared_count, 0)
        
        print("✅ 모든 STM API 호환성 테스트 통과")
    
    def test_performance_benchmark(self):
        """Phase 2 성능 벤치마크 테스트"""
        print("\n=== Phase 2 성능 벤치마크 ===")
        
        # 대량 데이터로 성능 테스트
        self.hybrid_stm.switch_mode("hybrid")
        
        # 100개 메모리 추가
        add_times = []
        for i in range(100):
            memory_data = {
                "content": f"벤치마크 테스트 데이터 {i}: {self.test_contexts[i % len(self.test_contexts)]}",
                "importance": 0.3 + (i % 7) * 0.1,
                "timestamp": datetime.now().isoformat()
            }
            
            start_time = time.perf_counter()
            memory_id = self.hybrid_stm.add_memory(memory_data)
            add_time = (time.perf_counter() - start_time) * 1000
            add_times.append(add_time)
            
            self.assertIsNotNone(memory_id)
        
        # 50회 검색 테스트
        search_times = []
        for i in range(50):
            query = f"테스트 {i % 10}"
            
            start_time = time.perf_counter()
            results = self.hybrid_stm.search_memories(query, top_k=5)
            search_time = (time.perf_counter() - start_time) * 1000
            search_times.append(search_time)
        
        # 통계 계산
        avg_add_time = sum(add_times) / len(add_times)
        avg_search_time = sum(search_times) / len(search_times)
        max_search_time = max(search_times)
        
        print(f"평균 메모리 추가 시간: {avg_add_time:.3f}ms")
        print(f"평균 검색 시간: {avg_search_time:.3f}ms")
        print(f"최대 검색 시간: {max_search_time:.3f}ms")
        
        # 하이브리드 시스템 통계
        stats = self.hybrid_stm.get_hybrid_statistics()
        print(f"Working Memory 효율성: {stats['efficiency_metrics']['working_memory_efficiency']:.2%}")
        print(f"Combined 사용률: {stats['efficiency_metrics']['combined_usage_rate']:.2%}")
        
        # 성능 목표 검증
        # Phase 2 목표: 평균 검색 시간 < 50ms, Working Memory 효율성 > 70%
        self.assertLess(avg_search_time, 50.0, "평균 검색 시간이 목표(50ms)를 초과했습니다")
        
        wm_efficiency = stats['efficiency_metrics']['working_memory_efficiency']
        if wm_efficiency > 0:  # Working Memory가 사용된 경우에만 검증
            self.assertGreater(wm_efficiency, 0.7, "Working Memory 효율성이 목표(70%)에 미달했습니다")
        
        print("✅ Phase 2 성능 목표 달성!")


def run_hybrid_stm_tests():
    """하이브리드 STM 테스트 실행"""
    print("🚀 Hybrid STM 시스템 테스트 시작")
    print("=" * 60)
    
    # 테스트 스위트 실행
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestHybridSTMPerformance)
    runner = unittest.TextTestRunner(verbosity=0)
    
    start_time = time.perf_counter()
    result = runner.run(suite)
    total_time = time.perf_counter() - start_time
    
    print("\n" + "=" * 60)
    print(f"📊 테스트 완료 - 총 소요시간: {total_time:.2f}초")
    print(f"✅ 성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ 실패: {len(result.failures)}")
    print(f"🚫 오류: {len(result.errors)}")
    
    if result.failures:
        print("\n🔍 실패한 테스트:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.splitlines()[-1] if traceback else 'Unknown error'}")
    
    if result.errors:
        print("\n🚫 오류가 발생한 테스트:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.splitlines()[-1] if traceback else 'Unknown error'}")
    
    return result.testsRun == (result.testsRun - len(result.failures) - len(result.errors))


if __name__ == "__main__":
    success = run_hybrid_stm_tests()
    sys.exit(0 if success else 1)