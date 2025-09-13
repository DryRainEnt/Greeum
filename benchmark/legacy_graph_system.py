"""
Legacy Graph-based Memory System (Baseline)
기존 그래프 기반 메모리 시스템 (비교 기준점)
"""

import time
import uuid
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
import numpy as np
from collections import defaultdict, deque
import json
import hashlib

logger = logging.getLogger(__name__)

class LegacyGraphNode:
    """기존 그래프 노드"""
    
    def __init__(self, node_id: str, content: str, timestamp: float = None):
        self.id = node_id
        self.content = content
        self.timestamp = timestamp or time.time()
        self.edges = {}  # target_id -> weight
        self.visit_count = 0
        self.embeddings = self._simple_embedding(content)
        
    def _simple_embedding(self, text: str) -> np.ndarray:
        """간단한 텍스트 임베딩"""
        words = text.lower().split()
        embedding = np.zeros(64)  # 작은 차원
        for word in words:
            hash_val = hash(word)
            indices = [hash_val % 64, (hash_val // 64) % 64]
            for idx in indices:
                embedding[idx] += 1.0
        norm = np.linalg.norm(embedding)
        return embedding / norm if norm > 0 else embedding
    
    def add_edge(self, target_id: str, weight: float = 1.0):
        """엣지 추가"""
        self.edges[target_id] = weight
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'content': self.content,
            'timestamp': self.timestamp,
            'edges': self.edges,
            'visit_count': self.visit_count
        }


class LegacyGraphManager:
    """기존 그래프 기반 메모리 매니저"""
    
    def __init__(self):
        self.nodes: Dict[str, LegacyGraphNode] = {}
        self.recent_nodes: List[str] = []  # LRU 형태
        self.max_recent = 100
        
        # 성능 메트릭
        self.metrics = {
            'total_searches': 0,
            'total_hops': 0,
            'avg_hops': 0.0,
            'search_times': [],
            'avg_search_time': 0.0,
            'hit_rate': 0.0,
            'total_hits': 0
        }
        
    def add_node(self, content: str, connect_to_recent: int = 3) -> str:
        """
        노드 추가 (기존 방식)
        최근 노드들과 자동 연결
        """
        node_id = str(uuid.uuid4())
        node = LegacyGraphNode(node_id, content)
        
        # 최근 노드들과 연결 (전통적 그래프 방식)
        for recent_id in self.recent_nodes[-connect_to_recent:]:
            if recent_id in self.nodes:
                # 양방향 연결
                similarity = self._calculate_similarity(node, self.nodes[recent_id])
                if similarity > 0.1:  # 최소 유사도
                    node.add_edge(recent_id, similarity)
                    self.nodes[recent_id].add_edge(node_id, similarity)
        
        self.nodes[node_id] = node
        self.recent_nodes.append(node_id)
        
        # LRU 크기 제한
        if len(self.recent_nodes) > self.max_recent:
            self.recent_nodes = self.recent_nodes[-self.max_recent:]
            
        return node_id
    
    def search(self, query: str, max_results: int = 10, max_hops: int = 6) -> Tuple[List[Dict], Dict]:
        """
        전통적인 그래프 검색 (BFS + 유사도)
        """
        start_time = time.time()
        self.metrics['total_searches'] += 1
        
        # 시작점들 (최근 노드들에서)
        start_points = self.recent_nodes[-5:] if self.recent_nodes else []
        
        if not start_points:
            return [], {'search_type': 'empty', 'hops': 0, 'time_ms': 0}
        
        # BFS with 유사도 스코어링
        visited = set()
        queue = deque()
        results = []
        total_hops = 0
        
        # 시작점들을 큐에 추가
        for start_id in start_points:
            if start_id in self.nodes:
                queue.append((start_id, 0))  # (node_id, hop_count)
        
        while queue and len(results) < max_results * 2:
            node_id, hop_count = queue.popleft()
            
            if node_id in visited or hop_count > max_hops:
                continue
                
            visited.add(node_id)
            total_hops += 1
            
            if node_id not in self.nodes:
                continue
                
            node = self.nodes[node_id]
            node.visit_count += 1
            
            # 유사도 계산
            similarity = self._query_similarity(query, node.content)
            if similarity > 0:
                results.append({
                    'node': node.to_dict(),
                    'score': similarity,
                    'hops': hop_count
                })
            
            # 인접 노드들을 큐에 추가
            for neighbor_id, edge_weight in node.edges.items():
                if neighbor_id not in visited:
                    queue.append((neighbor_id, hop_count + 1))
        
        # 정렬 및 상위 결과 선택
        results.sort(key=lambda x: x['score'], reverse=True)
        final_results = results[:max_results]
        
        # 메트릭 업데이트
        search_time = (time.time() - start_time) * 1000
        self.metrics['total_hops'] += total_hops
        self.metrics['avg_hops'] = self.metrics['total_hops'] / self.metrics['total_searches']
        self.metrics['search_times'].append(search_time)
        self.metrics['avg_search_time'] = sum(self.metrics['search_times']) / len(self.metrics['search_times'])
        
        if final_results:
            self.metrics['total_hits'] += 1
        self.metrics['hit_rate'] = self.metrics['total_hits'] / self.metrics['total_searches']
        
        return final_results, {
            'search_type': 'graph_bfs',
            'hops': total_hops,
            'time_ms': search_time,
            'visited_nodes': len(visited)
        }
    
    def _calculate_similarity(self, node1: LegacyGraphNode, node2: LegacyGraphNode) -> float:
        """노드 간 유사도"""
        # 벡터 유사도
        vec_sim = np.dot(node1.embeddings, node2.embeddings)
        
        # 키워드 유사도
        words1 = set(node1.content.lower().split())
        words2 = set(node2.content.lower().split())
        if words1 and words2:
            keyword_sim = len(words1 & words2) / len(words1 | words2)
        else:
            keyword_sim = 0.0
        
        # 시간 근접성
        time_diff = abs(node1.timestamp - node2.timestamp)
        time_sim = np.exp(-time_diff / (24 * 3600))  # 1일 반감기
        
        return 0.5 * vec_sim + 0.3 * keyword_sim + 0.2 * time_sim
    
    def _query_similarity(self, query: str, content: str) -> float:
        """쿼리-내용 유사도"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words or not content_words:
            return 0.0
            
        # Jaccard 유사도 + 키워드 매칭 보너스
        jaccard = len(query_words & content_words) / len(query_words | content_words)
        
        # 정확한 키워드 매칭 보너스
        exact_matches = sum(1 for word in query_words if word in content.lower())
        match_bonus = exact_matches / len(query_words)
        
        return 0.7 * jaccard + 0.3 * match_bonus
    
    def get_metrics(self) -> Dict[str, Any]:
        """메트릭 반환"""
        return self.metrics.copy()
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """그래프 통계"""
        total_edges = sum(len(node.edges) for node in self.nodes.values())
        avg_degree = total_edges / len(self.nodes) if self.nodes else 0
        
        return {
            'total_nodes': len(self.nodes),
            'total_edges': total_edges,
            'avg_degree': avg_degree,
            'recent_nodes_count': len(self.recent_nodes)
        }