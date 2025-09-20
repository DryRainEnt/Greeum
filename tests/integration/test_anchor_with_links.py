#!/usr/bin/env python3
"""
앵커 기반 국소 탐색 효과 검증 스크립트 v2
- 싱글톤 패턴 적용
- 실제 링크 생성 및 검증
"""

import json
import time
from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.core.working_memory import AIContextualSlots, SlotType, MemorySlot
from datetime import datetime

def setup_test_network():
    """테스트용 블록 네트워크 설정"""
    
    print("=" * 60)
    print("테스트 네트워크 설정")
    print("=" * 60)
    
    db_manager = DatabaseManager()
    block_manager = BlockManager(db_manager)
    
    # 1. 테스트 블록 생성 (없으면)
    recent_blocks = block_manager.get_blocks(limit=10, sort_by='timestamp', order='desc')
    
    if len(recent_blocks) < 5:
        print("테스트 블록 생성 중...")
        test_contexts = [
            "[사용자-요청-프로젝트설정] 새로운 프로젝트 초기 설정 진행",
            "[Claude-구현-프로젝트구조] 프로젝트 디렉토리 구조 생성 완료",
            "[사용자-질문-프로젝트진행] 프로젝트 진행 상황 확인 요청",
            "[Claude-분석-프로젝트상태] 현재 프로젝트 50% 완료 상태",
            "[팀-결정-프로젝트방향] 프로젝트 아키텍처 변경 결정"
        ]
        
        for context in test_contexts:
            block_manager.add_block(context, importance=0.7)
            
        recent_blocks = block_manager.get_blocks(limit=10, sort_by='timestamp', order='desc')
    
    # 2. 블록 간 링크 생성
    print("\n블록 간 링크 생성 중...")
    
    # 첫 3개 블록을 서로 연결 (프로젝트 관련 네트워크)
    if len(recent_blocks) >= 3:
        block_ids = [b['block_index'] for b in recent_blocks[:3]]
        
        # 양방향 링크 생성
        block_manager.update_block_links(block_ids[0], [block_ids[1], block_ids[2]])
        block_manager.update_block_links(block_ids[1], [block_ids[0], block_ids[2]])
        block_manager.update_block_links(block_ids[2], [block_ids[0], block_ids[1]])
        
        print(f"✅ 블록 {block_ids[0]}, {block_ids[1]}, {block_ids[2]} 간 링크 생성 완료")
        
        # 링크 확인
        neighbors = block_manager.get_block_neighbors(block_ids[0])
        print(f"   블록 {block_ids[0]}의 이웃: {neighbors}")
        
        return block_ids[0]  # 첫 번째 블록을 앵커로 반환
    
    return None

