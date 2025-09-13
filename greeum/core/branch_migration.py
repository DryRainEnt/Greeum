"""
Migration Bridge: Graph → Branch Structure
그래프 구조에서 브랜치 구조로 마이그레이션
"""

import logging
import time
from typing import Dict, List, Any, Optional, Set, Tuple
import uuid
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class BranchMigration:
    """그래프 → 브랜치 마이그레이션 브리지"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.migration_stats = {
            'total_nodes': 0,
            'migrated_nodes': 0,
            'orphan_nodes': 0,
            'cycles_removed': 0,
            'roots_created': 0,
            'xrefs_created': 0,
            'max_depth': 0,
            'avg_branching_factor': 0.0
        }
        
    def migrate_graph_to_branch(self, graph_data: List[Dict], 
                                anchors: Optional[Dict] = None) -> Dict[str, Any]:
        """
        그래프 데이터를 브랜치 구조로 변환
        
        Args:
            graph_data: 기존 그래프 노드 리스트
            anchors: 앵커 정보 (프로젝트/루트 결정용)
            
        Returns:
            migration_result: {
                'branches': Dict[root_id, List[node]],
                'stm_slots': Dict[slot, head_id],
                'xrefs': List[{from, to, type}],
                'stats': migration_stats
            }
        """
        logger.info("Starting graph to branch migration")
        start_time = time.time()
        
        # 1. 루트 결정
        roots = self._determine_roots(graph_data, anchors)
        self.migration_stats['roots_created'] = len(roots)
        
        # 2. 부모 선택 (가중치 기반)
        parent_map = self._select_parents(graph_data)
        
        # 3. 사이클 제거 (Spanning Forest)
        forest = self._create_spanning_forest(graph_data, parent_map, roots)
        
        # 4. STM 초기화 (최근 3개 노드)
        stm_slots = self._initialize_stm(graph_data)
        
        # 5. 검증 및 통계
        self._validate_migration(forest)
        
        elapsed = time.time() - start_time
        logger.info(f"Migration completed in {elapsed:.2f}s: {self.migration_stats}")
        
        return {
            'branches': forest['branches'],
            'stm_slots': stm_slots,
            'xrefs': forest['xrefs'],
            'stats': self.migration_stats
        }
    
    def _determine_roots(self, graph_data: List[Dict], 
                        anchors: Optional[Dict]) -> Dict[str, str]:
        """
        루트 노드 결정
        - 앵커가 있으면 앵커 기반
        - 없으면 강연결 컴포넌트 기반
        """
        roots = {}
        
        if anchors:
            # 앵커 기반 루트
            for anchor_id, anchor_info in anchors.items():
                root_id = f"root_{anchor_id}"
                roots[root_id] = {
                    'title': anchor_info.get('label', f'Project {anchor_id}'),
                    'nodes': []
                }
                logger.debug(f"Created root from anchor: {root_id}")
        else:
            # 모든 노드가 고아인지 확인
            all_orphans = all(
                not node.get('prev_hash') and not node.get('related_nodes') 
                for node in graph_data
            )
            
            if all_orphans:
                # 모든 노드를 default 루트로
                roots['root_default'] = {
                    'title': 'Default Branch',
                    'nodes': [node.get('id') or node.get('block_index') for node in graph_data]
                }
            else:
                # 강연결 컴포넌트 찾기
                components = self._find_strongly_connected_components(graph_data)
                for i, component in enumerate(components[:10]):  # 최대 10개 루트
                    root_id = f"root_{i}"
                    roots[root_id] = {
                        'title': f'Component {i}',
                        'nodes': component
                    }
                
        # 고아 노드용 기본 루트 (비어있는 경우)
        if not roots:
            roots['root_default'] = {
                'title': 'Default Branch',
                'nodes': []
            }
            
        return roots
    
    def _select_parents(self, graph_data: List[Dict]) -> Dict[str, str]:
        """
        각 노드의 부모 선택 (가중치 기반)
        엣지 가중치 = 시간 근접성 + 유사도 + 공출현
        """
        parent_map = {}
        edge_weights = defaultdict(lambda: defaultdict(float))
        
        # 엣지 가중치 계산
        for node in graph_data:
            node_id = node.get('id') or node.get('block_index')
            
            # 시간 기반 엣지
            if 'prev_hash' in node and node['prev_hash']:
                prev_node = self._find_node_by_hash(graph_data, node['prev_hash'])
                if prev_node:
                    prev_id = prev_node.get('id') or prev_node.get('block_index')
                    edge_weights[node_id][prev_id] += 1.0  # 시간 순서 가중치
                    
            # 유사도 기반 엣지 (있다면)
            if 'related_nodes' in node:
                for related_id, similarity in node['related_nodes'].items():
                    edge_weights[node_id][related_id] += similarity * 0.5
                    
        # 최대 가중치 엣지를 부모로 선택
        for node_id, candidates in edge_weights.items():
            if candidates:
                parent_id = max(candidates.items(), key=lambda x: x[1])[0]
                parent_map[node_id] = parent_id
                
        return parent_map
    
    def _create_spanning_forest(self, graph_data: List[Dict],
                                parent_map: Dict[str, str],
                                roots: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Spanning Forest 생성 (사이클 제거)
        
        Returns:
            {
                'branches': Dict[root_id, List[node]],
                'xrefs': List[{from, to, type}]
            }
        """
        branches = {root_id: [] for root_id in roots}
        xrefs = []
        visited = set()
        node_to_root = {}
        
        # BFS로 트리 구성
        for root_id, root_info in roots.items():
            queue = deque()
            
            # 루트에 속한 노드들을 시작점으로
            if root_info['nodes']:
                for node_id in root_info['nodes']:
                    if node_id not in visited:
                        queue.append((node_id, root_id, None))
            else:
                # 고아 노드 처리 (모든 고아 노드를 default 루트로)
                pass  # 나중에 처리
                        
            while queue:
                node_id, current_root, parent_id = queue.popleft()
                
                if node_id in visited:
                    # 사이클 감지 - xref로 처리
                    if parent_id:
                        xrefs.append({
                            'from': parent_id,
                            'to': node_id,
                            'type': 'cycle_removed'
                        })
                        self.migration_stats['cycles_removed'] += 1
                    continue
                    
                visited.add(node_id)
                node_to_root[node_id] = current_root
                
                # 노드 정보 구성
                node = self._find_node_by_id(graph_data, node_id)
                if node:
                    branch_node = {
                        'id': node_id,
                        'root': current_root,
                        'before': parent_id,
                        'after': [],
                        'content': node.get('context', ''),
                        'created_at': node.get('timestamp', time.time())
                    }
                    
                    branches[current_root].append(branch_node)
                    
                    # 부모의 after 업데이트
                    if parent_id:
                        parent_node = self._find_branch_node(branches, parent_id)
                        if parent_node:
                            parent_node['after'].append(node_id)
                    
                    # 자식 노드들 큐에 추가
                    for child_id, parent in parent_map.items():
                        if parent == node_id and child_id not in visited:
                            queue.append((child_id, current_root, node_id))
                            
        # 고아 노드 처리
        orphan_found = False
        for node in graph_data:
            node_id = node.get('id') or node.get('block_index')
            if node_id not in visited:
                orphan_found = True
                self.migration_stats['orphan_nodes'] += 1
                # 기본 루트가 없으면 생성
                if 'root_default' not in branches:
                    branches['root_default'] = []
                # 기본 루트에 추가
                branches['root_default'].append({
                    'id': node_id,
                    'root': 'root_default',
                    'before': None,
                    'after': [],
                    'content': node.get('context', ''),
                    'created_at': node.get('timestamp', time.time())
                })
                
        self.migration_stats['total_nodes'] = len(graph_data)
        self.migration_stats['migrated_nodes'] = len(visited)
        self.migration_stats['xrefs_created'] = len(xrefs)
        
        return {
            'branches': branches,
            'xrefs': xrefs
        }
    
    def _initialize_stm(self, graph_data: List[Dict]) -> Dict[str, str]:
        """
        STM 슬롯 초기화 (최근 3개 노드)
        """
        # 시간순 정렬
        sorted_nodes = sorted(
            graph_data,
            key=lambda x: x.get('timestamp', 0),
            reverse=True
        )
        
        stm_slots = {}
        slots = ['A', 'B', 'C']
        
        for i, slot in enumerate(slots):
            if i < len(sorted_nodes):
                node = sorted_nodes[i]
                node_id = node.get('id') or node.get('block_index')
                stm_slots[slot] = node_id
            else:
                stm_slots[slot] = None
                
        logger.info(f"Initialized STM slots: {stm_slots}")
        return stm_slots
    
    def _validate_migration(self, forest: Dict[str, Any]):
        """마이그레이션 검증 및 통계"""
        total_depth = 0
        max_depth = 0
        total_branching = 0
        node_count = 0
        
        for root_id, nodes in forest['branches'].items():
            for node in nodes:
                node_count += 1
                
                # 깊이 계산
                depth = self._calculate_node_depth(node, forest['branches'])
                total_depth += depth
                max_depth = max(max_depth, depth)
                
                # 분기도 계산
                branching = len(node.get('after', []))
                total_branching += branching
                
        if node_count > 0:
            self.migration_stats['max_depth'] = max_depth
            self.migration_stats['avg_branching_factor'] = total_branching / node_count
            
    def _calculate_node_depth(self, node: Dict, branches: Dict) -> int:
        """노드의 깊이 계산"""
        depth = 0
        current = node
        
        while current.get('before') and depth < 100:  # 무한루프 방지
            depth += 1
            parent_id = current['before']
            current = self._find_branch_node(branches, parent_id)
            if not current:
                break
                
        return depth
    
    def _find_node_by_id(self, graph_data: List[Dict], node_id: str) -> Optional[Dict]:
        """ID로 노드 찾기"""
        for node in graph_data:
            if (node.get('id') == node_id or 
                node.get('block_index') == node_id):
                return node
        return None
    
    def _find_node_by_hash(self, graph_data: List[Dict], hash_val: str) -> Optional[Dict]:
        """해시로 노드 찾기"""
        for node in graph_data:
            if node.get('hash') == hash_val:
                return node
        return None
    
    def _find_branch_node(self, branches: Dict, node_id: str) -> Optional[Dict]:
        """브랜치에서 노드 찾기"""
        for root_id, nodes in branches.items():
            for node in nodes:
                if node['id'] == node_id:
                    return node
        return None
    
    def _find_strongly_connected_components(self, graph_data: List[Dict]) -> List[List[str]]:
        """
        강연결 컴포넌트 찾기 (Tarjan's algorithm)
        간단한 구현 - 실제로는 networkx 등 사용 권장
        """
        # 간단히 시간 근접성 기반으로 그룹핑
        components = []
        sorted_nodes = sorted(graph_data, key=lambda x: x.get('timestamp', 0))
        
        current_component = []
        last_time = None
        
        for node in sorted_nodes:
            node_time = node.get('timestamp', 0)
            node_id = node.get('id') or node.get('block_index')
            
            if last_time is None:
                current_component = [node_id]
                last_time = node_time
            elif abs(node_time - last_time) < 3600:  # 1시간 이내
                current_component.append(node_id)
                last_time = node_time
            else:
                if current_component:
                    components.append(current_component)
                current_component = [node_id]
                last_time = node_time
                
        if current_component:
            components.append(current_component)
            
        return components