"""
BlockManager에 GraphIndex를 통합하는 패치
GREEN 단계: 테스트를 통과시킬 최소 구현
"""

from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def patch_block_manager_with_graphindex(BlockManager):
    """BlockManager 클래스에 GraphIndex 기능을 추가하는 몽키 패치"""
    
    # 원본 __init__ 저장
    original_init = BlockManager.__init__
    
    def new_init(self, db_manager):
        """GraphIndex를 포함하는 새로운 초기화"""
        # 원본 초기화 실행
        original_init(self, db_manager)
        
        # GraphIndex 추가
        from ..graph.index import GraphIndex
        self.graph_index = GraphIndex()
        
        # 자동 부트스트랩 시도
        try:
            self._auto_bootstrap_graph_index()
        except Exception as e:
            logger.debug(f"Auto-bootstrap skipped: {e}")
    
    # 원본 _search_local_graph 저장
    original_search_local_graph = BlockManager._search_local_graph
    
    def new_search_local_graph(self, anchor_block: int, radius: int, query: str, limit: int) -> List[Dict[str, Any]]:
        """GraphIndex.beam_search를 사용하는 새로운 그래프 탐색"""
        
        # GraphIndex가 있고 사용 가능한 경우
        if hasattr(self, 'graph_index') and self.graph_index:
            try:
                # beam_search를 위한 목표 함수
                def is_goal(node_id: str) -> bool:
                    try:
                        block_idx = int(node_id)
                        block = self.db_manager.get_block_by_index(block_idx)
                        if block:
                            return self._matches_query(block, query)
                    except:
                        pass
                    return False
                
                # GraphIndex beam_search 사용
                hit_nodes = self.graph_index.beam_search(
                    start=str(anchor_block),
                    is_goal=is_goal,
                    beam=32,
                    max_hop=radius
                )
                
                # 결과 변환
                results = []
                for i, node_id in enumerate(hit_nodes[:limit]):
                    block_idx = int(node_id)
                    block = self.db_manager.get_block_by_index(block_idx)
                    if block:
                        block_dict = block.to_dict() if hasattr(block, 'to_dict') else block
                        block_dict['hop_distance'] = i  # 실제 거리는 beam_search가 추적해야 함
                        block_dict['anchor_block'] = anchor_block
                        results.append(block_dict)
                
                return results
                
            except Exception as e:
                logger.debug(f"GraphIndex search failed, falling back to BFS: {e}")
        
        # Fallback: 원본 BFS 사용
        return original_search_local_graph(self, anchor_block, radius, query, limit)
    
    # 원본 add_block 저장
    original_add_block = BlockManager.add_block
    
    def new_add_block(self, context: str, keywords: List[str], tags: List[str], 
                      embedding: List[float], importance: float = 0.5, **metadata) -> int:
        """GraphIndex를 업데이트하는 새로운 블록 추가"""
        
        # 원본 add_block 실행
        new_block_index = original_add_block(
            self, context, keywords, tags, embedding, importance, **metadata
        )
        
        # GraphIndex에 노드 추가
        if hasattr(self, 'graph_index') and self.graph_index:
            try:
                node_id = str(new_block_index)
                
                # 노드가 없으면 추가
                if node_id not in self.graph_index.adj:
                    self.graph_index.adj[node_id] = []
                
                # Near-Anchor Write 시 엣지 추가
                # (update_block_links가 호출되면 자동으로 처리됨)
                
            except Exception as e:
                logger.debug(f"Failed to update GraphIndex: {e}")
        
        return new_block_index
    
    # 원본 update_block_links 저장
    original_update_block_links = BlockManager.update_block_links
    
    def new_update_block_links(self, block_index: int, neighbors: List[int]) -> bool:
        """GraphIndex도 함께 업데이트하는 링크 업데이트"""
        
        # 원본 update_block_links 실행
        success = original_update_block_links(self, block_index, neighbors)
        
        # GraphIndex 업데이트
        if success and hasattr(self, 'graph_index') and self.graph_index:
            try:
                node_id = str(block_index)
                
                # 노드가 없으면 추가
                if node_id not in self.graph_index.adj:
                    self.graph_index.adj[node_id] = []
                
                # 이웃 추가 (중복 제거)
                existing_neighbors = {n[0] for n in self.graph_index.adj[node_id]}
                
                for neighbor_idx in neighbors:
                    neighbor_id = str(neighbor_idx)
                    if neighbor_id not in existing_neighbors:
                        # 가중치 1.0으로 추가
                        self.graph_index.adj[node_id].append((neighbor_id, 1.0))
                        
                        # 양방향 엣지 (이웃에도 추가)
                        if neighbor_id not in self.graph_index.adj:
                            self.graph_index.adj[neighbor_id] = []
                        
                        neighbor_existing = {n[0] for n in self.graph_index.adj[neighbor_id]}
                        if node_id not in neighbor_existing:
                            self.graph_index.adj[neighbor_id].append((node_id, 1.0))
                
                # 가중치 기준 정렬 (상위 k개만 유지)
                self.graph_index.adj[node_id].sort(key=lambda x: x[1], reverse=True)
                self.graph_index.adj[node_id] = self.graph_index.adj[node_id][:self.graph_index.kmax]
                
            except Exception as e:
                logger.debug(f"Failed to update GraphIndex links: {e}")
        
        return success
    
    def bootstrap_graph_index(self):
        """기존 블록들로부터 GraphIndex를 부트스트랩"""
        if not hasattr(self, 'graph_index'):
            from ..graph.index import GraphIndex
            self.graph_index = GraphIndex()
        
        logger.info("Bootstrapping GraphIndex from existing blocks...")
        
        # 모든 블록 가져오기
        blocks = self.get_blocks(limit=10000)  # 실제로는 페이징 필요
        
        for block in blocks:
            block_idx = block.get('block_index')
            if block_idx is None:
                continue
            
            node_id = str(block_idx)
            
            # 노드 추가
            if node_id not in self.graph_index.adj:
                self.graph_index.adj[node_id] = []
            
            # 메타데이터에서 링크 정보 추출
            metadata = block.get('metadata', {})
            links = metadata.get('links', {})
            neighbors = links.get('neighbors', [])
            
            for neighbor in neighbors:
                if isinstance(neighbor, dict):
                    neighbor_id = str(neighbor.get('id'))
                    weight = neighbor.get('weight', 1.0)
                else:
                    neighbor_id = str(neighbor)
                    weight = 1.0
                
                # 엣지 추가 (중복 체크)
                existing = {n[0] for n in self.graph_index.adj[node_id]}
                if neighbor_id not in existing:
                    self.graph_index.adj[node_id].append((neighbor_id, weight))
        
        # 모든 노드의 이웃 정렬 및 제한
        for node_id in self.graph_index.adj:
            self.graph_index.adj[node_id].sort(key=lambda x: x[1], reverse=True)
            self.graph_index.adj[node_id] = self.graph_index.adj[node_id][:self.graph_index.kmax]
        
        logger.info(f"GraphIndex bootstrapped with {len(self.graph_index.adj)} nodes")
    
    def bootstrap_and_save_graph(self, output_path):
        """GraphIndex를 부트스트랩하고 스냅샷 저장"""
        self.bootstrap_graph_index()
        
        # 스냅샷 저장
        from ..graph.snapshot import save_graph_snapshot
        
        # 파라미터 준비
        params = {
            "theta": self.graph_index.theta,
            "kmax": self.graph_index.kmax,
            "alpha": 0.7,  # 기본값
            "beta": 0.2,
            "gamma": 0.1
        }
        
        save_graph_snapshot(self.graph_index.adj, params, output_path)
        
        return output_path
    
    def _auto_bootstrap_graph_index(self):
        """첫 실행 시 자동 부트스트랩"""
        # 기존 블록이 있는지 확인
        blocks = self.get_blocks(limit=1)
        if blocks and len(self.graph_index.adj) == 0:
            # GraphIndex가 비어있으면 부트스트랩
            self.bootstrap_graph_index()
    
    # 메서드 교체
    BlockManager.__init__ = new_init
    BlockManager._search_local_graph = new_search_local_graph
    BlockManager.add_block = new_add_block
    BlockManager.update_block_links = new_update_block_links
    BlockManager.bootstrap_graph_index = bootstrap_graph_index
    BlockManager.bootstrap_and_save_graph = bootstrap_and_save_graph
    BlockManager._auto_bootstrap_graph_index = _auto_bootstrap_graph_index
    
    return BlockManager