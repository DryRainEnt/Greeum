#!/usr/bin/env python3
"""
Phase 2 Critical 이슈 수정 검증 테스트
- 빈 임베딩 문제 해결 확인
- 무한 재귀 호출 문제 해결 확인  
- Working Memory 임베딩 생성 동작 확인
"""

import time
import sys
import os
from typing import List, Dict, Any

# 상위 디렉토리를 path에 추가
sys.path.insert(0, os.path.abspath('../../..'))

from greeum.core.hybrid_stm_manager import HybridSTMManager
from greeum.core.database_manager import DatabaseManager

def test_fixed_search_memories():
    """수정된 search_memories 메서드 테스트"""
    print("🔍 수정된 search_memories 테스트:")
    
    # 메모리 DB로 테스트
    db_manager = DatabaseManager(connection_string=":memory:")
    hybrid_stm = HybridSTMManager(db_manager, mode="hybrid")
    
    try:
        # 테스트 메모리 추가
        test_memories = [
            {"content": "프로젝트 진행 상황 업데이트", "importance": 0.8},
            {"content": "성능 최적화 작업 완료", "importance": 0.9},
            {"content": "버그 수정 및 테스트", "importance": 0.7}
        ]
        
        print("  메모리 추가 중...")
        for memory in test_memories:
            result = hybrid_stm.add_memory(memory)
            print(f"    추가됨: {result}")
        
        # 검색 테스트 (임베딩 없이)
        print("  검색 테스트 (임베딩 자동 생성):")
        
        start_time = time.perf_counter()
        search_results = hybrid_stm.search_memories("프로젝트 진행", query_embedding=None, top_k=3)
        execution_time = (time.perf_counter() - start_time) * 1000
        
        print(f"    실행 시간: {execution_time:.2f}ms")
        print(f"    검색 결과 수: {len(search_results)}")
        
        # Working Memory 결과 확인
        wm_results = [r for r in search_results if r.get("source") == "working_memory"]
        print(f"    Working Memory 결과: {len(wm_results)}개")
        
        # STM 적중률 확인
        stats = hybrid_stm.get_hybrid_statistics()
        wm_hits = stats["hybrid_performance"]["working_memory_hits"]
        total_requests = stats["hybrid_performance"]["total_requests"]
        hit_rate = (wm_hits / max(1, total_requests)) * 100
        
        print(f"    Working Memory 적중률: {hit_rate:.1f}%")
        
        success = len(search_results) > 0 and hit_rate > 0
        print(f"  ✅ 검색 기능: {'성공' if success else '실패'}")
        
        return success, hit_rate, execution_time
        
    except Exception as e:
        print(f"  ❌ 검색 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, 0, 0

def test_fixed_get_recent_memories():
    """수정된 get_recent_memories 메서드 테스트"""
    print("\n🕐 수정된 get_recent_memories 테스트:")
    
    db_manager = DatabaseManager(connection_string=":memory:")
    hybrid_stm = HybridSTMManager(db_manager, mode="hybrid")
    
    try:
        # 메모리 추가
        print("  메모리 추가 중...")
        for i in range(5):
            memory = {"content": f"테스트 메모리 {i+1}", "importance": 0.5 + i*0.1}
            hybrid_stm.add_memory(memory)
            time.sleep(0.01)  # 타임스탬프 차이를 위해
        
        # get_recent_memories 테스트 (무한 재귀 확인)
        print("  최근 메모리 조회 테스트:")
        
        start_time = time.perf_counter()
        recent_memories = hybrid_stm.get_recent_memories(count=10)
        execution_time = (time.perf_counter() - start_time) * 1000
        
        print(f"    실행 시간: {execution_time:.2f}ms")
        print(f"    조회된 메모리 수: {len(recent_memories)}")
        
        # 무한 재귀 없이 완료되었는지 확인 (1초 이내)
        no_infinite_recursion = execution_time < 1000
        has_results = len(recent_memories) > 0
        
        print(f"    무한 재귀 방지: {'✅' if no_infinite_recursion else '❌'}")
        print(f"    결과 반환: {'✅' if has_results else '❌'}")
        
        # 결과 상세 확인
        if recent_memories:
            print("    조회된 메모리:")
            for i, memory in enumerate(recent_memories[:3]):
                print(f"      {i+1}. {memory.get('content', 'N/A')[:30]}...")
        
        success = no_infinite_recursion and has_results
        print(f"  ✅ 최근 메모리 조회: {'성공' if success else '실패'}")
        
        return success, len(recent_memories), execution_time
        
    except Exception as e:
        print(f"  ❌ 최근 메모리 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, 0, 0

def test_embedding_generation():
    """임베딩 생성 메서드 테스트"""
    print("\n🧮 임베딩 생성 테스트:")
    
    db_manager = DatabaseManager(connection_string=":memory:")
    hybrid_stm = HybridSTMManager(db_manager, mode="working_only")
    
    try:
        test_queries = [
            "프로젝트 진행 상황",
            "성능 최적화 작업", 
            "버그 수정 완료",
            "새로운 기능 구현"
        ]
        
        embeddings = []
        total_time = 0
        
        for query in test_queries:
            start_time = time.perf_counter()
            embedding = hybrid_stm._generate_query_embedding(query)
            execution_time = (time.perf_counter() - start_time) * 1000
            
            embeddings.append(embedding)
            total_time += execution_time
            
            print(f"  쿼리: '{query}'")
            print(f"    임베딩 길이: {len(embedding)}")
            print(f"    생성 시간: {execution_time:.3f}ms")
            print(f"    샘플 값: {embedding[:3]}")
        
        avg_time = total_time / len(test_queries)
        print(f"\n  평균 생성 시간: {avg_time:.3f}ms")
        
        # 검증 기준
        all_same_length = all(len(emb) == 16 for emb in embeddings)
        all_valid_range = all(all(0.0 <= val <= 1.0 for val in emb) for emb in embeddings)
        fast_generation = avg_time < 10  # 10ms 이내
        
        print(f"  길이 일관성 (16개): {'✅' if all_same_length else '❌'}")
        print(f"  값 범위 (0-1): {'✅' if all_valid_range else '❌'}")
        print(f"  생성 속도 (<10ms): {'✅' if fast_generation else '❌'}")
        
        success = all_same_length and all_valid_range and fast_generation
        print(f"  ✅ 임베딩 생성: {'성공' if success else '실패'}")
        
        return success, avg_time, len(embeddings[0]) if embeddings else 0
        
    except Exception as e:
        print(f"  ❌ 임베딩 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, 0, 0

def test_working_memory_integration():
    """Working Memory 통합 동작 테스트"""
    print("\n🔧 Working Memory 통합 테스트:")
    
    db_manager = DatabaseManager(connection_string=":memory:")
    hybrid_stm = HybridSTMManager(db_manager, mode="working_only")
    
    try:
        # Working Memory에 데이터 추가
        print("  Working Memory 데이터 추가:")
        test_data = [
            {"content": "중요한 프로젝트 미팅", "importance": 0.9},
            {"content": "코드 리뷰 완료", "importance": 0.7},
            {"content": "테스트 케이스 작성", "importance": 0.8},
            {"content": "문서 업데이트", "importance": 0.6}
        ]
        
        for data in test_data:
            result = hybrid_stm.add_memory(data)
            print(f"    추가: {result}")
        
        # Working Memory 상태 확인
        wm_stats = hybrid_stm.working_memory.get_statistics()
        print(f"  활성 슬롯: {wm_stats['active_slots']}/{wm_stats['total_slots']}")
        print(f"  활용률: {wm_stats['utilization_rate']:.1%}")
        
        # 검색 성능 테스트
        print("  Working Memory 검색 테스트:")
        search_queries = ["프로젝트", "코드", "테스트", "문서"]
        
        total_hits = 0
        total_time = 0
        
        for query in search_queries:
            start_time = time.perf_counter()
            results = hybrid_stm.search_memories(query, top_k=3)
            execution_time = (time.perf_counter() - start_time) * 1000
            
            wm_results = [r for r in results if r.get("source") == "working_memory"]
            
            print(f"    '{query}': {len(wm_results)}개 결과, {execution_time:.2f}ms")
            
            if wm_results:
                total_hits += 1
            total_time += execution_time
        
        hit_rate = (total_hits / len(search_queries)) * 100
        avg_time = total_time / len(search_queries)
        
        print(f"\n  Working Memory 검색 결과:")
        print(f"    적중률: {hit_rate:.1f}%")
        print(f"    평균 검색 시간: {avg_time:.2f}ms")
        
        # 성공 기준
        good_utilization = wm_stats['utilization_rate'] > 0.5
        good_hit_rate = hit_rate > 50  # 50% 이상 적중
        fast_search = avg_time < 50  # 50ms 이내
        
        print(f"    활용률 (>50%): {'✅' if good_utilization else '❌'}")
        print(f"    적중률 (>50%): {'✅' if good_hit_rate else '❌'}")
        print(f"    검색 속도 (<50ms): {'✅' if fast_search else '❌'}")
        
        success = good_utilization and good_hit_rate and fast_search
        print(f"  ✅ Working Memory 통합: {'성공' if success else '실패'}")
        
        return success, hit_rate, avg_time
        
    except Exception as e:
        print(f"  ❌ Working Memory 통합 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, 0, 0

def main():
    """메인 검증 테스트"""
    print("=" * 60)
    print("🧪 Phase 2 Critical 이슈 수정 검증")
    print("=" * 60)
    
    results = {}
    
    # 1. 검색 기능 테스트
    search_success, hit_rate, search_time = test_fixed_search_memories()
    results["search"] = {"success": search_success, "hit_rate": hit_rate, "time": search_time}
    
    # 2. 최근 메모리 조회 테스트  
    recent_success, recent_count, recent_time = test_fixed_get_recent_memories()
    results["recent"] = {"success": recent_success, "count": recent_count, "time": recent_time}
    
    # 3. 임베딩 생성 테스트
    embed_success, embed_time, embed_length = test_embedding_generation()
    results["embedding"] = {"success": embed_success, "time": embed_time, "length": embed_length}
    
    # 4. Working Memory 통합 테스트
    wm_success, wm_hit_rate, wm_time = test_working_memory_integration()
    results["working_memory"] = {"success": wm_success, "hit_rate": wm_hit_rate, "time": wm_time}
    
    print("\n" + "=" * 60)
    print("📋 수정 검증 결과 요약")
    print("=" * 60)
    
    # 결과 요약
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r["success"])
    
    print(f"🎯 전체 테스트: {passed_tests}/{total_tests} 통과")
    print(f"📊 성공률: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\n상세 결과:")
    print(f"  검색 기능: {'✅' if results['search']['success'] else '❌'} (적중률: {results['search']['hit_rate']:.1f}%)")
    print(f"  최근 조회: {'✅' if results['recent']['success'] else '❌'} (결과: {results['recent']['count']}개)")
    print(f"  임베딩 생성: {'✅' if results['embedding']['success'] else '❌'} (길이: {results['embedding']['length']})")
    print(f"  Working Memory: {'✅' if results['working_memory']['success'] else '❌'} (적중률: {results['working_memory']['hit_rate']:.1f}%)")
    
    # 최종 판정
    all_critical_fixed = (
        results["search"]["success"] and 
        results["recent"]["success"] and 
        results["embedding"]["success"]
    )
    
    performance_improved = results["working_memory"]["success"]
    
    print(f"\n🔧 Critical 이슈 수정: {'✅ 완료' if all_critical_fixed else '❌ 미완료'}")
    print(f"⚡ 성능 개선 확인: {'✅ 확인' if performance_improved else '❌ 미확인'}")
    
    overall_success = all_critical_fixed and performance_improved
    print(f"\n🏆 Phase 2 수정 성공: {'✅' if overall_success else '❌'}")
    
    if overall_success:
        print("\n🚀 Phase 2가 정상 작동합니다! STM 적중률이 0%에서 개선되었습니다.")
    else:
        print("\n⚠️  추가 수정이 필요합니다.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)