def test_anchor_search_with_links():
    
    """링크가 있는 앵커 기반 검색 테스트"""
    
    print()
    print("=" * 60)
    print("앵커 기반 국소 탐색 효과 검증 (링크 포함)")
    print("=" * 60)
    
    # 1. 초기화
    db_manager = DatabaseManager()
    block_manager = BlockManager(db_manager)
    slots = AIContextualSlots()  # 싱글톤 인스턴스
    
    # 2. 테스트 네트워크 설정
    anchor_id = setup_test_network()
    
    if not anchor_id:
        print("❌ 테스트 네트워크 설정 실패")
        return
    
    # 3. 슬롯 A에 앵커 설정
    print()
    print(f"✅ 슬롯 A에 앵커 설정: 블록 #{anchor_id}")
    
    anchor_slot = MemorySlot(
        content=f"Anchor for block #{anchor_id}",
        timestamp=datetime.utcnow(),
        slot_type=SlotType.ANCHOR,
        ltm_anchor_block=anchor_id,
        search_radius=2,
        importance_score=0.9,
    )
    slots.slots['A'] = anchor_slot
    
    slot_a = slots.get_slot('A')
    if slot_a:
        print(f"   앵커 블록: {slot_a.ltm_anchor_block}")
        print(f"   검색 반경: {slot_a.search_radius}")
        print(f"   슬롯 타입: {slot_a.slot_type}")
    
    # 4. 검색 쿼리 준비
    test_query = "프로젝트"
    
    print()
    print("=" * 60)
    print(f"검색어: '{test_query}'")
    print("=" * 60)
    
    # 5. A: 표준 검색 (앵커 없이)
    print()
    print("📊 A. 표준 검색 (앵커 없음)")
    print("-" * 40)
    
    start_time = time.time()
    standard_payload = block_manager.search_with_slots(
        test_query,
        limit=5,
        use_slots=False,
    )
    standard_time = (time.time() - start_time) * 1000
    
    standard_results = standard_payload.get('items', [])
    standard_meta = standard_payload.get('meta', {})
    
    print(f"⏱️  응답 시간: {standard_time:.2f}ms")
    print(f"📋 결과 수: {len(standard_results)}")
    
    for i, result in enumerate(standard_results[:3], 1):
        result_meta = result.get('_meta', standard_meta)
        print()
        print(f"  {i}. 블록 #{result.get('block_index', 'N/A')}")
        print(f"     내용: {result.get('context', '')[:50]}...")
        print(f"     타입: {result_meta.get('search_type', 'standard')}")
    
    # 6. B: 앵커 기반 국소 검색
    print()
    print()
    print("📊 B. 앵커 기반 국소 검색 (슬롯 A, 반경 2)")
    print("-" * 40)
    
    start_time = time.time()
    anchor_payload = block_manager.search_with_slots(
        test_query,
        limit=5,
        use_slots=True,
        slot='A',
        depth=3,
        fallback=True,
    )
    anchor_time = (time.time() - start_time) * 1000
    
    anchor_results = anchor_payload.get('items', [])
    anchor_meta = anchor_payload.get('meta', {})
    
    print(f"⏱️  응답 시간: {anchor_time:.2f}ms")
    print(f"📋 결과 수: {len(anchor_results)}")
    
    hop_distances = []
    graph_used = bool(anchor_meta.get('search_type') == 'graph')
    fallback_used = bool(anchor_meta.get('fallback_used'))
    
    for i, result in enumerate(anchor_results[:3], 1):
        result_meta = result.get('_meta', anchor_meta)
        print()
        print(f"  {i}. 블록 #{result.get('block_index', 'N/A')}")
        print(f"     내용: {result.get('context', '')[:50]}...")
        print(f"     타입: {result_meta.get('search_type', 'standard')}")
    
        hop_distance = result_meta.get('hop_distance')
        if hop_distance is not None:
            print(f"     거리: {hop_distance} hop")
            hop_distances.append(hop_distance)
    
        if result_meta.get('search_type') == 'graph':
            graph_used = True
        if result_meta.get('fallback_used'):
            fallback_used = True
    
    # 7. 결과 분석
    print()
    print()
    print("=" * 60)
    print("📈 분석 결과")
    print("=" * 60)
    
    speedup = standard_time / anchor_time if anchor_time > 0 else 0
    print()
    print("⚡ 속도 비교:")
    print(f"   - 표준: {standard_time:.2f}ms")
    print(f"   - 앵커: {anchor_time:.2f}ms")
    print(f"   - 개선: {speedup:.2f}x")
    
    if hop_distances:
        avg_hops = sum(hop_distances) / len(hop_distances)
        print()
        print(f"🎯 평균 홉 거리: {avg_hops:.1f}")
    
    print()
    print("🔍 검색 메타데이터:")
    print(f"   - 그래프 사용: {'✅' if graph_used else '❌'}")
    print(f"   - Fallback 사용: {'✅' if fallback_used else '❌'}")
    
    # 8. 슬롯 상태 확인
    print()
    print("📌 현재 슬롯 상태:")
    for slot_name in ['A', 'B', 'C']:
        slot = slots.get_slot(slot_name)
        if slot:
            print(f"   슬롯 {slot_name}: {slot.slot_type.value} - 앵커 #{slot.ltm_anchor_block}")
        else:
            print(f"   슬롯 {slot_name}: 비어있음")
    
    # 9. 권장사항
    print()
    print()
    print("💡 권장사항:")
    if speedup > 1.5:
        print("   ✅ 앵커 기반 검색이 효과적입니다!")
    else:
        print("   ⚠️  속도 개선이 미미합니다.")
    
    if graph_used:
        print("   ✅ 그래프 검색이 정상 작동합니다!")
    else:
        print("   ⚠️  그래프 검색이 작동하지 않았습니다.")
    
    print()
    print("=" * 60)
    

if __name__ == "__main__":
    test_anchor_search_with_links()