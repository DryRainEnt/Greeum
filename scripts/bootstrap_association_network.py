#!/usr/bin/env python3
"""
기존 블록들에 대해 AssociationNetwork 부트스트랩
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.core.association_network import AssociationNetwork
from greeum.core.spreading_activation import SpreadingActivation
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_keyword_similarity(keywords1, keywords2):
    """키워드 집합 간 Jaccard 유사도 계산"""
    set1 = set(keywords1)
    set2 = set(keywords2)
    if not set1 and not set2:
        return 0.0
    intersection = set1 & set2
    union = set1 | set2
    return len(intersection) / len(union) if union else 0.0

def calculate_embedding_similarity(emb1, emb2):
    """임베딩 간 코사인 유사도 계산"""
    if not emb1 or not emb2 or len(emb1) != len(emb2):
        return 0.0
    
    vec1 = np.array(emb1)
    vec2 = np.array(emb2)
    
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return np.dot(vec1, vec2) / (norm1 * norm2)

def calculate_temporal_distance(timestamp1, timestamp2):
    """두 타임스탬프 간 시간 거리 (시간 단위)"""
    try:
        t1 = datetime.fromisoformat(timestamp1.replace('Z', '+00:00'))
        t2 = datetime.fromisoformat(timestamp2.replace('Z', '+00:00'))
        diff = abs((t1 - t2).total_seconds()) / 3600  # 시간 단위
        return diff
    except:
        return float('inf')

def bootstrap_association_network():
    """기존 블록들에 대해 AssociationNetwork 부트스트랩"""
    
    print("=" * 60)
    print("AssociationNetwork 부트스트랩 시작")
    print("=" * 60)
    
    # 데이터베이스 연결
    db_manager = DatabaseManager()
    
    # AssociationNetwork 직접 초기화
    association_network = AssociationNetwork(db_manager)
    spreading_activation = SpreadingActivation(association_network, db_manager)
    
    print(f"\n초기 상태:")
    print(f"  - 기존 노드 수: {len(association_network.nodes)}")
    print(f"  - 기존 연결 수: {len(association_network.associations)}")
    
    # 모든 블록 가져오기
    cursor = db_manager.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM blocks")
    total_blocks = cursor.fetchone()[0]
    print(f"  - 전체 블록 수: {total_blocks}")
    
    # 배치 처리
    batch_size = 100
    processed = 0
    created_nodes = 0
    created_associations = 0
    
    print(f"\n1단계: 노드 생성 중...")
    
    for offset in range(0, total_blocks, batch_size):
        blocks = db_manager.get_blocks(limit=batch_size, offset=offset)
        
        for block in blocks:
            block_idx = block['block_index']
            
            # 이미 노드가 있는지 확인
            node_exists = any(node.memory_id == block_idx for node in association_network.nodes.values())
            
            if not node_exists:
                # 노드 생성
                node = association_network.create_node(
                    content=block['context'],
                    node_type='memory',
                    memory_id=block_idx,
                    embedding=block.get('embedding', [])
                )
                created_nodes += 1
                
                if created_nodes % 100 == 0:
                    print(f"    {created_nodes} 노드 생성됨...")
        
        processed += len(blocks)
    
    print(f"  ✅ {created_nodes}개 노드 생성 완료")
    
    # 2단계: 연상 관계 생성
    print(f"\n2단계: 연상 관계 생성 중...")
    
    # 노드를 블록 인덱스 순으로 정렬
    sorted_nodes = sorted(
        association_network.nodes.values(),
        key=lambda n: n.memory_id if n.memory_id is not None else float('inf')
    )
    
    # 설정값
    temporal_window_hours = 24  # 24시간 이내
    keyword_similarity_threshold = 0.2
    embedding_similarity_threshold = 0.7
    max_associations_per_node = 5
    
    for i, node in enumerate(sorted_nodes):
        if node.memory_id is None:
            continue
            
        # 이 노드의 블록 정보 가져오기
        block = db_manager.get_block(node.memory_id)
        if not block:
            continue
        
        node_associations = 0
        
        # 근처 노드들과 비교 (전후 50개씩)
        start_idx = max(0, i - 50)
        end_idx = min(len(sorted_nodes), i + 50)
        
        candidates = []
        
        for j in range(start_idx, end_idx):
            if i == j:  # 자기 자신 제외
                continue
                
            other_node = sorted_nodes[j]
            if other_node.memory_id is None:
                continue
            
            # 이미 연결이 있는지 확인
            existing = any(
                (assoc.source_node_id == node.node_id and assoc.target_node_id == other_node.node_id) or
                (assoc.source_node_id == other_node.node_id and assoc.target_node_id == node.node_id)
                for assoc in association_network.associations.values()
            )
            
            if existing:
                continue
            
            other_block = db_manager.get_block(other_node.memory_id)
            if not other_block:
                continue
            
            # 유사도 계산
            scores = {}
            
            # 1. 키워드 유사도
            keyword_sim = calculate_keyword_similarity(
                block.get('keywords', []),
                other_block.get('keywords', [])
            )
            if keyword_sim > keyword_similarity_threshold:
                scores['keyword'] = keyword_sim
            
            # 2. 임베딩 유사도
            if block.get('embedding') and other_block.get('embedding'):
                embedding_sim = calculate_embedding_similarity(
                    block['embedding'],
                    other_block['embedding']
                )
                if embedding_sim > embedding_similarity_threshold:
                    scores['embedding'] = embedding_sim
            
            # 3. 시간적 근접성
            temporal_dist = calculate_temporal_distance(
                block['timestamp'],
                other_block['timestamp']
            )
            if temporal_dist < temporal_window_hours:
                # 거리가 가까울수록 높은 점수
                temporal_score = 1.0 - (temporal_dist / temporal_window_hours)
                scores['temporal'] = temporal_score
            
            # 종합 점수 계산
            if scores:
                # 가중 평균
                weights = {'keyword': 0.4, 'embedding': 0.4, 'temporal': 0.2}
                total_score = sum(
                    scores.get(key, 0) * weights[key] 
                    for key in weights
                ) / sum(weights[key] for key in scores)
                
                candidates.append((other_node, total_score, scores))
        
        # 상위 N개 선택
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        for other_node, score, scores in candidates[:max_associations_per_node]:
            # 연결 타입 결정
            if 'embedding' in scores and scores['embedding'] > 0.8:
                assoc_type = 'semantic'
            elif 'temporal' in scores and scores['temporal'] > 0.8:
                assoc_type = 'temporal'
            elif 'keyword' in scores:
                assoc_type = 'entity'
            else:
                assoc_type = 'semantic'
            
            # 연결 생성
            assoc = association_network.create_association(
                source_node_id=node.node_id,
                target_node_id=other_node.node_id,
                association_type=assoc_type,
                strength=score
            )
            created_associations += 1
            node_associations += 1
        
        if (i + 1) % 100 == 0:
            print(f"    {i + 1}/{len(sorted_nodes)} 노드 처리됨, {created_associations} 연결 생성됨...")
    
    print(f"  ✅ {created_associations}개 연결 생성 완료")
    
    # 3단계: 네트워크 통계
    print(f"\n3단계: 네트워크 분석...")
    
    stats = association_network.get_network_stats()
    print(f"  - 총 노드 수: {stats['total_nodes']}")
    print(f"  - 총 연결 수: {stats['total_associations']}")
    print(f"  - 평균 연결 강도: {stats['average_strength']:.3f}")
    print(f"  - 최대 차수: {stats['max_degree']}")
    print(f"  - 고립된 노드: {stats['isolated_nodes']}")
    print(f"  - 노드 타입별 분포: {stats['node_types']}")
    
    # 연결 타입별 통계
    type_counts = {}
    for assoc in association_network.associations.values():
        type_counts[assoc.association_type] = type_counts.get(assoc.association_type, 0) + 1
    print(f"  - 연결 타입별 분포: {type_counts}")
    
    # 4단계: 샘플 활성화 테스트
    print(f"\n4단계: 활성화 전파 테스트...")
    
    # 랜덤 노드 선택
    import random
    sample_nodes = random.sample(list(association_network.nodes.keys()), min(3, len(association_network.nodes)))
    
    for seed_node in sample_nodes[:1]:  # 첫 번째 노드만 테스트
        print(f"\n  시드 노드: {seed_node}")
        
        # 활성화 전파
        activation = spreading_activation.activate(
            seed_nodes=[seed_node],
            initial_activation=1.0
        )
        
        # 활성화된 노드들
        activated = sorted(
            [(node_id, level) for node_id, level in activation.items() if level > 0.1],
            key=lambda x: x[1],
            reverse=True
        )
        
        print(f"  활성화된 노드 수: {len(activated)}")
        for node_id, level in activated[:5]:
            node = association_network.nodes[node_id]
            print(f"    - {node_id}: 레벨 {level:.3f}, 블록 #{node.memory_id}")
    
    print("\n✅ AssociationNetwork 부트스트랩 완료!")
    
    # 최종 상태
    print(f"\n최종 상태:")
    print(f"  - 노드 수: {len(association_network.nodes)}")
    print(f"  - 연결 수: {len(association_network.associations)}")
    
    return association_network

if __name__ == "__main__":
    bootstrap_association_network()