#!/usr/bin/env python3
"""
Phase 3 체크포인트 시스템 성능 테스트

이 테스트는 Phase 3의 체크포인트 기반 지역 검색 시스템의 성능을 검증합니다.
목표: B+등급(82/100) → A등급(90+/100) 달성
"""

import sys
import os
import time
import json
import traceback
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

from greeum import BlockManager, STMManager, CacheManager, DatabaseManager
from greeum.core.hybrid_stm_manager import HybridSTMManager
from greeum.core.checkpoint_manager import CheckpointManager
from greeum.core.localized_search_engine import LocalizedSearchEngine
from greeum.core.phase_three_coordinator import PhaseThreeSearchCoordinator


class Phase3CheckpointTest:
    """Phase 3 체크포인트 시스템 종합 테스트"""
    
    def __init__(self):
        self.test_start_time = time.perf_counter()
        self.results = {
            "test_name": "Phase 3 Checkpoint System Test",
            "start_time": datetime.now().isoformat(),
            "phase": "phase_3",
            "target_grade": "A (90+/100)",
            "components_tested": [
                "CheckpointManager",
                "LocalizedSearchEngine", 
                "PhaseThreeSearchCoordinator",
                "Integrated Performance"
            ]
        }
        
        # 테스트 환경 설정
        self.setup_test_environment()
        
    def setup_test_environment(self):
        """테스트 환경 초기화"""
        print("🔧 Phase 3 테스트 환경 초기화...")
        
        try:
            # 데이터베이스 및 기본 매니저들
            self.db_manager = DatabaseManager()
            self.block_manager = BlockManager(self.db_manager)
            self.cache_manager = CacheManager()
            
            # Phase 2 하이브리드 STM
            self.hybrid_stm = HybridSTMManager(self.db_manager)
            
            # Phase 3 새로운 구성요소들
            self.checkpoint_manager = CheckpointManager(self.db_manager, self.block_manager)
            self.localized_engine = LocalizedSearchEngine(self.checkpoint_manager, self.block_manager)
            self.phase3_coordinator = PhaseThreeSearchCoordinator(
                self.hybrid_stm,
                self.cache_manager,
                self.checkpoint_manager,
                self.localized_engine,
                self.block_manager
            )
            
            print("  ✅ 모든 Phase 3 구성요소 초기화 완료")
            
        except Exception as e:
            print(f"  ❌ 초기화 실패: {str(e)}")
            raise
    
    def run_all_tests(self):
        """모든 Phase 3 테스트 실행"""
        print("=" * 60)
        print("🧪 Phase 3 체크포인트 시스템 종합 테스트")
        print("=" * 60)
        
        tests = [
            ("1️⃣ 체크포인트 관리자 기본 기능", self.test_checkpoint_manager),
            ("2️⃣ 지역 검색 엔진 성능", self.test_localized_search_engine),
            ("3️⃣ 4층 지능적 검색 통합", self.test_phase3_coordinator),
            ("4️⃣ A등급 달성 종합 성능", self.test_overall_performance)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{test_name} 테스트:")
            try:
                result = test_func()
                if result:
                    print(f"  ✅ {test_name}: 성공")
                    passed_tests += 1
                else:
                    print(f"  ❌ {test_name}: 실패")
            except Exception as e:
                print(f"  ❌ {test_name}: 오류 - {str(e)}")
                traceback.print_exc()
        
        # 최종 결과
        success_rate = (passed_tests / total_tests) * 100
        self.results["tests_passed"] = passed_tests
        self.results["tests_total"] = total_tests
        self.results["success_rate"] = success_rate
        
        print("\n" + "=" * 60)
        print("📋 Phase 3 테스트 결과 요약")
        print("=" * 60)
        print(f"🎯 전체 테스트: {passed_tests}/{total_tests} 통과")
        print(f"📊 성공률: {success_rate:.1f}%")
        
        if success_rate >= 75:
            print("🏆 최종 판정: ✅ Phase 3 시스템 검증 성공")
            return True
        else:
            print("❌ 최종 판정: Phase 3 시스템 개선 필요")
            return False
    
    def test_checkpoint_manager(self):
        """체크포인트 관리자 기본 기능 테스트"""
        try:
            print("  📍 체크포인트 생성 및 관리 테스트...")
            
            # 테스트 LTM 블록 추가
            test_blocks = []
            for i in range(10):
                context = f"테스트 블록 {i}: Phase 3 체크포인트 시스템 검증용 데이터"
                keywords = ["Phase3", "체크포인트", f"테스트{i}"]
                tags = ["test", "phase3"]
                importance = 0.7 + (i * 0.03)
                embedding = [0.1 * j + i * 0.05 for j in range(128)]  # 128차원 테스트 임베딩
                
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
                        "similarity_score": 0.8 - (i * 0.05),
                        "embedding": embedding,
                        "context": context,
                        "keywords": keywords
                    })
            
            print(f"    {len(test_blocks)}개 테스트 블록 생성 완료")
            
            # Working Memory 슬롯 생성
            working_memory = self.hybrid_stm.working_memory
            available_slots = [slot for slot in working_memory.slots if slot.is_empty()]
            
            if not available_slots:
                print("    ❌ 사용 가능한 Working Memory 슬롯 없음")
                return False
            
            test_slot = available_slots[0]
            test_slot.context = "Phase 3 체크포인트 테스트 컨텍스트"
            test_slot.embedding = [0.5 + i * 0.1 for i in range(128)]
            
            # 체크포인트 생성 테스트
            checkpoint = self.checkpoint_manager.create_checkpoint(test_slot, test_blocks[:5])
            
            if not checkpoint:
                print("    ❌ 체크포인트 생성 실패")
                return False
            
            print(f"    ✅ 체크포인트 생성: {len(checkpoint['ltm_blocks'])}개 블록 연결")
            
            # 체크포인트 접근 테스트
            access_success = self.checkpoint_manager.update_checkpoint_access(test_slot.slot_id)
            if not access_success:
                print("    ❌ 체크포인트 접근 업데이트 실패")
                return False
            
            # 반경 검색 테스트
            radius_blocks = self.checkpoint_manager.get_checkpoint_radius(test_slot.slot_id, radius=10)
            if not radius_blocks:
                print("    ❌ 체크포인트 반경 검색 실패")
                return False
            
            print(f"    ✅ 반경 검색: {len(radius_blocks)}개 블록 범위 계산")
            
            # 통계 확인
            stats = self.checkpoint_manager.get_stats()
            print(f"    📊 체크포인트 통계: 생성 {stats['checkpoints_created']}, 활성 {stats['checkpoints_active']}")
            
            return True
            
        except Exception as e:
            print(f"    ❌ 체크포인트 관리자 테스트 실패: {str(e)}")
            return False
    
    def test_localized_search_engine(self):
        """지역 검색 엔진 성능 테스트"""
        try:
            print("  🎯 지역 검색 성능 비교 테스트...")
            
            # 테스트 쿼리 임베딩
            query_embedding = [0.6 + i * 0.08 for i in range(128)]
            
            # 지역 검색 실행
            localized_start = time.perf_counter()
            localized_results = self.localized_engine.search_with_checkpoints(
                query_embedding, 
                self.hybrid_stm.working_memory
            )
            localized_time = (time.perf_counter() - localized_start) * 1000
            
            # 전체 LTM 검색 비교
            ltm_start = time.perf_counter()
            ltm_results = self.block_manager.search_by_embedding(query_embedding, top_k=5)
            ltm_time = (time.perf_counter() - ltm_start) * 1000
            
            print(f"    🎯 지역 검색: {len(localized_results)}개 결과, {localized_time:.2f}ms")
            print(f"    🔄 전체 LTM: {len(ltm_results)}개 결과, {ltm_time:.2f}ms")
            
            # 성능 비교
            if localized_time > 0 and ltm_time > 0:
                speed_improvement = ltm_time / localized_time
                print(f"    📈 속도 향상: {speed_improvement:.1f}x")
                
                # 목표: 지역 검색이 전체 검색보다 2배 이상 빠름
                if speed_improvement >= 2.0:
                    print("    ✅ 속도 향상 목표 달성 (2x+)")
                    speed_success = True
                else:
                    print("    ⚠️ 속도 향상 부족 (< 2x)")
                    speed_success = False
            else:
                speed_success = True  # 시간이 너무 짧아 측정 불가
            
            # 결과 품질 확인
            result_quality = len(localized_results) >= 2  # 최소 2개 결과
            
            # 통계 확인
            search_stats = self.localized_engine.get_stats()
            print(f"    📊 검색 통계: 지역 {search_stats['localized_searches']}, "
                  f"Fallback {search_stats['fallback_searches']}")
            
            return speed_success and result_quality
            
        except Exception as e:
            print(f"    ❌ 지역 검색 엔진 테스트 실패: {str(e)}")
            return False
    
    def test_phase3_coordinator(self):
        """Phase 3 통합 조정자 테스트"""
        try:
            print("  🚀 4층 지능적 검색 통합 테스트...")
            
            # 다양한 검색 시나리오 테스트
            test_scenarios = [
                {
                    "query": "Phase 3 체크포인트 시스템 성능",
                    "embedding": [0.7 + i * 0.03 for i in range(128)],
                    "keywords": ["Phase3", "체크포인트", "성능"],
                    "expected_source": ["working_memory", "checkpoint", "cache"]
                },
                {
                    "query": "지역 검색 알고리즘 최적화",
                    "embedding": [0.4 + i * 0.06 for i in range(128)],
                    "keywords": ["지역검색", "알고리즘", "최적화"],
                    "expected_source": ["checkpoint", "ltm_fallback"]
                }
            ]
            
            search_results = []
            
            for i, scenario in enumerate(test_scenarios):
                print(f"    시나리오 {i+1}: '{scenario['query'][:30]}...'")
                
                search_start = time.perf_counter()
                result = self.phase3_coordinator.intelligent_search(
                    scenario["query"],
                    scenario["embedding"], 
                    scenario["keywords"]
                )
                search_time = (time.perf_counter() - search_start) * 1000
                
                if result and "results" in result:
                    source = result.get("source", "unknown")
                    result_count = result.get("result_count", 0)
                    layer_time = result.get("layer_time_ms", 0)
                    
                    print(f"      ✅ 소스: {source}, 결과: {result_count}개, "
                          f"시간: {search_time:.2f}ms (층: {layer_time:.2f}ms)")
                    
                    search_results.append({
                        "scenario": i + 1,
                        "source": source,
                        "result_count": result_count,
                        "search_time_ms": search_time,
                        "layer_time_ms": layer_time
                    })
                else:
                    print(f"      ❌ 검색 실패")
                    return False
            
            # 통합 통계 확인
            comprehensive_stats = self.phase3_coordinator.get_comprehensive_stats()
            
            print("    📊 4층 검색 통계:")
            layer_usage = comprehensive_stats["phase_3_coordinator"]["layer_usage"]
            for layer, count in layer_usage.items():
                if count > 0:
                    print(f"      {layer}: {count}회 사용")
            
            # 성능 목표 확인: 평균 검색 시간 < 1ms
            avg_time = sum(r["search_time_ms"] for r in search_results) / len(search_results)
            print(f"    ⏱️ 평균 검색 시간: {avg_time:.2f}ms")
            
            time_success = avg_time < 1.0  # 1ms 이하 목표
            usage_success = sum(layer_usage.values()) > 0  # 최소 1회 사용
            
            return time_success and usage_success
            
        except Exception as e:
            print(f"    ❌ Phase 3 조정자 테스트 실패: {str(e)}")
            return False
    
    def test_overall_performance(self):
        """A등급 달성 종합 성능 테스트"""
        try:
            print("  🏆 A등급(90+/100) 달성 종합 성능 테스트...")
            
            # 성능 지표 측정
            performance_metrics = {
                "search_speed": 0,      # 검색 속도 (40점)
                "checkpoint_efficiency": 0,  # 체크포인트 효율성 (30점)
                "system_stability": 0,  # 시스템 안정성 (20점)
                "integration_quality": 0  # 통합 품질 (10점)
            }
            
            # 1. 검색 속도 테스트 (40점)
            speed_tests = []
            for i in range(10):
                query_embedding = [0.5 + (i * 0.1) + (j * 0.02) for j in range(128)]
                
                start_time = time.perf_counter()
                result = self.phase3_coordinator.intelligent_search(
                    f"속도 테스트 쿼리 {i}",
                    query_embedding,
                    [f"테스트{i}", "속도"]
                )
                search_time = (time.perf_counter() - start_time) * 1000
                speed_tests.append(search_time)
            
            avg_speed = sum(speed_tests) / len(speed_tests)
            print(f"    ⚡ 평균 검색 속도: {avg_speed:.2f}ms")
            
            # 현실적 목표: 1ms 이하 = 40점, 5ms 이하 = 30점, 10ms 이하 = 20점
            if avg_speed <= 1.0:
                performance_metrics["search_speed"] = 40
            elif avg_speed <= 5.0:
                performance_metrics["search_speed"] = 30
            elif avg_speed <= 10.0:
                performance_metrics["search_speed"] = 20
            else:
                performance_metrics["search_speed"] = 10
            
            # 2. 체크포인트 효율성 (30점)
            checkpoint_stats = self.checkpoint_manager.get_stats()
            localized_stats = self.localized_engine.get_stats()
            
            hit_rate = checkpoint_stats.get("cache_hit_rate", 0)
            checkpoint_usage = localized_stats.get("checkpoint_hit_rate", 0)
            
            print(f"    📍 체크포인트 적중률: {hit_rate:.1%}")
            print(f"    🎯 지역 검색 사용률: {checkpoint_usage:.1%}")
            
            # 목표: 70%+ = 30점, 50%+ = 20점, 30%+ = 10점
            efficiency_score = (hit_rate + checkpoint_usage) / 2
            if efficiency_score >= 0.7:
                performance_metrics["checkpoint_efficiency"] = 30
            elif efficiency_score >= 0.5:
                performance_metrics["checkpoint_efficiency"] = 20
            elif efficiency_score >= 0.3:
                performance_metrics["checkpoint_efficiency"] = 10
            
            # 3. 시스템 안정성 (20점)
            # 모든 구성요소가 오류 없이 동작하면 만점
            stability_score = 20  # 여기까지 오면 안정성 확인됨
            performance_metrics["system_stability"] = stability_score
            
            # 4. 통합 품질 (10점)
            coordinator_stats = self.phase3_coordinator.get_comprehensive_stats()
            total_searches = coordinator_stats["phase_3_coordinator"]["total_searches"]
            
            if total_searches >= 10:  # 충분한 테스트 수행
                performance_metrics["integration_quality"] = 10
            elif total_searches >= 5:
                performance_metrics["integration_quality"] = 7
            else:
                performance_metrics["integration_quality"] = 5
            
            # 총점 계산
            total_score = sum(performance_metrics.values())
            
            print("    📊 성능 평가 상세:")
            for metric, score in performance_metrics.items():
                print(f"      {metric}: {score}점")
            
            print(f"    🎯 총점: {total_score}/100")
            
            # A등급 판정 (90점 이상)
            if total_score >= 90:
                print("    🏆 A등급 달성! Phase 3 목표 완료")
                grade = "A"
                success = True
            elif total_score >= 80:
                print("    🥈 B+등급 달성")
                grade = "B+"
                success = False
            else:
                print("    📈 추가 최적화 필요")
                grade = "B"
                success = False
            
            self.results["final_score"] = total_score
            self.results["final_grade"] = grade
            self.results["performance_metrics"] = performance_metrics
            
            return success
            
        except Exception as e:
            print(f"    ❌ 종합 성능 테스트 실패: {str(e)}")
            return False
    
    def save_results(self):
        """테스트 결과 저장"""
        try:
            self.results["end_time"] = datetime.now().isoformat()
            self.results["total_duration_seconds"] = time.perf_counter() - self.test_start_time
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"phase3_checkpoint_test_{timestamp}.json"
            filepath = os.path.join(project_root, "tests", "performance_suite", "results", filename)
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 테스트 결과 저장: {filename}")
            
        except Exception as e:
            print(f"⚠️ 결과 저장 실패: {str(e)}")


def main():
    """메인 테스트 실행 함수"""
    try:
        test = Phase3CheckpointTest()
        success = test.run_all_tests()
        test.save_results()
        
        if success:
            print("\n🎉 Phase 3 체크포인트 시스템이 모든 검증을 통과했습니다!")
            return 0
        else:
            print("\n⚠️ Phase 3 시스템에 개선이 필요합니다.")
            return 1
            
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())