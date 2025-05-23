import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

from .block_manager import BlockManager
from .stm_manager import STMManager

class CacheManager:
    """웨이포인트 캐시를 관리하는 클래스"""
    
    def __init__(self, 
                 data_path: str = "data/context_cache.json",
                 block_manager: Optional[BlockManager] = None,
                 stm_manager: Optional[STMManager] = None):
        """
        캐시 매니저 초기화
        
        Args:
            data_path: 캐시 데이터 파일 경로
            block_manager: 블록 매니저 인스턴스 (없으면 자동 생성)
            stm_manager: STM 매니저 인스턴스 (없으면 자동 생성)
        """
        self.data_path = data_path
        self.block_manager = block_manager or BlockManager()
        self.stm_manager = stm_manager or STMManager()
        self._ensure_data_file()
        self.cache_data = self._load_cache()
        
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
        사용자 입력과 STM 기반으로 웨이포인트 캐시 업데이트
        
        Args:
            user_input: 사용자 입력
            query_embedding: 쿼리 임베딩
            extracted_keywords: 추출된 키워드
            top_k: 상위 k개 결과 반환
            
        Returns:
            업데이트된 웨이포인트 블록 목록
        """
        # 현재 컨텍스트 업데이트
        self.update_context(user_input)
        
        # 키워드 기반 검색 결과
        keyword_results = self.block_manager.search_by_keywords(extracted_keywords)
        
        # 임베딩 기반 검색 결과
        embedding_results = self.block_manager.search_by_embedding(query_embedding, top_k)
        
        # 결과 병합 및 점수 계산
        blocks_with_relevance = {}
        
        for block in keyword_results:
            block_index = block.get("block_index")
            if block_index is not None:
                blocks_with_relevance[block_index] = {
                    "block_index": block_index,
                    "relevance": 0.8  # 키워드 매치 기본 점수
                }
        
        for block in embedding_results:
            block_index = block.get("block_index")
            if block_index is not None:
                # 이미 키워드로 찾았다면 점수 합산
                if block_index in blocks_with_relevance:
                    blocks_with_relevance[block_index]["relevance"] += 0.2
                else:
                    # 임베딩으로만 찾은 경우
                    blocks_with_relevance[block_index] = {
                        "block_index": block_index,
                        "relevance": 0.7  # 임베딩 매치 기본 점수
                    }
        
        # 점수 기준 정렬
        waypoints = list(blocks_with_relevance.values())
        waypoints.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        
        # 상위 k개만 저장
        waypoints = waypoints[:top_k]
        self.update_waypoints(waypoints)
        
        # 해당 블록의 전체 정보 반환
        result_blocks = []
        for waypoint in waypoints:
            block_index = waypoint.get("block_index")
            block = self.block_manager.get_block_by_index(block_index)
            if block:
                # 관련성 정보 추가
                block["relevance"] = waypoint.get("relevance")
                result_blocks.append(block)
        
        return result_blocks
    
    def clear_cache(self) -> None:
        """캐시 초기화"""
        self.cache_data = {
            "current_context": "",
            "waypoints": [],
            "last_updated": datetime.now().isoformat()
        }
        self._save_cache() 