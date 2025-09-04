#!/usr/bin/env python3
"""
인과관계 시스템 개발 검증 테스트 (v2.4.0.dev1)

이론이 실제로 작동하는지 확인하는 기본 테스트
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from greeum.core.causality_detector import (
    detect_causality_for_memory,
    VectorBasedCausalityFilter,
    BasicCausalityDetector,
    BridgeMemoryDetector
)
import numpy as np
from datetime import datetime, timedelta
import json

def create_test_memory(block_index: int, context: str, timestamp: str = None, 
                      keywords: list = None, embedding: list = None) -> dict:
    """테스트용 메모리 생성"""
    
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    
    if keywords is None:
        keywords = context.split()[:3]  # 간단한 키워드 추출
    
    if embedding is None:
        # 간단한 해시 기반 임베딩 생성 (실제 그리움과 호환)
        np.random.seed(hash(context) % 10000)
        embedding = np.random.normal(0, 1, 128).tolist()
    
    return {
        'block_index': block_index,
        'timestamp': timestamp,
        'context': context,
        'keywords': keywords,
        'embedding': embedding,
        'importance': 0.7
    }

def test_vector_filtering():
    """벡터 기반 후보 축소 테스트"""
    print("🔧 벡터 기반 후보 축소 테스트...")
    
    # 테스트 메모리들 생성
    memories = [
        create_test_memory(1, "React 성능이 너무 느려서 문제다"),
        create_test_memory(2, "오늘 날씨가 정말 좋다"),  # 무관한 내용
        create_test_memory(3, "웹팩 번들 사이즈를 최적화했다"),  
        create_test_memory(4, "점심으로 파스타를 먹었다"),  # 무관한 내용
        create_test_memory(5, "사용자가 앱 속도에 대해 불만을 제기했다"),
    ]
    
    new_memory = create_test_memory(6, "성능 문제 해결을 위해 코드 리뷰를 진행했다")
    
    filter_system = VectorBasedCausalityFilter()
    candidates = filter_system.find_causality_candidates(new_memory, memories)
    
    # 디버깅: 유사도 점수도 출력
    print(f"  전체 메모리: {len(memories)}개")
    print("  유사도 분석:")
    new_vec = np.array(new_memory['embedding'])
    for mem in memories:
        existing_vec = np.array(mem['embedding'])
        similarity = filter_system._cosine_similarity(new_vec, existing_vec)
        print(f"    [{mem['block_index']}] 유사도: {similarity:.3f} - {mem['context'][:30]}...")
    
    print(f"  필터링 후: {len(candidates)}개")
    print("  선별된 메모리:")
    for mem in candidates:
        print(f"    - [{mem['block_index']}] {mem['context'][:50]}...")
    
    return len(candidates) > 0 and len(candidates) < len(memories)

def test_causality_detection():
    """기본 인과관계 감지 테스트"""
    print("\n🧠 인과관계 감지 테스트...")
    
    base_time = datetime.now()
    
    # 명확한 인과관계가 있는 메모리 쌍
    memory_a = create_test_memory(
        1, "사용자가 앱이 너무 느리다고 불만을 제기했다",
        (base_time - timedelta(days=1)).isoformat()
    )
    
    memory_b = create_test_memory(
        2, "성능 분석 결과 React 렌더링이 병목이라는 결론을 내렸다", 
        base_time.isoformat()
    )
    
    detector = BasicCausalityDetector()
    causality_score = detector.detect_causality(memory_a, memory_b)
    
    print(f"  메모리 A: {memory_a['context'][:50]}...")
    print(f"  메모리 B: {memory_b['context'][:50]}...")
    print(f"  인과관계 점수: {causality_score.strength:.3f}")
    print(f"  신뢰도: {causality_score.confidence:.3f}")
    print(f"  방향: {causality_score.direction}")
    print(f"  세부 분석:")
    for key, value in causality_score.breakdown.items():
        print(f"    {key}: {value:.3f}")
    
    return causality_score.strength > 0.3  # 최소한의 인과관계 감지

def test_bridge_detection():
    """브릿지 메모리 감지 테스트 (핵심 기능)"""
    print("\n🌉 브릿지 메모리 감지 테스트...")
    
    base_time = datetime.now()
    
    # 기존 메모리들 (서로 직접 연결되기 어려운)
    existing_memories = [
        create_test_memory(
            1, "사용자가 로그인 후 대시보드 로딩이 너무 느리다고 신고했다",
            (base_time - timedelta(days=10)).isoformat()
        ),
        create_test_memory(
            2, "React 컴포넌트 구조를 함수형으로 전면 리팩토링했다",
            (base_time - timedelta(days=2)).isoformat()
        ),
        create_test_memory(
            3, "오늘 점심은 김치찌개를 먹었다",  # 무관한 내용
            (base_time - timedelta(days=1)).isoformat()
        ),
        create_test_memory(
            4, "웹팩 설정을 최적화해서 번들 사이즈를 30% 줄였다",
            (base_time - timedelta(days=3)).isoformat()
        )
    ]
    
    # 브릿지 역할을 할 새 메모리
    bridge_memory = create_test_memory(
        5, "성능 프로파일링 결과 렌더링 최적화와 번들링 개선이 필요하다고 분석했다",
        (base_time - timedelta(days=5)).isoformat()
    )
    
    bridge_detector = BridgeMemoryDetector()
    bridges = bridge_detector.detect_bridge_opportunities(bridge_memory, existing_memories)
    
    print(f"  기존 메모리: {len(existing_memories)}개")
    print(f"  브릿지 연결 발견: {len(bridges)}개")
    
    for i, bridge in enumerate(bridges):
        print(f"  브릿지 {i+1}:")
        print(f"    시작: 메모리 #{bridge.start_memory_id}")
        print(f"    브릿지: 메모리 #{bridge.bridge_memory_id}")  
        print(f"    종료: 메모리 #{bridge.end_memory_id}")
        print(f"    점수: {bridge.bridge_score:.3f}")
        print(f"    유형: {bridge.chain_type}")
    
    return len(bridges) > 0

def test_integrated_system():
    """통합 시스템 테스트"""
    print("\n🚀 통합 시스템 테스트...")
    
    base_time = datetime.now()
    
    # 복잡한 시나리오: 3개월간의 프로젝트 진행 과정
    existing_memories = [
        create_test_memory(1, "새 프로젝트 킥오프 미팅을 했다", (base_time - timedelta(days=90)).isoformat()),
        create_test_memory(2, "요구사항 분석을 완료했다", (base_time - timedelta(days=85)).isoformat()),
        create_test_memory(3, "React와 Node.js로 기술 스택을 결정했다", (base_time - timedelta(days=80)).isoformat()),
        create_test_memory(4, "첫 번째 프로토타입을 개발했다", (base_time - timedelta(days=70)).isoformat()),
        create_test_memory(5, "사용자 테스트에서 성능 이슈가 발견되었다", (base_time - timedelta(days=60)).isoformat()),
        create_test_memory(6, "데이터베이스 쿼리를 최적화했다", (base_time - timedelta(days=50)).isoformat()),
        create_test_memory(7, "캐싱 시스템을 도입했다", (base_time - timedelta(days=40)).isoformat()),
        create_test_memory(8, "성능이 50% 개선되었다", (base_time - timedelta(days=30)).isoformat()),
        create_test_memory(9, "최종 사용자 검수를 통과했다", (base_time - timedelta(days=20)).isoformat()),
        create_test_memory(10, "프로덕션 배포를 완료했다", (base_time - timedelta(days=10)).isoformat()),
    ]
    
    # 새로 추가되는 회고 메모리
    new_memory = create_test_memory(
        11, "프로젝트 회고를 하면서 성능 문제 해결 과정이 가장 도전적이었다고 결론지었다",
        base_time.isoformat()
    )
    
    # 통합 시스템으로 분석
    result = detect_causality_for_memory(new_memory, existing_memories)
    
    print(f"  분석 대상: {result['analyzed_candidates']}개 메모리")
    print(f"  직접 인과관계: {result['direct_causality_links']}개")
    print(f"  브릿지 연결: {result['bridge_connections']}개")
    
    if result['causality_details']:
        print("  직접 인과관계 상위 3개:")
        for detail in sorted(result['causality_details'], key=lambda x: x['causality_score'], reverse=True)[:3]:
            print(f"    메모리 #{detail['memory_id']}: 점수 {detail['causality_score']:.3f}")
    
    if result['bridge_details']:
        print("  브릿지 연결 상위 3개:")
        for detail in sorted(result['bridge_details'], key=lambda x: x['score'], reverse=True)[:3]:
            print(f"    {detail['start_id']} → {detail['bridge_id']} → {detail['end_id']}: 점수 {detail['score']:.3f}")
    
    # 성공 기준: 최소한의 연결 발견
    return result['direct_causality_links'] > 0 or result['bridge_connections'] > 0

def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 60)
    print("🧪 그리움 인과관계 시스템 개발 검증 테스트 (v2.4.0.dev1)")
    print("=" * 60)
    
    tests = [
        ("벡터 필터링", test_vector_filtering),
        ("인과관계 감지", test_causality_detection),
        ("브릿지 감지", test_bridge_detection),
        ("통합 시스템", test_integrated_system)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"\n{status}")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"\n❌ ERROR: {str(e)}")
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    passed = 0
    for test_name, success, error in results:
        if success:
            print(f"✅ {test_name}")
            passed += 1
        elif error:
            print(f"💥 {test_name} - ERROR: {error}")
        else:
            print(f"❌ {test_name}")
    
    print(f"\n📈 성공률: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")
    
    if passed == len(results):
        print("🎉 모든 테스트 통과! 이론이 실제로 작동합니다.")
        print("👉 다음 단계: 알파 버전으로 프로덕션 레벨 성능 테스트")
    elif passed >= len(results) * 0.75:
        print("⚡ 대부분 테스트 통과! 일부 조정 후 알파 진행 가능")
    else:
        print("🔧 추가 개발 필요. 이론 재검토 및 구현 보완 필요")

if __name__ == "__main__":
    run_all_tests()