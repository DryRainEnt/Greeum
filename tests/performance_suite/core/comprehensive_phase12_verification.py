#!/usr/bin/env python3
"""
Phase 1+2 철저한 통합 검증 테스트
실제 Greeum 환경에서 모든 컴포넌트 통합 테스트
"""

import time
import sys
import os
import traceback
import threading
import gc
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# 상위 디렉토리를 path에 추가
sys.path.insert(0, os.path.abspath('../../..'))

from greeum import BlockManager, STMManager, CacheManager, PromptWrapper
from greeum.core.database_manager import DatabaseManager
from greeum.core.hybrid_stm_manager import HybridSTMManager
from greeum.embedding_models import get_embedding

class ComprehensiveVerificationSuite:
    """포괄적 검증 테스트 스위트"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        self.db_path = ":memory:"  # 격리된 테스트 환경
        
    def setup_test_environment(self):
        """실제 Greeum 환경 설정"""
        print("🔧 실제 Greeum 환경 설정 중...")
        
        try:
            # 데이터베이스 매니저 초기화
            self.db_manager = DatabaseManager(connection_string=self.db_path)
            
            # 핵심 컴포넌트들 초기화
            self.block_manager = BlockManager(self.db_manager)
            self.cache_manager = CacheManager(
                data_path="data/test_cache.json", 
                cache_ttl=300,  # 5분 TTL
                block_manager=self.block_manager
            )
            self.legacy_stm = STMManager(self.db_manager)
            self.hybrid_stm = HybridSTMManager(self.db_manager, mode="hybrid")
            self.prompt_wrapper = PromptWrapper(
                cache_manager=self.cache_manager, 
                stm_manager=self.hybrid_stm
            )
            
            print("  ✅ 모든 컴포넌트 초기화 완료")
            return True
            
        except Exception as e:
            print(f"  ❌ 환경 설정 실패: {e}")
            traceback.print_exc()
            return False
    
    def test_phase1_cache_integration(self):
        """Phase 1 캐시 최적화 통합 테스트"""
        print("\n🧪 Phase 1 캐시 최적화 통합 검증:")
        
        try:
            # 실제 LTM 데이터 생성
            print("  LTM 데이터 생성 중...")
            test_memories = [
                "AI 프로젝트 개발 시작 - 머신러닝 모델 설계 및 데이터 준비",
                "성능 최적화 작업 완료 - 캐시 시스템 도입으로 5x 속도 향상",
                "버그 수정 및 코드 리뷰 - 메모리 누수 문제 해결 완료",
                "새로운 기능 구현 - 하이브리드 STM 시스템 설계 및 개발",
                "테스트 코드 작성 - 단위 테스트 및 통합 테스트 완료",
                "문서화 작업 - API 문서 및 사용자 가이드 업데이트",
                "배포 준비 - CI/CD 파이프라인 구축 및 자동화",
                "성능 모니터링 - 메트릭 수집 및 대시보드 구성"
            ]
            
            # LTM에 실제 메모리 블록 추가
            block_indices = []
            for i, memory in enumerate(test_memories):
                block_data = {
                    "context": memory,
                    "keywords": memory.split()[:3],  # 첫 3개 단어를 키워드로
                    "importance": 0.5 + (i % 3) * 0.2  # 0.5-0.9 범위
                }
                
                block_index = self.block_manager.add_block(block_data)
                block_indices.append(block_index)
                time.sleep(0.01)  # 타임스탬프 차이
            
            print(f"    추가된 LTM 블록: {len(block_indices)}개")
            
            # 캐시 성능 테스트 (실제 검색 쿼리)
            test_queries = [
                "AI 프로젝트 개발",
                "성능 최적화 작업", 
                "버그 수정 완료",
                "새로운 기능 구현"
            ]
            
            # 캐시 미스 시간 측정 (첫 번째 실행)
            print("  캐시 미스 성능 측정:")
            miss_times = []
            
            for query in test_queries:
                embedding = get_embedding(query)
                keywords = query.split()
                
                start_time = time.perf_counter()
                results = self.cache_manager.update_cache(query, embedding, keywords, top_k=5)
                execution_time = (time.perf_counter() - start_time) * 1000
                
                miss_times.append(execution_time)
                print(f"    '{query}': {execution_time:.2f}ms, {len(results)}개 결과")
            
            avg_miss_time = sum(miss_times) / len(miss_times)
            
            # 캐시 히트 시간 측정 (두 번째 실행)
            print("  캐시 히트 성능 측정:")
            hit_times = []
            
            for query in test_queries:
                embedding = get_embedding(query)
                keywords = query.split()
                
                start_time = time.perf_counter()
                results = self.cache_manager.update_cache(query, embedding, keywords, top_k=5)
                execution_time = (time.perf_counter() - start_time) * 1000
                
                hit_times.append(execution_time)
                print(f"    '{query}': {execution_time:.2f}ms (캐시 히트)")
            
            avg_hit_time = sum(hit_times) / len(hit_times)
            
            # 캐시 통계 확인
            cache_stats = self.cache_manager.get_cache_stats()
            
            # 성능 분석
            speedup = avg_miss_time / avg_hit_time if avg_hit_time > 0 else 1
            
            print(f"\n  Phase 1 캐시 성능 결과:")
            print(f"    평균 캐시 미스 시간: {avg_miss_time:.2f}ms")
            print(f"    평균 캐시 히트 시간: {avg_hit_time:.2f}ms")
            print(f"    속도 향상: {speedup:.1f}x")
            print(f"    캐시 히트율: {cache_stats['hit_ratio']:.1%}")
            
            # 성공 기준
            good_speedup = speedup > 5  # 5배 이상 개선
            fast_hit = avg_hit_time < 10  # 10ms 이내
            good_hit_ratio = cache_stats['hit_ratio'] > 0.4  # 40% 이상
            
            success = good_speedup and fast_hit and good_hit_ratio
            
            print(f"    속도 향상 (>5x): {'✅' if good_speedup else '❌'}")
            print(f"    히트 시간 (<10ms): {'✅' if fast_hit else '❌'}")
            print(f"    히트율 (>40%): {'✅' if good_hit_ratio else '❌'}")
            print(f"  ✅ Phase 1 통합 테스트: {'성공' if success else '실패'}")
            
            return {
                "success": success,
                "speedup": speedup,
                "avg_hit_time": avg_hit_time,
                "hit_ratio": cache_stats['hit_ratio'],
                "blocks_created": len(block_indices)
            }
            
        except Exception as e:
            print(f"  ❌ Phase 1 통합 테스트 실패: {e}")
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def test_phase2_hybrid_stm_integration(self):
        """Phase 2 하이브리드 STM 통합 테스트"""
        print("\n🧪 Phase 2 하이브리드 STM 통합 검증:")
        
        try:
            # 실제 STM 데이터 추가
            print("  STM 데이터 추가 중...")
            stm_memories = [
                {"content": "현재 세션: AI 성능 최적화 프로젝트 진행 중", "importance": 0.9},
                {"content": "방금 완료: 캐시 시스템 통합 테스트 성공", "importance": 0.8},
                {"content": "진행 예정: 하이브리드 STM 시스템 검증", "importance": 0.8},
                {"content": "이슈 발견: Working Memory 검색 적중률 개선 필요", "importance": 0.7},
                {"content": "성과 달성: Phase 1에서 259x 속도 향상 확인", "importance": 0.9}
            ]
            
            added_memories = []
            for memory in stm_memories:
                memory_id = self.hybrid_stm.add_memory(memory)
                added_memories.append(memory_id)
                time.sleep(0.02)  # 타임스탬프 차이
            
            print(f"    추가된 STM 메모리: {len(added_memories)}개")
            
            # Working Memory 상태 확인
            wm_stats = self.hybrid_stm.working_memory.get_statistics()
            print(f"    Working Memory 활용률: {wm_stats['utilization_rate']:.1%}")
            
            # 하이브리드 검색 성능 테스트
            print("  하이브리드 검색 성능 측정:")
            search_queries = [
                "AI 성능 최적화",
                "캐시 시스템 통합",
                "STM 시스템 검증",
                "Working Memory 검색",
                "Phase 속도 향상"
            ]
            
            search_results = []
            search_times = []
            wm_hits = 0
            
            for query in search_queries:
                start_time = time.perf_counter()
                results = self.hybrid_stm.search_memories(query, top_k=3)
                execution_time = (time.perf_counter() - start_time) * 1000
                
                search_times.append(execution_time)
                search_results.extend(results)
                
                # Working Memory 결과 확인
                wm_results = [r for r in results if r.get("source") == "working_memory"]
                if wm_results:
                    wm_hits += 1
                
                print(f"    '{query}': {len(results)}개 결과, {execution_time:.3f}ms")
                if wm_results:
                    print(f"      Working Memory: {len(wm_results)}개 적중")
            
            avg_search_time = sum(search_times) / len(search_times)
            wm_hit_rate = (wm_hits / len(search_queries)) * 100
            
            # 최근 메모리 조회 테스트
            print("  최근 메모리 조회 테스트:")
            start_time = time.perf_counter()
            recent_memories = self.hybrid_stm.get_recent_memories(count=8)
            recent_time = (time.perf_counter() - start_time) * 1000
            
            print(f"    조회 시간: {recent_time:.3f}ms")
            print(f"    조회된 메모리: {len(recent_memories)}개")
            
            # 하이브리드 통계 확인
            hybrid_stats = self.hybrid_stm.get_hybrid_statistics()
            efficiency = hybrid_stats["efficiency_metrics"]
            
            print(f"\n  Phase 2 하이브리드 STM 결과:")
            print(f"    평균 검색 시간: {avg_search_time:.3f}ms")
            print(f"    Working Memory 적중률: {wm_hit_rate:.1f}%")
            print(f"    Working Memory 효율성: {efficiency['working_memory_efficiency']:.1%}")
            print(f"    최근 조회 시간: {recent_time:.3f}ms")
            
            # 성공 기준
            fast_search = avg_search_time < 5  # 5ms 이내
            good_wm_hit = wm_hit_rate > 60  # 60% 이상 적중
            fast_recent = recent_time < 1  # 1ms 이내
            good_efficiency = efficiency['working_memory_efficiency'] > 0.5  # 50% 이상
            
            success = fast_search and good_wm_hit and fast_recent and good_efficiency
            
            print(f"    검색 속도 (<5ms): {'✅' if fast_search else '❌'}")
            print(f"    WM 적중률 (>60%): {'✅' if good_wm_hit else '❌'}")
            print(f"    최근 조회 (<1ms): {'✅' if fast_recent else '❌'}")
            print(f"    WM 효율성 (>50%): {'✅' if good_efficiency else '❌'}")
            print(f"  ✅ Phase 2 통합 테스트: {'성공' if success else '실패'}")
            
            return {
                "success": success,
                "avg_search_time": avg_search_time,
                "wm_hit_rate": wm_hit_rate,
                "recent_time": recent_time,
                "efficiency": efficiency['working_memory_efficiency'],
                "memories_added": len(added_memories)
            }
            
        except Exception as e:
            print(f"  ❌ Phase 2 통합 테스트 실패: {e}")
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def test_phase12_integration_synergy(self):
        """Phase 1+2 통합 시너지 효과 테스트"""
        print("\n🧪 Phase 1+2 통합 시너지 효과 검증:")
        
        try:
            # PromptWrapper를 통한 실제 워크플로우 테스트
            print("  PromptWrapper 통합 워크플로우 테스트:")
            
            test_prompts = [
                "AI 프로젝트의 현재 진행 상황을 정리해주세요",
                "성능 최적화 작업에서 얻은 성과는 무엇인가요?",
                "캐시 시스템의 효과는 어느 정도인가요?",
                "Working Memory의 활용도는 어떤가요?"
            ]
            
            synergy_results = []
            total_time = 0
            
            for prompt in test_prompts:
                print(f"    프롬프트: '{prompt[:30]}...'")
                
                start_time = time.perf_counter()
                
                # 실제 PromptWrapper 워크플로우
                enhanced_prompt = self.prompt_wrapper.enhance_prompt(
                    user_input=prompt,
                    max_context_blocks=5,
                    include_stm=True,
                    include_cache=True
                )
                
                execution_time = (time.perf_counter() - start_time) * 1000
                total_time += execution_time
                
                # 결과 분석
                has_ltm_context = "# LTM 관련 기억" in enhanced_prompt
                has_stm_context = "# STM 기억" in enhanced_prompt
                prompt_length = len(enhanced_prompt)
                
                result = {
                    "prompt": prompt,
                    "time": execution_time,
                    "has_ltm": has_ltm_context,
                    "has_stm": has_stm_context,
                    "length": prompt_length
                }
                synergy_results.append(result)
                
                print(f"      실행 시간: {execution_time:.2f}ms")
                print(f"      LTM 컨텍스트: {'✅' if has_ltm_context else '❌'}")
                print(f"      STM 컨텍스트: {'✅' if has_stm_context else '❌'}")
                print(f"      강화된 프롬프트 길이: {prompt_length}자")
            
            avg_time = total_time / len(test_prompts)
            ltm_usage = sum(1 for r in synergy_results if r["has_ltm"]) / len(synergy_results)
            stm_usage = sum(1 for r in synergy_results if r["has_stm"]) / len(synergy_results)
            
            print(f"\n  통합 시너지 효과 결과:")
            print(f"    평균 프롬프트 강화 시간: {avg_time:.2f}ms")
            print(f"    LTM 활용률: {ltm_usage:.1%}")
            print(f"    STM 활용률: {stm_usage:.1%}")
            
            # 성공 기준
            fast_enhancement = avg_time < 50  # 50ms 이내
            good_ltm_usage = ltm_usage > 0.7  # 70% 이상
            good_stm_usage = stm_usage > 0.5  # 50% 이상
            
            success = fast_enhancement and good_ltm_usage and good_stm_usage
            
            print(f"    강화 속도 (<50ms): {'✅' if fast_enhancement else '❌'}")
            print(f"    LTM 활용 (>70%): {'✅' if good_ltm_usage else '❌'}")
            print(f"    STM 활용 (>50%): {'✅' if good_stm_usage else '❌'}")
            print(f"  ✅ 통합 시너지 테스트: {'성공' if success else '실패'}")
            
            return {
                "success": success,
                "avg_time": avg_time,
                "ltm_usage": ltm_usage,
                "stm_usage": stm_usage,
                "results": synergy_results
            }
            
        except Exception as e:
            print(f"  ❌ 통합 시너지 테스트 실패: {e}")
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def test_stress_and_stability(self):
        """스트레스 및 안정성 테스트"""
        print("\n🧪 스트레스 및 안정성 검증:")
        
        try:
            print("  대용량 동시 요청 테스트:")
            
            # 동시 요청 함수
            def concurrent_operations(thread_id: int, results: list):
                try:
                    operations = 0
                    for i in range(20):  # 각 스레드에서 20개 작업
                        # STM 추가
                        memory = {
                            "content": f"스레드 {thread_id} 작업 {i+1}: 동시성 테스트 진행",
                            "importance": 0.5 + (i % 5) * 0.1
                        }
                        self.hybrid_stm.add_memory(memory)
                        
                        # 검색 수행
                        search_results = self.hybrid_stm.search_memories(f"스레드 {thread_id}", top_k=3)
                        
                        # 캐시 검색
                        embedding = get_embedding(f"테스트 {thread_id}")
                        cache_results = self.cache_manager.update_cache(
                            f"테스트 {thread_id}", embedding, [f"테스트", f"{thread_id}"]
                        )
                        
                        operations += 3  # 추가, 검색, 캐시
                        
                        if i % 5 == 0:
                            time.sleep(0.001)  # 가끔 대기
                    
                    results.append({"thread_id": thread_id, "operations": operations, "success": True})
                    
                except Exception as e:
                    results.append({"thread_id": thread_id, "error": str(e), "success": False})
            
            # 멀티스레드 실행
            threads = []
            results = []
            start_time = time.perf_counter()
            
            for i in range(5):  # 5개 스레드
                thread = threading.Thread(target=concurrent_operations, args=(i, results))
                threads.append(thread)
                thread.start()
            
            # 모든 스레드 완료 대기
            for thread in threads:
                thread.join(timeout=30)  # 30초 타임아웃
            
            stress_time = (time.perf_counter() - start_time) * 1000
            
            # 결과 분석
            successful_threads = [r for r in results if r.get("success", False)]
            failed_threads = [r for r in results if not r.get("success", False)]
            total_operations = sum(r["operations"] for r in successful_threads)
            
            print(f"    실행 시간: {stress_time:.1f}ms")
            print(f"    성공한 스레드: {len(successful_threads)}/5")
            print(f"    총 수행 작업: {total_operations}개")
            print(f"    초당 작업 수: {total_operations / (stress_time/1000):.1f} ops/sec")
            
            if failed_threads:
                print("    실패한 스레드 오류:")
                for fail in failed_threads:
                    print(f"      스레드 {fail.get('thread_id', '?')}: {fail.get('error', 'Unknown')}")
            
            # 메모리 사용량 확인
            gc.collect()
            import psutil
            import os
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            print(f"    메모리 사용량: {memory_mb:.1f}MB")
            
            # 성공 기준
            good_success_rate = len(successful_threads) >= 4  # 80% 이상 성공
            good_performance = total_operations > 200  # 200개 이상 작업
            reasonable_memory = memory_mb < 200  # 200MB 이내
            
            success = good_success_rate and good_performance and reasonable_memory
            
            print(f"    성공률 (≥80%): {'✅' if good_success_rate else '❌'}")
            print(f"    성능 (>200 ops): {'✅' if good_performance else '❌'}")
            print(f"    메모리 (<200MB): {'✅' if reasonable_memory else '❌'}")
            print(f"  ✅ 스트레스 테스트: {'성공' if success else '실패'}")
            
            return {
                "success": success,
                "stress_time": stress_time,
                "successful_threads": len(successful_threads),
                "total_operations": total_operations,
                "memory_mb": memory_mb
            }
            
        except Exception as e:
            print(f"  ❌ 스트레스 테스트 실패: {e}")
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def run_comprehensive_verification(self):
        """포괄적 검증 실행"""
        print("=" * 80)
        print("🧪 Phase 1+2 철저한 통합 검증 테스트")
        print("=" * 80)
        
        # 환경 설정
        if not self.setup_test_environment():
            return False
        
        # 각 테스트 실행
        self.test_results["phase1"] = self.test_phase1_cache_integration()
        self.test_results["phase2"] = self.test_phase2_hybrid_stm_integration()
        self.test_results["synergy"] = self.test_phase12_integration_synergy()
        self.test_results["stress"] = self.test_stress_and_stability()
        
        # 최종 결과 분석
        return self.analyze_final_results()
    
    def analyze_final_results(self):
        """최종 결과 분석"""
        print("\n" + "=" * 80)
        print("📋 철저한 검증 결과 분석")
        print("=" * 80)
        
        total_time = time.time() - self.start_time
        
        # 각 테스트 성공 여부
        phase1_success = self.test_results.get("phase1", {}).get("success", False)
        phase2_success = self.test_results.get("phase2", {}).get("success", False)
        synergy_success = self.test_results.get("synergy", {}).get("success", False)
        stress_success = self.test_results.get("stress", {}).get("success", False)
        
        total_tests = 4
        passed_tests = sum([phase1_success, phase2_success, synergy_success, stress_success])
        
        print(f"🎯 전체 테스트: {passed_tests}/{total_tests} 통과")
        print(f"📊 성공률: {(passed_tests/total_tests)*100:.1f}%")
        print(f"⏱️ 총 검증 시간: {total_time:.1f}초")
        
        # 상세 결과
        print(f"\n상세 결과:")
        
        if phase1_success:
            p1 = self.test_results["phase1"]
            print(f"  Phase 1 캐시: ✅ (속도향상: {p1['speedup']:.1f}x, 히트율: {p1['hit_ratio']:.1%})")
        else:
            print(f"  Phase 1 캐시: ❌")
        
        if phase2_success:
            p2 = self.test_results["phase2"]
            print(f"  Phase 2 STM: ✅ (WM적중률: {p2['wm_hit_rate']:.1f}%, 검색: {p2['avg_search_time']:.1f}ms)")
        else:
            print(f"  Phase 2 STM: ❌")
        
        if synergy_success:
            syn = self.test_results["synergy"]
            print(f"  통합 시너지: ✅ (강화시간: {syn['avg_time']:.1f}ms, LTM활용: {syn['ltm_usage']:.1%})")
        else:
            print(f"  통합 시너지: ❌")
        
        if stress_success:
            stress = self.test_results["stress"]
            print(f"  스트레스: ✅ (성공스레드: {stress['successful_threads']}/5, 작업: {stress['total_operations']}개)")
        else:
            print(f"  스트레스: ❌")
        
        # 전체 평가
        overall_success = passed_tests >= 3  # 4개 중 3개 이상 성공
        
        print(f"\n🏆 철저한 검증 결과: {'✅ 성공' if overall_success else '❌ 실패'}")
        
        if overall_success:
            print("\n🚀 Phase 1+2 통합 시스템이 철저한 검증을 통과했습니다!")
            print("   실제 운영 환경에서 안정적으로 동작할 준비가 완료되었습니다.")
        else:
            print("\n⚠️  일부 테스트가 실패했습니다. 추가 수정이 필요합니다.")
        
        # 결과를 JSON으로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"tests/performance_suite/results/comprehensive_verification_{timestamp}.json"
        
        try:
            os.makedirs(os.path.dirname(result_file), exist_ok=True)
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": timestamp,
                    "total_time": total_time,
                    "success_rate": (passed_tests/total_tests)*100,
                    "overall_success": overall_success,
                    "test_results": self.test_results
                }, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 상세 결과가 저장되었습니다: {result_file}")
            
        except Exception as e:
            print(f"\n⚠️  결과 저장 실패: {e}")
        
        return overall_success

def main():
    """메인 실행 함수"""
    verification_suite = ComprehensiveVerificationSuite()
    success = verification_suite.run_comprehensive_verification()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)