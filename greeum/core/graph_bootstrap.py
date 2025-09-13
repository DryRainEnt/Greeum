#!/usr/bin/env python3
"""
Graph Bootstrap System for Greeum v3.0.0

블록 간 자동 링크 생성 및 그래프 네트워크 초기화를 담당하는 모듈
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class GraphBootstrap:
    """그래프 부트스트랩 시스템"""
    
    def __init__(self, db_manager, block_manager):
        """
        초기화
        
        Args:
            db_manager: DatabaseManager 인스턴스
            block_manager: BlockManager 인스턴스
        """
        self.db_manager = db_manager
        self.block_manager = block_manager
        
        # 부트스트랩 설정
        self.config = {
            'similarity_threshold': 0.7,  # 유사도 임계값
            'temporal_window': 3600,  # 시간 윈도우 (초)
            'max_links_per_block': 5,  # 블록당 최대 링크 수
            'keyword_weight': 0.3,  # 키워드 가중치
            'embedding_weight': 0.5,  # 임베딩 가중치
            'temporal_weight': 0.2,  # 시간적 근접성 가중치
        }
        
        self.stats = {
            'blocks_processed': 0,
            'links_created': 0,
            'clusters_found': 0,
            'average_similarity': 0.0
        }
    
    def bootstrap_graph(self, last_n_blocks: int = 100, force: bool = False) -> Dict[str, Any]:
        """
        최근 N개 블록에 대해 그래프 부트스트랩 수행
        
        Args:
            last_n_blocks: 처리할 최근 블록 수
            force: 기존 링크 무시하고 재생성
            
        Returns:
            부트스트랩 결과 통계
        """
        logger.info(f"Starting graph bootstrap for last {last_n_blocks} blocks")
        
        # 최근 블록 가져오기
        blocks = self.db_manager.get_blocks(limit=last_n_blocks, sort_by='block_index', order='desc')
        
        if not blocks:
            logger.warning("No blocks found for bootstrap")
            return self.stats
        
        # 블록 간 유사도 계산 및 링크 생성
        for i, block1 in enumerate(blocks):
            block1_id = block1.get('block_index')
            
            # 이미 링크가 있고 force가 False면 스킵
            if not force:
                existing_links = self.block_manager.get_block_neighbors(block1_id)
                if existing_links and len(existing_links) >= self.config['max_links_per_block']:
                    continue
            
            # 유사한 블록 찾기
            similar_blocks = self._find_similar_blocks(block1, blocks[i+1:])
            
            # 상위 K개 블록과 링크 생성
            for block2_id, similarity in similar_blocks[:self.config['max_links_per_block']]:
                if similarity >= self.config['similarity_threshold']:
                    # 양방향 링크 생성
                    self.block_manager.update_block_links(block1_id, [block2_id])
                    self.block_manager.update_block_links(block2_id, [block1_id])
                    self.stats['links_created'] += 1
                    logger.debug(f"Created link: {block1_id} <-> {block2_id} (similarity: {similarity:.3f})")
            
            self.stats['blocks_processed'] += 1
        
        # 클러스터 감지
        self._detect_clusters(blocks)
        
        logger.info(f"Bootstrap completed: {self.stats}")
        return self.stats
    
    def _find_similar_blocks(self, target_block: Dict[str, Any], 
                            candidate_blocks: List[Dict[str, Any]]) -> List[Tuple[int, float]]:
        """
        타겟 블록과 유사한 블록들 찾기
        
        Args:
            target_block: 대상 블록
            candidate_blocks: 후보 블록들
            
        Returns:
            [(block_id, similarity), ...] 정렬된 리스트
        """
        similarities = []
        
        target_embedding = np.array(target_block.get('embedding', []))
        target_keywords = set(target_block.get('keywords', []))
        target_timestamp = self._parse_timestamp(target_block.get('timestamp'))
        
        for block in candidate_blocks:
            block_id = block.get('block_index')
            
            # 임베딩 유사도
            embedding_sim = 0.0
            if len(target_embedding) > 0:
                block_embedding = np.array(block.get('embedding', []))
                if len(block_embedding) == len(target_embedding):
                    embedding_sim = self._cosine_similarity(target_embedding, block_embedding)
            
            # 키워드 유사도
            block_keywords = set(block.get('keywords', []))
            keyword_sim = self._jaccard_similarity(target_keywords, block_keywords)
            
            # 시간적 근접성
            block_timestamp = self._parse_timestamp(block.get('timestamp'))
            temporal_sim = self._temporal_similarity(target_timestamp, block_timestamp)
            
            # 종합 유사도 계산
            total_similarity = (
                self.config['embedding_weight'] * embedding_sim +
                self.config['keyword_weight'] * keyword_sim +
                self.config['temporal_weight'] * temporal_sim
            )
            
            similarities.append((block_id, total_similarity))
            self.stats['average_similarity'] += total_similarity
        
        # 유사도 기준 정렬
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        if len(similarities) > 0:
            self.stats['average_similarity'] /= len(similarities)
        
        return similarities
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """코사인 유사도 계산"""
        if len(vec1) == 0 or len(vec2) == 0:
            return 0.0
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _jaccard_similarity(self, set1: set, set2: set) -> float:
        """자카드 유사도 계산"""
        if not set1 and not set2:
            return 0.0
        
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _temporal_similarity(self, time1: Optional[datetime], 
                           time2: Optional[datetime]) -> float:
        """시간적 근접성 계산"""
        if not time1 or not time2:
            return 0.0
        
        time_diff = abs((time1 - time2).total_seconds())
        
        # 시간 윈도우 내에서 선형적으로 감소
        if time_diff <= self.config['temporal_window']:
            return 1.0 - (time_diff / self.config['temporal_window'])
        
        return 0.0
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """타임스탬프 파싱"""
        if not timestamp_str:
            return None
        
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return None
    
    def _detect_clusters(self, blocks: List[Dict[str, Any]]):
        """
        연결된 컴포넌트(클러스터) 감지
        
        Args:
            blocks: 블록 리스트
        """
        # 인접 리스트 구성
        adjacency = defaultdict(set)
        block_ids = {block['block_index'] for block in blocks}
        
        for block_id in block_ids:
            neighbors = self.block_manager.get_block_neighbors(block_id)
            if neighbors:
                for neighbor_id in neighbors:
                    if neighbor_id in block_ids:
                        adjacency[block_id].add(neighbor_id)
                        adjacency[neighbor_id].add(block_id)
        
        # DFS로 연결된 컴포넌트 찾기
        visited = set()
        clusters = []
        
        for block_id in block_ids:
            if block_id not in visited:
                cluster = self._dfs_cluster(block_id, adjacency, visited)
                if len(cluster) > 1:  # 2개 이상 연결된 경우만 클러스터로 간주
                    clusters.append(cluster)
        
        self.stats['clusters_found'] = len(clusters)
        
        # 클러스터 정보 로깅
        for i, cluster in enumerate(clusters):
            logger.info(f"Cluster {i+1}: {len(cluster)} blocks connected")
    
    def _dfs_cluster(self, start_id: int, adjacency: Dict[int, set], 
                    visited: set) -> List[int]:
        """DFS로 연결된 컴포넌트 탐색"""
        stack = [start_id]
        cluster = []
        
        while stack:
            node = stack.pop()
            if node not in visited:
                visited.add(node)
                cluster.append(node)
                
                for neighbor in adjacency.get(node, []):
                    if neighbor not in visited:
                        stack.append(neighbor)
        
        return cluster
    
    def get_graph_snapshot(self) -> Dict[str, Any]:
        """
        현재 그래프 상태 스냅샷 생성
        
        Returns:
            그래프 스냅샷 데이터
        """
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats.copy(),
            'config': self.config.copy(),
            'nodes': [],
            'edges': []
        }
        
        # 모든 블록 정보 수집
        blocks = self.db_manager.get_blocks(limit=1000)
        
        for block in blocks:
            block_id = block['block_index']
            
            # 노드 정보
            node = {
                'id': block_id,
                'context': block.get('context', '')[:100],
                'keywords': block.get('keywords', []),
                'importance': block.get('importance', 0.5),
                'timestamp': block.get('timestamp', '')
            }
            snapshot['nodes'].append(node)
            
            # 엣지 정보
            neighbors = self.block_manager.get_block_neighbors(block_id)
            if neighbors:
                for neighbor_id in neighbors:
                    # 중복 엣지 방지 (작은 ID -> 큰 ID)
                    if block_id < neighbor_id:
                        edge = {
                            'source': block_id,
                            'target': neighbor_id,
                            'weight': 1.0  # 추후 가중치 계산 가능
                        }
                        snapshot['edges'].append(edge)
        
        snapshot['stats']['total_nodes'] = len(snapshot['nodes'])
        snapshot['stats']['total_edges'] = len(snapshot['edges'])
        
        return snapshot
    
    def restore_from_snapshot(self, snapshot: Dict[str, Any]) -> bool:
        """
        스냅샷에서 그래프 복원
        
        Args:
            snapshot: 그래프 스냅샷 데이터
            
        Returns:
            복원 성공 여부
        """
        try:
            edges = snapshot.get('edges', [])
            
            for edge in edges:
                source = edge['source']
                target = edge['target']
                
                # 양방향 링크 복원
                self.block_manager.update_block_links(source, [target])
                self.block_manager.update_block_links(target, [source])
            
            logger.info(f"Restored {len(edges)} edges from snapshot")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore from snapshot: {e}")
            return False