#!/usr/bin/env python3
"""
STM vs LTM Direct 성능 비교 실험
현재 LTM 데이터를 사용하여 두 가지 방식의 성능을 비교
"""

import sys
import os
import json
import tempfile
import time
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add the Greeum package to path
sys.path.insert(0, str(Path(__file__).parent))

from greeum.core.database_manager import DatabaseManager
from greeum.core.hierarchical_memory import HierarchicalMemorySystem
from greeum.core.memory_layer import MemoryLayerType, create_memory_item
from greeum.core.dashboard import get_dashboard_system


class STMPerformanceTester:
    """STM 성능 테스터"""
    
    def __init__(self):
        self.results = {
            'ltm_direct': {},
            'stm_priority': {}
        }
        self.test_data = []
    
    def extract_current_memories(self) -> List[Dict[str, Any]]:
        """현재 LTM에서 메모리 데이터 추출"""
        print("📂 현재 LTM 데이터 추출 중...")
        
        db = DatabaseManager()
        system = HierarchicalMemorySystem(db)
        system.initialize()
        
        memories = []
        for block_idx, block in system.ltm_layer.blocks.items():
            memory_data = {
                'content': block.memory_item.content,
                'keywords': block.memory_item.keywords,
                'tags': block.memory_item.tags,
                'importance': block.memory_item.importance,
                'timestamp': block.memory_item.timestamp.isoformat(),
                'metadata': block.memory_item.metadata,
                'original_block_index': block_idx
            }
            memories.append(memory_data)
        
        print(f"✅ {len(memories)}개 메모리 추출 완료")
        return memories
    
    def test_ltm_direct_approach(self, memories: List[Dict]) -> Dict[str, Any]:
        """LTM 직접 저장 방식 테스트"""
        print("\n🏛️  테스트 A: LTM 직접 저장 방식")
        
        # 임시 데이터베이스 생성
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            test_db_path = tmp_db.name
        
        try:
            db = DatabaseManager(test_db_path)
            system = HierarchicalMemorySystem(db)
            system.initialize()
            
            # 성능 측정 시작
            start_time = time.time()
            add_times = []
            
            # 메모리들을 직접 LTM에 저장
            for i, memory_data in enumerate(memories):
                add_start = time.time()
                
                # LTM에 직접 추가
                memory_item = create_memory_item(
                    content=memory_data['content'],
                    layer=MemoryLayerType.LTM,
                    keywords=memory_data['keywords'],
                    tags=memory_data['tags'],
                    importance=memory_data['importance'],
                    metadata=memory_data['metadata']
                )
                
                system.ltm_layer.add_memory(memory_item)
                
                add_time = time.time() - add_start
                add_times.append(add_time)
                
                if (i + 1) % 10 == 0:
                    print(f"   진행: {i+1}/{len(memories)} ({(i+1)/len(memories)*100:.1f}%)")
            
            total_time = time.time() - start_time
            
            # 검색 성능 테스트
            search_times = []
            for i in range(10):  # 10회 검색 테스트
                search_start = time.time()
                results = system.search_memories("테스트", limit=10)
                search_time = time.time() - search_start
                search_times.append(search_time)
            
            # 대시보드로 시스템 상태 확인
            dashboard = get_dashboard_system(db)
            health = dashboard.get_system_health()
            overview = dashboard.get_overview()
            
            return {
                'total_time': total_time,
                'avg_add_time': statistics.mean(add_times),
                'avg_search_time': statistics.mean(search_times),
                'memory_count': len(memories),
                'system_health': health.overall_health,
                'working_count': overview['memory_stats']['working_memory_count'],
                'stm_count': overview['memory_stats']['stm_count'], 
                'ltm_count': overview['memory_stats']['ltm_count'],
                'performance_details': {
                    'add_times_std': statistics.stdev(add_times) if len(add_times) > 1 else 0,
                    'search_times_std': statistics.stdev(search_times) if len(search_times) > 1 else 0,
                    'min_add_time': min(add_times),
                    'max_add_time': max(add_times),
                }
            }
            
        finally:
            # 정리
            try:
                os.unlink(test_db_path)
            except:
                pass
    
    def test_stm_priority_approach(self, memories: List[Dict]) -> Dict[str, Any]:
        """STM 우선 저장 방식 테스트"""
        print("\n⚡ 테스트 B: STM 우선 저장 방식")
        
        # 임시 데이터베이스 생성
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            test_db_path = tmp_db.name
        
        try:
            db = DatabaseManager(test_db_path)
            system = HierarchicalMemorySystem(db)
            system.initialize()
            
            # 성능 측정 시작
            start_time = time.time()
            add_times = []
            promotion_count = 0
            
            # 메모리들을 STM에 먼저 저장 후 자동 승급
            for i, memory_data in enumerate(memories):
                add_start = time.time()
                
                # STM에 먼저 추가
                memory_item = create_memory_item(
                    content=memory_data['content'],
                    layer=MemoryLayerType.STM,
                    keywords=memory_data['keywords'],
                    tags=memory_data['tags'],
                    importance=memory_data['importance'],
                    metadata=memory_data['metadata']
                )
                
                stm_success = system.stm_layer.add_memory(memory_item)
                
                # 중요도가 높으면(0.7 이상) LTM으로 자동 승급
                if memory_data['importance'] >= 0.7:
                    promotion_success = system.promote_memory(
                        memory_item.id, 
                        MemoryLayerType.LTM, 
                        "High importance auto-promotion"
                    )
                    if promotion_success:
                        promotion_count += 1
                
                add_time = time.time() - add_start
                add_times.append(add_time)
                
                if (i + 1) % 10 == 0:
                    print(f"   진행: {i+1}/{len(memories)} ({(i+1)/len(memories)*100:.1f}%)")
            
            total_time = time.time() - start_time
            
            # 검색 성능 테스트 (계층 횡단 검색)
            search_times = []
            for i in range(10):
                search_start = time.time()
                results = system.search_memories("테스트", limit=10)
                search_time = time.time() - search_start
                search_times.append(search_time)
            
            # 대시보드로 시스템 상태 확인
            dashboard = get_dashboard_system(db)
            health = dashboard.get_system_health()
            overview = dashboard.get_overview()
            
            return {
                'total_time': total_time,
                'avg_add_time': statistics.mean(add_times),
                'avg_search_time': statistics.mean(search_times),
                'memory_count': len(memories),
                'promotion_count': promotion_count,
                'promotion_rate': promotion_count / len(memories),
                'system_health': health.overall_health,
                'working_count': overview['memory_stats']['working_memory_count'],
                'stm_count': overview['memory_stats']['stm_count'],
                'ltm_count': overview['memory_stats']['ltm_count'],
                'performance_details': {
                    'add_times_std': statistics.stdev(add_times) if len(add_times) > 1 else 0,
                    'search_times_std': statistics.stdev(search_times) if len(search_times) > 1 else 0,
                    'min_add_time': min(add_times),
                    'max_add_time': max(add_times),
                }
            }
            
        finally:
            # 정리
            try:
                os.unlink(test_db_path)
            except:
                pass
    
    def compare_results(self, ltm_result: Dict, stm_result: Dict) -> None:
        """결과 비교 및 리포트"""
        print("\n" + "="*80)
        print("📊 STM vs LTM 직접저장 성능 비교 결과")
        print("="*80)
        
        print(f"\n🏛️  LTM 직접 저장 방식:")
        print(f"   총 소요 시간: {ltm_result['total_time']:.2f}초")
        print(f"   평균 추가 시간: {ltm_result['avg_add_time']*1000:.2f}ms")
        print(f"   평균 검색 시간: {ltm_result['avg_search_time']*1000:.2f}ms")
        print(f"   시스템 건강도: {ltm_result['system_health']*100:.1f}%")
        print(f"   메모리 분포: W:{ltm_result['working_count']} | S:{ltm_result['stm_count']} | L:{ltm_result['ltm_count']}")
        
        print(f"\n⚡ STM 우선 저장 방식:")
        print(f"   총 소요 시간: {stm_result['total_time']:.2f}초")
        print(f"   평균 추가 시간: {stm_result['avg_add_time']*1000:.2f}ms")
        print(f"   평균 검색 시간: {stm_result['avg_search_time']*1000:.2f}ms")
        print(f"   시스템 건강도: {stm_result['system_health']*100:.1f}%")
        print(f"   승급률: {stm_result['promotion_rate']*100:.1f}% ({stm_result['promotion_count']}/{stm_result['memory_count']})")
        print(f"   메모리 분포: W:{stm_result['working_count']} | S:{stm_result['stm_count']} | L:{stm_result['ltm_count']}")
        
        print(f"\n🔍 비교 분석:")
        
        # 성능 비교
        speed_diff = ((ltm_result['avg_add_time'] - stm_result['avg_add_time']) / ltm_result['avg_add_time']) * 100
        search_diff = ((ltm_result['avg_search_time'] - stm_result['avg_search_time']) / ltm_result['avg_search_time']) * 100
        health_diff = (stm_result['system_health'] - ltm_result['system_health']) * 100
        
        print(f"   추가 성능: STM이 {abs(speed_diff):.1f}% {'빠름' if speed_diff > 0 else '느림'}")
        print(f"   검색 성능: STM이 {abs(search_diff):.1f}% {'빠름' if search_diff > 0 else '느림'}")
        print(f"   건강도 차이: {health_diff:+.1f}%p")
        
        # 계층 활용도 비교
        ltm_total = ltm_result['working_count'] + ltm_result['stm_count'] + ltm_result['ltm_count']
        stm_total = stm_result['working_count'] + stm_result['stm_count'] + stm_result['ltm_count']
        
        print(f"\n🎯 계층 활용도:")
        print(f"   LTM 직접: STM 사용률 {ltm_result['stm_count']/ltm_total*100:.1f}%")
        print(f"   STM 우선: STM 사용률 {stm_result['stm_count']/stm_total*100:.1f}%")
        
        # 권장사항
        print(f"\n💡 권장사항:")
        if stm_result['system_health'] > ltm_result['system_health']:
            print("   ✅ STM 우선 방식이 시스템 건강도가 더 높습니다")
        else:
            print("   ⚠️  LTM 직접 방식이 시스템 건강도가 더 높습니다")
        
        if stm_result['stm_count'] > ltm_result['stm_count']:
            print("   ✅ STM 우선 방식이 계층적 아키텍처를 더 잘 활용합니다")
        else:
            print("   ⚠️  LTM 직접 방식도 STM을 활용하고 있습니다")
        
        # 결과를 파일로 저장
        comparison_result = {
            'timestamp': datetime.now().isoformat(),
            'ltm_direct': ltm_result,
            'stm_priority': stm_result,
            'analysis': {
                'speed_difference_percent': speed_diff,
                'search_difference_percent': search_diff,
                'health_difference_percent': health_diff,
                'stm_utilization_ltm_direct': ltm_result['stm_count']/ltm_total*100 if ltm_total > 0 else 0,
                'stm_utilization_stm_priority': stm_result['stm_count']/stm_total*100 if stm_total > 0 else 0,
            }
        }
        
        with open('stm_vs_ltm_comparison.json', 'w', encoding='utf-8') as f:
            json.dump(comparison_result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📁 상세 결과가 'stm_vs_ltm_comparison.json'에 저장되었습니다")
    
    def run_experiment(self):
        """전체 실험 실행"""
        print("🧪 STM vs LTM 성능 비교 실험 시작")
        print("="*50)
        
        # 1. 현재 데이터 추출
        memories = self.extract_current_memories()
        
        if len(memories) == 0:
            print("❌ 테스트할 메모리 데이터가 없습니다")
            return
        
        print(f"📊 테스트 데이터: {len(memories)}개 메모리")
        
        # 2. LTM 직접 저장 방식 테스트
        ltm_result = self.test_ltm_direct_approach(memories)
        
        # 3. STM 우선 저장 방식 테스트
        stm_result = self.test_stm_priority_approach(memories)
        
        # 4. 결과 비교
        self.compare_results(ltm_result, stm_result)


if __name__ == "__main__":
    print("🚀 STM vs LTM 직접저장 성능 비교 실험")
    
    tester = STMPerformanceTester()
    tester.run_experiment()