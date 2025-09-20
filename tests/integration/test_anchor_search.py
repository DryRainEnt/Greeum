#!/usr/bin/env python3
"""
앵커 기반 국소 탐색 효과 검증 스크립트
PR#1, PR#2 구현 효과를 A/B 테스트로 검증
"""

import json
import time
from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.core.working_memory import AIContextualSlots, SlotType

def test_anchor_search():

    """앵커 기반 검색 vs 표준 검색 비교"""

    print("=" * 60)
    print("앵커 기반 국소 탐색 효과 검증")
    print("=" * 60)

    # 1. 초기화
    db_manager = DatabaseManager()
    block_manager = BlockManager(db_manager)
    slots = AIContextualSlots()

    # 2. 테스트 데이터 준비 (기존 블록 중 하나를 앵커로 설정)
    recent_blocks = block_manager.get_blocks(limit=10, sort_by='timestamp', order='desc')

    if not recent_blocks:
        print("❌ 테스트할 블록이 없습니다. 먼저 메모리를 추가해주세요.")
        return

    # 첫 번째 블록을 앵커로 설정
    anchor_block = recent_blocks[0]
    anchor_id = anchor_block['block_index']

    # 슬롯 A에 앵커 설정
    slot_a = slots.get_slot('A')
    if slot_a:
        slot_a.content = f"Anchor test: {anchor_block['context'][:50]}..."
        slot_a.ltm_anchor_block = anchor_id
        slot_a.search_radius = 2
        slot_a.slot_type = SlotType.ANCHOR
        print(f"✅ 슬롯 A에 앵커 설정: 블록 #{anchor_id}")

    # 3. 검색 쿼리 준비
    test_query = "프로젝트"  # 일반적인 검색어

    print()
    print("=" * 60)
    print(f"검색어: '{test_query}'")
    print("=" * 60)

    # 4. A: 표준 검색 (앵커 없이)
    print()
    print("📊 A. 표준 검색 (앵커 없음)")
    print("-" * 40)

    start_time = time.time()
    standard_payload = block_manager.search_with_slots(
        test_query,
        limit=5,
        use_slots=False  # 슬롯 비활성화
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

    # 5. B: 앵커 기반 국소 검색
    print()
    print()
    print("📊 B. 앵커 기반 국소 검색 (슬롯 A, 반경 2)")
    print("-" * 40)

    start_time = time.time()
    anchor_payload = block_manager.search_with_slots(
        test_query,
        limit=5,
        use_slots=True,
        slot='A',      # 슬롯 A 사용
        depth=3,       # DFS 깊이 기본값 유지
        fallback=True  # fallback 활성화
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

    # 6. 결과 분석
    print()
    print()
    print("=" * 60)
    print("📈 분석 결과")
    print("=" * 60)

    speedup = standard_time / anchor_time if anchor_time > 0 else 0
    print()
    print(f"⚡ 속도 개선: {speedup:.2f}x")
    print(f"   - 표준: {standard_time:.2f}ms")
    print(f"   - 앵커: {anchor_time:.2f}ms")

    if hop_distances:
        avg_hops = sum(hop_distances) / len(hop_distances)
        print()
        print(f"🎯 평균 홉 거리: {avg_hops:.1f}")

    print()
    print("🔍 검색 메타데이터:")
    print(f"   - 그래프 사용: {'✅' if graph_used else '❌'}")
    print(f"   - Fallback 사용: {'✅' if fallback_used else '❌'}")

    # 7. 권장사항
    print()
    print()
    print("💡 권장사항:")
    if speedup > 1.5:
        print("   ✅ 앵커 기반 검색이 효과적입니다!")
    else:
        print("   ⚠️  더 많은 블록과 링크가 필요합니다.")

    if not graph_used:
        print("   ⚠️  그래프 검색이 작동하지 않았습니다. 앵커 설정을 확인하세요.")

    print()
    print("=" * 60)


if __name__ == "__main__":
    test_anchor_search()