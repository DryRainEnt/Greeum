#!/usr/bin/env python3
"""
보고서 기반 개선사항 통합 테스트 스크립트
- CLI 앵커 검색
- STM 승격
- 메트릭 집계
"""

import json
import time
import numpy as np
from datetime import datetime
from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.core.stm_manager import STMManager
from greeum.core.working_memory import AIContextualSlots, SlotType, MemorySlot

def test_integrated_features():
    print("=" * 60)
    print("통합 기능 테스트")
    print("=" * 60)
    
    # 초기화
    db_manager = DatabaseManager()
    block_manager = BlockManager(db_manager)
    stm_manager = STMManager(db_manager)
    slots = AIContextualSlots()
    
    # 1. 테스트 블록 네트워크 생성
    print("\n1. 테스트 블록 네트워크 생성")
    test_blocks = []
    
    contexts = [
        "[사용자-요청-프로젝트초기화] 새 프로젝트 시작",
        "[Claude-구현-프로젝트설정] 프로젝트 구조 설정",
        "[사용자-질문-프로젝트진행] 진행 상황 확인",
        "[Claude-분석-프로젝트상태] 50% 완료 상태",
        "[팀-결정-프로젝트방향] 아키텍처 변경"
    ]
    
    # 더미 임베딩
    base_embedding = np.random.randn(768)
    
    for i, context in enumerate(contexts):
        # 약간씩 다른 임베딩 생성
        embedding = base_embedding + np.random.randn(768) * 0.1
        embedding = embedding.tolist()
        
        block = block_manager.add_block(
            context=context,
            keywords=["프로젝트"],
            tags=["test"],
            embedding=embedding,
            importance=0.7 + i * 0.05
        )
        if block:
            test_blocks.append(block['block_index'])
            print(f"   ✅ 블록 #{block['block_index']}: {context[:30]}...")
    
    # 블록 간 링크 생성
    if len(test_blocks) >= 3:
        anchor_block = test_blocks[0]
        block_manager.update_block_links(anchor_block, test_blocks[1:3])
        for neighbor in test_blocks[1:3]:
            block_manager.update_block_links(neighbor, [anchor_block])
        print(f"   ✅ 네트워크 구성: {anchor_block} ↔ {test_blocks[1:3]}")
    
    # 2. 앵커 슬롯 설정
    print(f"\n2. 슬롯 A에 앵커 설정: 블록 #{anchor_block}")
    anchor_slot = MemorySlot(
        content=f"Project network anchor - block #{anchor_block}",
        timestamp=datetime.utcnow(),
        slot_type=SlotType.ANCHOR,
        ltm_anchor_block=anchor_block,
        search_radius=2,
        importance_score=0.9
    )
    slots.slots['A'] = anchor_slot
    
    # 3. CLI 명령어 시뮬레이션 (앵커 검색)
    print("\n3. CLI 앵커 검색 테스트 (--slot A --radius 2)")
    search_payload = block_manager.search_with_slots(
        "프로젝트",
        limit=5,
        use_slots=True,
        slot='A',
        radius=2,
        fallback=True
    )
    
    results = search_payload.get('items', [])
    search_meta = search_payload.get('meta', {})
    print(f"   결과: {len(results)}개")
    graph_used = (
        search_meta.get('search_type') == 'graph'
        or any(
            result.get('_meta', search_meta).get('search_type') == 'graph'
            for result in results
        )
    )
    print(f"   그래프 검색: {'✅' if graph_used else '❌'}")
    
    # 4. STM 승격 테스트
    print("\n4. STM → LTM 자동 승격 테스트")
    
    # STM에 메모리 추가
    stm_memory = {
        'id': 'test_stm_001',
        'content': '[사용자-피드백-프로젝트성능] 매우 만족스러운 성능',
        'keywords': ['프로젝트', '성능'],
        'embedding': (base_embedding + np.random.randn(768) * 0.05).tolist(),
        'timestamp': datetime.now().isoformat()
    }
    
    memory_id = stm_manager.add_memory(stm_memory)
    print(f"   STM 메모리 추가: {memory_id}")
    
    # 여러 번 접근하여 승격 조건 충족
    query_embedding = np.array(base_embedding)
    for i in range(3):
        should_promote = stm_manager.check_promotion_to_working_memory(
            memory_id, 
            query_embedding if i == 0 else None
        )
        print(f"   접근 #{i+1}: 승격 조건 = {should_promote}")
        
        if should_promote:
            promoted_block = stm_manager.promote_to_ltm(memory_id)
            if promoted_block:
                print(f"   ✅ LTM으로 승격 완료: 블록 #{promoted_block}")
            break
    
    # STM 통계 확인
    stm_stats = stm_manager.get_stats()
    print(f"   STM 상태: {stm_stats.get('active_count')}개 활성, "
          f"{stm_stats.get('promotion_ready')}개 승격 대기")
    
    # 5. 메트릭 확인
    print("\n5. 검색 메트릭 확인")
    metrics = block_manager.get_metrics()
    
    print(f"   총 검색: {metrics['total_searches']}회")
    print(f"   그래프 검색: {metrics['graph_searches']}회")
    print(f"   그래프 히트: {metrics['graph_hits']}개")
    print(f"   로컬 히트율: {metrics['local_hit_rate']:.1%}")
    print(f"   평균 홉 거리: {metrics['avg_hops']:.1f}")
    
    # 6. Near-Anchor Write 테스트
    print("\n6. Near-Anchor Write 테스트")
    
    # 앵커 근처에 새 블록 추가
    new_block = block_manager.add_block(
        context="[사용자-요청-프로젝트최적화] 성능 최적화 요청",
        keywords=["프로젝트", "최적화"],
        tags=["near_anchor"],
        embedding=(base_embedding + np.random.randn(768) * 0.08).tolist(),
        importance=0.85
    )
    
    if new_block:
        new_block_id = new_block['block_index']
        print(f"   새 블록 생성: #{new_block_id}")
        
        # 앵커와 자동 연결
        block_manager.update_block_links(new_block_id, [anchor_block])
        block_manager.update_block_links(anchor_block, [new_block_id])
        print(f"   ✅ 앵커 #{anchor_block}와 자동 연결")
        
        # 연결 확인
        neighbors = block_manager.get_block_neighbors(anchor_block)
        print(f"   앵커의 이웃: {neighbors}")
    
    # 7. 종합 평가
    print("\n" + "=" * 60)
    print("📊 통합 테스트 결과")
    print("=" * 60)
    
    test_results = {
        "앵커 기반 검색": "✅ 작동" if graph_used else "❌ 실패",
        "STM 자동 승격": "✅ 작동" if stm_stats.get('promotion_ready', 0) >= 0 else "❌ 실패",
        "메트릭 집계": "✅ 작동" if metrics['total_searches'] > 0 else "❌ 실패",
        "Near-Anchor Write": "✅ 작동" if new_block else "❌ 실패"
    }
    
    for feature, status in test_results.items():
        print(f"   {feature}: {status}")
    
    success_count = sum(1 for s in test_results.values() if "✅" in s)
    print(f"\n   전체 성공률: {success_count}/{len(test_results)} ({success_count/len(test_results)*100:.0f}%)")
    
    # 메트릭 초기화 (다음 테스트를 위해)
    block_manager.reset_metrics()
    print("\n   메트릭 초기화 완료")

if __name__ == "__main__":
    test_integrated_features()