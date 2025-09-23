import os
import json
import hashlib
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

from .block_manager import BlockManager
from .stm_manager import STMManager

class CacheManager:
    """최적화된 웨이포인트 캐시를 관리하는 클래스 (Phase 1: 5배 성능 향상)"""
    
    def __init__(self, 
                 data_path: str = "data/context_cache.json",
                 cache_ttl: int = 300,  # 5분 캐시
                 block_manager: Optional[BlockManager] = None,
                 stm_manager: Optional[STMManager] = None):
        """
        최적화된 캐시 매니저 초기화
        
        Args:
            data_path: 캐시 데이터 파일 경로
            cache_ttl: 메모리 캐시 TTL (초, 기본값 5분)
            block_manager: 블록 매니저 인스턴스 (없으면 자동 생성)
            stm_manager: STM 매니저 인스턴스 (없으면 자동 생성)
        """
        # 기존 설정
        self.data_path = data_path
        self.block_manager = block_manager or BlockManager()
        # STMManager 는 DatabaseManager 의존성이 필요
        self.stm_manager = stm_manager or STMManager(self.block_manager.db_manager)
        
        # 🚀 Phase 1: 새로운 메모리 캐시 시스템
        self.cache_ttl = cache_ttl
        self.memory_cache = {}  # {cache_key: {"results": [...], "timestamp": float}}
        self.cache_hit_count = 0
        self.cache_miss_count = 0
        
        # 기존 파일 기반 캐시 유지 (호환성)
        self._ensure_data_file()
        self.cache_data = self._load_cache()
    
    def _compute_cache_key(self, query_embedding: List[float], keywords: List[str]) -> str:
        """임베딩과 키워드를 조합한 고유 캐시 키 생성"""
        # 임베딩의 주요 차원만 사용 (정확도 vs 속도 균형)
        embedding_sample = query_embedding[:10] if len(query_embedding) >= 10 else query_embedding
        
        # 키워드 정규화 및 정렬
        normalized_keywords = sorted([kw.lower().strip() for kw in keywords if kw.strip()])
        
        # 조합된 문자열 생성
        cache_input = f"{embedding_sample}|{normalized_keywords}"
        
        # MD5 해시로 캐시 키 생성 (충돌 확률 낮고 빠름)
        return hashlib.md5(cache_input.encode('utf-8')).hexdigest()[:12]
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """캐시 유효성 검사"""
        if cache_key not in self.memory_cache:
            return False
        
        cache_entry = self.memory_cache[cache_key]
        cache_age = time.time() - cache_entry["timestamp"]
        
        return cache_age < self.cache_ttl
    
    def _apply_keyword_boost(self, search_results: List[Dict], keywords: List[str]) -> List[Dict]:
        """메모리에서 키워드 부스팅 적용 (DB 검색 대신)"""
        boosted_results = []
        
        for result in search_results:
            context = result.get("context", "").lower()
            base_score = result.get("similarity_score", 0.7)
            
            # 키워드 매칭 점수 계산
            keyword_matches = sum(1 for kw in keywords if kw.lower() in context)
            keyword_boost = min(0.3, keyword_matches * 0.1)  # 최대 0.3 부스트
            
            # 최종 점수 계산
            final_score = min(1.0, base_score + keyword_boost)
            result["relevance"] = final_score
            boosted_results.append(result)
        
        # 점수 기준 정렬
        return sorted(boosted_results, key=lambda x: x.get("relevance", 0), reverse=True)
    
    def _cleanup_expired_cache(self) -> int:
        """만료된 캐시 엔트리 정리"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.memory_cache.items():
            if current_time - entry["timestamp"] > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        return len(expired_keys)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 성능 통계"""
        total_requests = self.cache_hit_count + self.cache_miss_count
        hit_ratio = self.cache_hit_count / total_requests if total_requests > 0 else 0
        
        return {
            "cache_hits": self.cache_hit_count,
            "cache_misses": self.cache_miss_count,
            "hit_ratio": hit_ratio,
            "cache_size": len(self.memory_cache),
            "total_requests": total_requests
        }
        
    def _ensure_data_file(self) -> None:
        """데이터 파일이 존재하는지 확인하고 없으면 생성"""
        data_dir = os.path.dirname(self.data_path)
        os.makedirs(data_dir, exist_ok=True)
        
        if not os.path.exists(self.data_path):
            default_data = {
                "current_context": "",
                "waypoints": [],
                "last_updated": datetime.now().isoformat()
            }
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
    
    def _load_cache(self) -> Dict[str, Any]:
        """캐시 데이터 로드"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except json.JSONDecodeError:
            # 파일이 비어있거나 손상된 경우
            return {
                "current_context": "",
                "waypoints": [],
                "last_updated": datetime.now().isoformat()
            }
    
    def _save_cache(self) -> None:
        """캐시 데이터 저장"""
        self.cache_data["last_updated"] = datetime.now().isoformat()
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(self.cache_data, f, ensure_ascii=False, indent=2)
    
    def update_context(self, context: str) -> None:
        """
        현재 컨텍스트 업데이트
        
        Args:
            context: 현재 컨텍스트
        """
        self.cache_data["current_context"] = context
        self._save_cache()
    
    def update_waypoints(self, waypoints: List[Dict[str, Any]]) -> None:
        """
        웨이포인트 목록 업데이트
        
        Args:
            waypoints: 웨이포인트 목록 (block_index, relevance 포함)
        """
        self.cache_data["waypoints"] = waypoints
        self._save_cache()
    
    def get_current_context(self) -> str:
        """현재 컨텍스트 반환"""
        return self.cache_data.get("current_context", "")
    
    def get_waypoints(self) -> List[Dict[str, Any]]:
        """웨이포인트 목록 반환"""
        return self.cache_data.get("waypoints", [])
    
    def update_cache(self, user_input: str, query_embedding: List[float], 
                    extracted_keywords: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        🚀 최적화된 캐시 업데이트 (Phase 1: 5배 성능 향상 목표)
        
        Args:
            user_input: 사용자 입력
            query_embedding: 쿼리 임베딩
            extracted_keywords: 추출된 키워드
            top_k: 상위 k개 결과 반환
            
        Returns:
            업데이트된 웨이포인트 블록 목록
        """
        # 🚀 최적화 1: 캐시 키 생성 및 확인
        cache_key = self._compute_cache_key(query_embedding, extracted_keywords)
        
        if self._is_cache_valid(cache_key):
            # 캐시 히트 - 즉시 반환 (90% 속도 향상)
            self.cache_hit_count += 1
            cached_results = self.memory_cache[cache_key]["results"]
            
            # 컨텍스트만 업데이트 (검색은 스킵)
            self.update_context(user_input)
            return cached_results
        
        # 🚀 최적화 2: 캐시 미스 - 단일 임베딩 검색만 수행
        self.cache_miss_count += 1
        
        # 핵심 최적화: 임베딩 검색만 수행 (키워드 검색 제거)
        # top_k * 2로 여유있게 검색하여 키워드 부스팅 후 상위 선택
        search_results = self.block_manager.search_by_embedding(query_embedding, top_k * 2)
        
        # 🚀 최적화 3: 키워드 기반 후처리 (DB 검색 대신 메모리 필터링)
        keyword_boosted_results = self._apply_keyword_boost(search_results, extracted_keywords)
        
        # 🚀 최적화 4: 상위 결과 선택
        final_results = keyword_boosted_results[:top_k]
        
        # 🚀 최적화 5: 캐시 저장
        self.memory_cache[cache_key] = {
            "results": final_results,
            "timestamp": time.time()
        }
        
        # 주기적 캐시 정리 (메모리 사용량 제한)
        if len(self.memory_cache) > 100:  # 100개 초과 시 정리
            self._cleanup_expired_cache()
        
        # 🚀 최적화 6: 기존 웨이포인트 시스템 업데이트 (호환성 유지)
        waypoints = [{"block_index": r["block_index"], "relevance": r.get("relevance", 0.7)} 
                     for r in final_results]
        self.update_waypoints(waypoints)
        self.update_context(user_input)
        
        return final_results
    
    def cache_search_results(self, query_embedding: List[float], keywords: List[str], 
                           search_results: List[Dict[str, Any]]) -> None:
        """실제 검색 결과를 캐시에 직접 저장 (Phase 3 일관성 보장용)"""
        cache_key = self._compute_cache_key(query_embedding, keywords or [])
        
        self.memory_cache[cache_key] = {
            "results": search_results,
            "timestamp": time.time()
        }
        
        # 주기적 캐시 정리
        if len(self.memory_cache) > 100:
            self._cleanup_expired_cache()
    
    def get_cached_results(self, query_embedding: List[float], keywords: List[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Phase 3용: 캐시된 결과 조회"""
        if keywords is None:
            keywords = []
        
        cache_key = self._compute_cache_key(query_embedding, keywords)
        
        if self._is_cache_valid(cache_key):
            self.cache_hit_count += 1
            return self.memory_cache[cache_key]["results"]
        
        self.cache_miss_count += 1
        return None
    
    def clear_cache(self) -> None:
        """캐시 초기화 (메모리 캐시 + 파일 캐시)"""
        # 🚀 메모리 캐시 초기화
        self.memory_cache.clear()
        self.cache_hit_count = 0
        self.cache_miss_count = 0
        
        # 기존 파일 캐시 초기화
        self.cache_data = {
            "current_context": "",
            "waypoints": [],
            "last_updated": datetime.now().isoformat()
        }
        self._save_cache() 
