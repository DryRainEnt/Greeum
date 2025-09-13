"""
Global Index for Branch-based Memory System
전역 점프를 위한 역색인 및 벡터 인덱스
"""

import logging
import time
from typing import Dict, List, Any, Optional, Set, Tuple
import numpy as np
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

class GlobalIndex:
    """전역 인덱스 (역색인 + 벡터)"""
    
    def __init__(self):
        # 역색인: 키워드 → 노드ID 리스트
        self.inverted_index: Dict[str, Set[str]] = defaultdict(set)
        
        # 벡터 인덱스 (간이 구현)
        self.vectors: Dict[str, np.ndarray] = {}
        self.vector_dim = 128
        
        # 노드 메타데이터 (빠른 접근용)
        self.node_meta: Dict[str, Dict] = {}
        
        # 통계
        self.stats = {
            'total_terms': 0,
            'total_nodes': 0,
            'avg_terms_per_node': 0.0
        }
        
    def add_node(self, node_id: str, content: str, 
                 root: str, created_at: float,
                 embedding: Optional[np.ndarray] = None):
        """
        노드를 전역 인덱스에 추가
        
        Args:
            node_id: 노드 ID
            content: 텍스트 내용
            root: 브랜치 루트
            created_at: 생성 시간
            embedding: 벡터 임베딩 (선택)
        """
        # 1. 키워드 추출 및 역색인 업데이트
        keywords = self._extract_keywords(content)
        for keyword in keywords:
            self.inverted_index[keyword].add(node_id)
            
        # 2. 벡터 인덱스 업데이트
        if embedding is not None:
            self.vectors[node_id] = embedding
        else:
            # 간이 임베딩 생성 (실제로는 BERT 등 사용)
            self.vectors[node_id] = self._create_simple_embedding(content)
            
        # 3. 메타데이터 저장
        self.node_meta[node_id] = {
            'root': root,
            'created_at': created_at,
            'keywords': keywords
        }
        
        # 통계 업데이트
        self.stats['total_nodes'] += 1
        self.stats['total_terms'] = len(self.inverted_index)
        
    def search_keywords(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        """
        키워드 기반 검색 (역색인)
        
        Returns:
            List of (node_id, score)
        """
        query_keywords = self._extract_keywords(query)
        if not query_keywords:
            return []
            
        # 각 노드의 매칭 점수 계산
        node_scores: Dict[str, float] = defaultdict(float)
        
        for keyword in query_keywords:
            if keyword in self.inverted_index:
                matching_nodes = self.inverted_index[keyword]
                idf = np.log(self.stats['total_nodes'] / (len(matching_nodes) + 1))
                
                for node_id in matching_nodes:
                    # TF-IDF 스코어
                    tf = 1.0  # 간단히 1로 설정
                    node_scores[node_id] += tf * idf
                    
                    # 최근성 부스트
                    if node_id in self.node_meta:
                        time_diff = time.time() - self.node_meta[node_id]['created_at']
                        recency_boost = np.exp(-time_diff / (7 * 24 * 3600))
                        node_scores[node_id] += 0.1 * recency_boost
                        
        # 상위 K개 반환
        sorted_results = sorted(node_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:limit]
    
    def search_vectors(self, query_embedding: np.ndarray, limit: int = 10) -> List[Tuple[str, float]]:
        """
        벡터 유사도 검색
        
        Args:
            query_embedding: 쿼리 벡터
            limit: 결과 개수
            
        Returns:
            List of (node_id, similarity)
        """
        if not self.vectors:
            return []
            
        similarities = []
        
        for node_id, node_vec in self.vectors.items():
            # 코사인 유사도
            sim = self._cosine_similarity(query_embedding, node_vec)
            similarities.append((node_id, sim))
            
        # 상위 K개 반환
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]
    
    def hybrid_search(self, query: str, limit: int = 10,
                     keyword_weight: float = 0.5) -> List[Tuple[str, float]]:
        """
        하이브리드 검색 (키워드 + 벡터)
        
        Args:
            query: 검색 쿼리
            limit: 결과 개수
            keyword_weight: 키워드 검색 가중치 (0~1)
            
        Returns:
            List of (node_id, combined_score)
        """
        # 1. 키워드 검색
        keyword_results = self.search_keywords(query, limit * 2)
        keyword_scores = {node_id: score for node_id, score in keyword_results}
        
        # 2. 벡터 검색
        query_embedding = self._create_simple_embedding(query)
        vector_results = self.search_vectors(query_embedding, limit * 2)
        vector_scores = {node_id: score for node_id, score in vector_results}
        
        # 3. 스코어 결합
        all_nodes = set(keyword_scores.keys()) | set(vector_scores.keys())
        combined_scores = []
        
        for node_id in all_nodes:
            k_score = keyword_scores.get(node_id, 0.0)
            v_score = vector_scores.get(node_id, 0.0)
            
            # 정규화
            k_score_norm = k_score / (max(keyword_scores.values()) + 1e-10) if keyword_scores else 0
            v_score_norm = v_score / (max(vector_scores.values()) + 1e-10) if vector_scores else 0
            
            # 가중 평균
            combined = keyword_weight * k_score_norm + (1 - keyword_weight) * v_score_norm
            combined_scores.append((node_id, combined))
            
        # 정렬 및 반환
        combined_scores.sort(key=lambda x: x[1], reverse=True)
        return combined_scores[:limit]
    
    def get_entry_points(self, query: str, limit: int = 5) -> List[str]:
        """
        전역 점프를 위한 엔트리 포인트 찾기
        
        Args:
            query: 검색 쿼리
            limit: 엔트리 포인트 개수
            
        Returns:
            List of node_ids to use as DFS starting points
        """
        # 하이브리드 검색으로 후보 찾기
        candidates = self.hybrid_search(query, limit * 3)  # 더 많은 후보
        
        # 다양성을 위해 서로 다른 루트에서 선택
        selected = []
        used_roots = set()
        
        for node_id, score in candidates:
            if node_id in self.node_meta:
                root = self.node_meta[node_id]['root']
                # 각 루트에서 하나씩 먼저 선택
                if root not in used_roots:
                    selected.append(node_id)
                    used_roots.add(root)
                    
                if len(selected) >= limit:
                    break
        
        # 부족하면 추가 선택
        if len(selected) < limit:
            for node_id, score in candidates:
                if node_id not in selected:
                    selected.append(node_id)
                    if len(selected) >= limit:
                        break
                    
        return selected
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        텍스트에서 키워드 추출 (간이 구현)
        실제로는 KeyBERT, RAKE 등 사용 권장
        """
        # 소문자 변환 및 특수문자 제거
        text = text.lower()
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        
        # 단어 분리
        words = text.split()
        
        # 불용어 제거 (간단한 예시)
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                    '이', '그', '저', '것', '수', '등', '및', '의', '를', '을'}
        keywords = [w for w in words if w not in stopwords and len(w) > 1]
        
        # 중복 제거하되 순서 유지
        seen = set()
        unique_keywords = []
        for k in keywords:
            if k not in seen:
                seen.add(k)
                unique_keywords.append(k)
                
        return unique_keywords[:20]  # 최대 20개
    
    def _create_simple_embedding(self, text: str) -> np.ndarray:
        """
        간단한 임베딩 생성 (실제로는 sentence-transformers 등 사용)
        """
        # 해시 기반 간이 임베딩
        words = self._extract_keywords(text)
        embedding = np.zeros(self.vector_dim)
        
        for word in words:
            # 각 단어를 해시하여 벡터 차원에 매핑
            hash_val = hash(word)
            indices = [hash_val % self.vector_dim, 
                      (hash_val // self.vector_dim) % self.vector_dim]
            for idx in indices:
                embedding[idx] += 1.0
                
        # L2 정규화
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """코사인 유사도 계산"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 * norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
    
    def remove_node(self, node_id: str):
        """노드 제거"""
        # 역색인에서 제거
        if node_id in self.node_meta:
            keywords = self.node_meta[node_id].get('keywords', [])
            for keyword in keywords:
                if keyword in self.inverted_index:
                    self.inverted_index[keyword].discard(node_id)
                    if not self.inverted_index[keyword]:
                        del self.inverted_index[keyword]
                        
        # 벡터 인덱스에서 제거
        if node_id in self.vectors:
            del self.vectors[node_id]
            
        # 메타데이터 제거
        if node_id in self.node_meta:
            del self.node_meta[node_id]
            
        self.stats['total_nodes'] -= 1
        
    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        stats = self.stats.copy()
        if stats['total_nodes'] > 0:
            stats['avg_terms_per_node'] = stats['total_terms'] / stats['total_nodes']
        return stats