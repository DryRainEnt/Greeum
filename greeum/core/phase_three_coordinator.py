"""
Phase 3: PhaseThreeSearchCoordinator - 지능적 4층 검색 통합 조정

이 모듈은 Phase 1+2+3의 모든 구성요소를 통합하여 최적화된 검색을 제공합니다:
Layer 1: Working Memory 직접 검색
Layer 2: 캐시 확인  
Layer 3: 체크포인트 기반 지역 검색
Layer 4: 전체 LTM 검색 (fallback)
"""

import time
from typing import Dict, List, Any, Optional
from datetime import datetime


class PhaseThreeSearchCoordinator:
    """Phase 3 검색 시스템 통합 조정"""
    
    def __init__(self, hybrid_stm, cache_manager, checkpoint_manager, localized_engine, block_manager):
        self.hybrid_stm = hybrid_stm
        self.cache_manager = cache_manager
        self.checkpoint_manager = checkpoint_manager
        self.localized_engine = localized_engine
        self.block_manager = block_manager
        
        # 성능 설정
        self.min_wm_results = 3  # Working Memory 최소 결과 수
        self.min_checkpoint_results = 2  # 체크포인트 최소 결과 수
        self.auto_checkpoint_creation = True  # 자동 체크포인트 생성
        
        # 성능 모니터링
        self.stats = {
            "total_searches": 0,
            "layer_usage": {
                "working_memory": 0,
                "cache": 0, 
                "checkpoint": 0,
                "ltm_fallback": 0
            },
            "avg_search_times": {
                "working_memory": 0.0,
                "cache": 0.0,
                "checkpoint": 0.0,
                "ltm_fallback": 0.0
            },
            "search_success_rates": {
                "working_memory": 0.0,
                "cache": 0.0,
                "checkpoint": 0.0,
                "ltm_fallback": 1.0
            }
        }
        
    def intelligent_search(self, user_input: str, query_embedding: List[float], 
                         keywords: List[str], top_k: int = 5) -> Dict[str, Any]:
        """Phase 3 지능적 4층 검색"""
        search_start = time.perf_counter()
        self.stats["total_searches"] += 1
        
        print(f"🔍 Phase 3 지능적 검색 시작: '{user_input[:50]}...'")
        
        # Layer 1: Working Memory 직접 검색 (최고 속도)
        layer1_result = self._try_working_memory_search(query_embedding, search_start)
        if layer1_result:
            return layer1_result
        
        # Layer 2: 캐시 확인 (두 번째 속도)
        layer2_result = self._try_cache_search(user_input, query_embedding, keywords, search_start)
        if layer2_result:
            return layer2_result
        
        # Layer 3: 체크포인트 기반 지역 검색 (핵심 신기능)
        layer3_result = self._try_checkpoint_search(user_input, query_embedding, keywords, search_start)
        if layer3_result:
            return layer3_result
        
        # Layer 4: 전체 LTM 검색 (fallback)
        return self._fallback_ltm_search(user_input, query_embedding, keywords, search_start)
    
    def _try_working_memory_search(self, query_embedding: List[float], 
                                 search_start: float) -> Optional[Dict[str, Any]]:
        """Layer 1: Working Memory 직접 검색"""
        try:
            layer_start = time.perf_counter()
            
            wm_results = self.hybrid_stm.search_working_memory(query_embedding)
            
            layer_time = (time.perf_counter() - layer_start) * 1000
            
            if len(wm_results) >= self.min_wm_results:
                print(f"  ✅ Layer 1 (Working Memory): {len(wm_results)}개 결과, {layer_time:.2f}ms")
                
                # 체크포인트 업데이트
                self._update_checkpoints_on_success(wm_results)
                
                # 통계 업데이트
                self._update_layer_stats("working_memory", layer_time, True)
                
                return self._format_search_result(
                    wm_results, "working_memory", search_start, layer_time
                )
            else:
                print(f"  ❌ Layer 1: 결과 부족 ({len(wm_results)}/{self.min_wm_results})")
                self._update_layer_stats("working_memory", layer_time, False)
                return None
                
        except Exception as e:
            print(f"  ❌ Layer 1 오류: {str(e)}")
            return None
    
    def _try_cache_search(self, user_input: str, query_embedding: List[float], 
                        keywords: List[str], search_start: float) -> Optional[Dict[str, Any]]:
        """Layer 2: 캐시 확인"""
        try:
            layer_start = time.perf_counter()
            
            cached_results = self.cache_manager.get_cached_results(query_embedding, keywords)
            
            layer_time = (time.perf_counter() - layer_start) * 1000
            
            if cached_results:
                print(f"  ✅ Layer 2 (Cache): {len(cached_results)}개 결과, {layer_time:.2f}ms")
                
                # 통계 업데이트
                self._update_layer_stats("cache", layer_time, True)
                
                return self._format_search_result(
                    cached_results, "cache", search_start, layer_time
                )
            else:
                print(f"  ❌ Layer 2: 캐시 미스")
                self._update_layer_stats("cache", layer_time, False)
                return None
                
        except Exception as e:
            print(f"  ❌ Layer 2 오류: {str(e)}")
            return None
    
    def _try_checkpoint_search(self, user_input: str, query_embedding: List[float], 
                             keywords: List[str], search_start: float) -> Optional[Dict[str, Any]]:
        """Layer 3: 체크포인트 기반 지역 검색 (핵심)"""
        try:
            layer_start = time.perf_counter()
            
            print(f"  🎯 Layer 3 (체크포인트 지역 검색) 시작...")
            
            # 체크포인트 검색 실행
            checkpoint_results = self.localized_engine.search_with_checkpoints(
                query_embedding, 
                self.hybrid_stm.working_memory
            )
            
            layer_time = (time.perf_counter() - layer_start) * 1000
            
            if len(checkpoint_results) >= self.min_checkpoint_results:
                print(f"  ✅ Layer 3: {len(checkpoint_results)}개 결과, {layer_time:.2f}ms")
                
                # 성공한 체크포인트 검색 결과를 캐시에 직접 저장 (일관성 보장)
                try:
                    self.cache_manager.cache_search_results(query_embedding, keywords, checkpoint_results)
                except Exception as cache_error:
                    print(f"    ⚠️ 캐시 저장 실패: {str(cache_error)}")
                
                # 체크포인트 자동 생성 (다음 검색 개선용)
                if self.auto_checkpoint_creation:
                    self._create_checkpoints_from_results(checkpoint_results)
                
                # 통계 업데이트
                self._update_layer_stats("checkpoint", layer_time, True)
                
                return self._format_search_result(
                    checkpoint_results, "checkpoint", search_start, layer_time
                )
            else:
                print(f"  ❌ Layer 3: 결과 부족 ({len(checkpoint_results)}/{self.min_checkpoint_results})")
                self._update_layer_stats("checkpoint", layer_time, False)
                return None
                
        except Exception as e:
            print(f"  ❌ Layer 3 오류: {str(e)}")
            return None
    
    def _fallback_ltm_search(self, user_input: str, query_embedding: List[float], 
                           keywords: List[str], search_start: float) -> Dict[str, Any]:
        """Layer 4: 전체 LTM 검색 (fallback)"""
        try:
            layer_start = time.perf_counter()
            
            print(f"  🔄 Layer 4 (LTM Fallback) 시작...")
            
            # 전체 LTM 검색
            ltm_results = self.block_manager.search_by_embedding(query_embedding, top_k=5)
            
            layer_time = (time.perf_counter() - layer_start) * 1000
            
            print(f"  ✅ Layer 4: {len(ltm_results)}개 결과, {layer_time:.2f}ms")
            
            # fallback 결과도 캐시에 직접 저장 (일관성 보장)
            try:
                self.cache_manager.cache_search_results(query_embedding, keywords, ltm_results)
            except Exception as cache_error:
                print(f"    ⚠️ Fallback 캐시 저장 실패: {str(cache_error)}")
            
            # 체크포인트 생성 (다음 검색 개선용)
            if self.auto_checkpoint_creation and ltm_results:
                self._create_checkpoints_from_results(ltm_results)
            
            # 통계 업데이트
            self._update_layer_stats("ltm_fallback", layer_time, True)
            
            return self._format_search_result(
                ltm_results, "ltm_fallback", search_start, layer_time
            )
            
        except Exception as e:
            print(f"  ❌ Layer 4 오류: {str(e)}")
            # 최후의 빈 결과 반환
            return self._format_search_result([], "error", search_start, 0)
    
    def _update_checkpoints_on_success(self, wm_results: List[Dict[str, Any]]):
        """Working Memory 성공 시 체크포인트 접근 업데이트"""
        for result in wm_results:
            slot_id = result.get("source_slot")
            if slot_id:
                self.checkpoint_manager.update_checkpoint_access(slot_id)
    
    def _create_checkpoints_from_results(self, search_results: List[Dict[str, Any]]):
        """검색 결과로부터 체크포인트 생성"""
        try:
            active_slots = self.hybrid_stm.working_memory.get_active_slots()
            
            for slot in active_slots:
                if not hasattr(slot, 'slot_id'):
                    continue
                    
                # 기존 체크포인트가 없는 슬롯에만 생성
                existing_checkpoint = self.checkpoint_manager.get_checkpoint_info(slot.slot_id)
                
                if not existing_checkpoint and search_results:
                    # 상위 결과들로 체크포인트 생성
                    relevant_results = search_results[:5]  # 상위 5개만
                    
                    checkpoint = self.checkpoint_manager.create_checkpoint(slot, relevant_results)
                    
                    if checkpoint:
                        print(f"      📍 새 체크포인트 생성: 슬롯 {slot.slot_id}")
                        
        except Exception as e:
            print(f"    ⚠️ 체크포인트 자동 생성 실패: {str(e)}")
    
    def _format_search_result(self, results: List[Dict[str, Any]], source: str, 
                            search_start: float, layer_time: float) -> Dict[str, Any]:
        """검색 결과 포맷팅"""
        total_time = (time.perf_counter() - search_start) * 1000
        
        return {
            "results": results,
            "source": source,
            "search_time_ms": round(total_time, 3),
            "layer_time_ms": round(layer_time, 3),
            "result_count": len(results),
            "timestamp": datetime.now().isoformat(),
            "phase": "phase_3_intelligent"
        }
    
    def _update_layer_stats(self, layer: str, layer_time: float, success: bool):
        """층별 통계 업데이트"""
        if success:
            self.stats["layer_usage"][layer] += 1
        
        # 평균 시간 업데이트
        current_avg = self.stats["avg_search_times"][layer]
        usage_count = self.stats["layer_usage"][layer]
        
        if usage_count > 0:
            self.stats["avg_search_times"][layer] = (
                (current_avg * (usage_count - 1) + layer_time) / usage_count
            )
        
        # 성공률 업데이트
        total_attempts = sum(1 for _ in self.stats["layer_usage"] if self.stats["layer_usage"][layer] > 0)
        if total_attempts > 0:
            self.stats["search_success_rates"][layer] = usage_count / self.stats["total_searches"]
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Phase 3 통합 통계 반환"""
        
        # 개별 구성요소 통계 수집
        checkpoint_stats = self.checkpoint_manager.get_stats()
        localized_stats = self.localized_engine.get_stats()
        
        return {
            "phase_3_coordinator": {
                "total_searches": self.stats["total_searches"],
                "layer_usage": self.stats["layer_usage"],
                "avg_search_times_ms": self.stats["avg_search_times"],
                "layer_success_rates": self.stats["search_success_rates"]
            },
            "checkpoint_manager": checkpoint_stats,
            "localized_search": localized_stats,
            "overall_performance": {
                "most_used_layer": max(
                    self.stats["layer_usage"], 
                    key=self.stats["layer_usage"].get
                ) if self.stats["layer_usage"] else "none",
                "fastest_avg_layer": min(
                    self.stats["avg_search_times"], 
                    key=self.stats["avg_search_times"].get
                ) if any(self.stats["avg_search_times"].values()) else "none",
                "checkpoint_utilization": round(
                    checkpoint_stats.get("cache_hit_rate", 0), 3
                )
            }
        }
    
    def optimize_settings(self):
        """성능 통계 기반 설정 자동 최적화 (안전 경계값 포함)"""
        try:
            # 체크포인트 성공률이 낮으면 임계값 조정
            checkpoint_success = self.stats["search_success_rates"].get("checkpoint", 0)
            
            # 안전 경계값 정의
            MIN_SLOT_RELEVANCE = 0.1  # 최소 슬롯 관련성
            MAX_SLOT_RELEVANCE = 0.8  # 최대 슬롯 관련성  
            MIN_CHECKPOINT_RESULTS = 1  # 최소 체크포인트 결과 수
            MAX_CHECKPOINT_RESULTS = 10  # 최대 체크포인트 결과 수
            
            if checkpoint_success < 0.3:  # 30% 미만이면
                # 임계값 조정 (안전 경계값 확인)
                new_relevance = self.localized_engine.min_slot_relevance * 0.9
                if new_relevance >= MIN_SLOT_RELEVANCE:
                    self.localized_engine.min_slot_relevance = new_relevance
                    print(f"  ⚙️ 슬롯 관련성 임계값 완화: {new_relevance:.3f}")
                
                # 결과 수 조정 (안전 경계값 확인)
                new_min_results = max(MIN_CHECKPOINT_RESULTS, self.min_checkpoint_results - 1)
                if new_min_results != self.min_checkpoint_results:
                    self.min_checkpoint_results = new_min_results
                    print(f"  ⚙️ 최소 체크포인트 결과 수 완화: {new_min_results}")
            
            elif checkpoint_success > 0.8:  # 80% 이상이면
                # 임계값 조정 (안전 경계값 확인)
                new_relevance = self.localized_engine.min_slot_relevance * 1.1
                if new_relevance <= MAX_SLOT_RELEVANCE:
                    self.localized_engine.min_slot_relevance = new_relevance
                    print(f"  ⚙️ 슬롯 관련성 임계값 강화: {new_relevance:.3f}")
                
                # 결과 수 조정 (안전 경계값 확인)
                new_min_results = min(MAX_CHECKPOINT_RESULTS, self.min_checkpoint_results + 1)
                if new_min_results != self.min_checkpoint_results:
                    self.min_checkpoint_results = new_min_results
                    print(f"  ⚙️ 최소 체크포인트 결과 수 강화: {new_min_results}")
            
        except Exception as e:
            print(f"  ⚠️ 설정 자동 최적화 실패: {str(e)}")