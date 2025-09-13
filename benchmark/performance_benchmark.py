"""
Performance Benchmark Suite
브랜치 기반 vs 그래프 기반 시스템 성능 비교
"""

import time
import random
import json
import uuid
import statistics
from typing import Dict, List, Any, Tuple
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.legacy_graph_system import LegacyGraphManager
from greeum.core.branch_manager import BranchManager
import logging

# 로깅 설정
logging.basicConfig(level=logging.WARNING)  # 노이즈 줄이기

class PerformanceBenchmark:
    """성능 벤치마크 러너"""
    
    def __init__(self):
        self.test_scenarios = []
        self.results = {
            'legacy_graph': {},
            'branch_based': {},
            'comparison': {}
        }
        
    def generate_realistic_workload(self, num_sessions: int = 5, 
                                   blocks_per_session: int = 20) -> List[Dict]:
        """
        현실적인 작업 부하 생성
        - 연속 개발 세션 시뮬레이션
        - 프로젝트별 작업 그룹핑
        """
        workload = []
        
        # 프로젝트 템플릿
        projects = [
            {
                'name': 'auth-service',
                'keywords': ['인증', '로그인', 'JWT', '토큰', '사용자', '보안'],
                'patterns': [
                    '{keyword} 구현 시작',
                    '{keyword} 버그 수정',
                    '{keyword} 테스트 추가',
                    '{keyword} 리팩토링',
                    '{keyword} 문서 작성'
                ]
            },
            {
                'name': 'data-pipeline',
                'keywords': ['데이터', '파이프라인', 'ETL', '처리', '변환', '저장'],
                'patterns': [
                    '{keyword} 파이프라인 설계',
                    '{keyword} 성능 최적화',
                    '{keyword} 에러 핸들링',
                    '{keyword} 모니터링 추가',
                    '{keyword} 스케일링'
                ]
            },
            {
                'name': 'frontend-app',
                'keywords': ['UI', '컴포넌트', '라우팅', '상태관리', '스타일링'],
                'patterns': [
                    '{keyword} 컴포넌트 개발',
                    '{keyword} 상태 연동',
                    '{keyword} 스타일 적용',
                    '{keyword} 반응형 대응',
                    '{keyword} 접근성 개선'
                ]
            }
        ]
        
        for session_id in range(num_sessions):
            project = random.choice(projects)
            session_start_time = time.time() - (num_sessions - session_id) * 24 * 3600
            
            for block_id in range(blocks_per_session):
                keyword = random.choice(project['keywords'])
                pattern = random.choice(project['patterns'])
                content = pattern.format(keyword=keyword)
                
                workload.append({
                    'session_id': session_id,
                    'project': project['name'],
                    'content': content,
                    'timestamp': session_start_time + block_id * 3600,  # 1시간 간격
                    'keywords': [keyword],
                    'block_id': f"{project['name']}_{session_id}_{block_id}"
                })
                
        return workload
    
    def generate_search_queries(self, workload: List[Dict]) -> List[Dict]:
        """
        현실적인 검색 쿼리 생성
        - 최근 작업 관련 검색
        - 키워드 조합 검색
        - 프로젝트 내/간 검색
        """
        queries = []
        
        # 프로젝트별 키워드 수집
        project_keywords = {}
        for item in workload:
            project = item['project']
            if project not in project_keywords:
                project_keywords[project] = set()
            project_keywords[project].update(item['keywords'])
        
        # 쿼리 패턴들
        query_patterns = [
            # 단일 키워드
            lambda: random.choice([kw for keywords in project_keywords.values() for kw in keywords]),
            
            # 프로젝트 내 조합
            lambda: ' '.join(random.sample(list(random.choice(list(project_keywords.values()))), 2)),
            
            # 문제 해결 패턴
            lambda: random.choice(['버그', '에러', '문제']) + ' ' + random.choice([kw for keywords in project_keywords.values() for kw in keywords]),
            
            # 구현 패턴  
            lambda: random.choice(['구현', '개발', '추가']) + ' ' + random.choice([kw for keywords in project_keywords.values() for kw in keywords]),
            
            # 최적화 패턴
            lambda: random.choice(['최적화', '성능', '개선']) + ' ' + random.choice([kw for keywords in project_keywords.values() for kw in keywords])
        ]
        
        for i in range(len(workload) // 2):  # 워크로드의 절반만큼 쿼리 생성
            pattern = random.choice(query_patterns)
            query = pattern()
            
            queries.append({
                'query_id': i,
                'query': query,
                'expected_project': random.choice(list(project_keywords.keys())),
                'query_time': time.time() - random.randint(0, 7 * 24 * 3600)  # 최근 일주일
            })
            
        return queries
    
    def run_legacy_benchmark(self, workload: List[Dict], queries: List[Dict]) -> Dict[str, Any]:
        """기존 그래프 시스템 벤치마크"""
        print("🔄 Running Legacy Graph System Benchmark...")
        
        legacy_system = LegacyGraphManager()
        
        # 데이터 입력 성능
        insert_times = []
        for item in workload:
            start_time = time.time()
            legacy_system.add_node(item['content'])
            insert_times.append((time.time() - start_time) * 1000)
            
        # 검색 성능
        search_results = []
        for query_item in queries:
            start_time = time.time()
            results, meta = legacy_system.search(query_item['query'], max_results=10)
            search_time = (time.time() - start_time) * 1000
            
            search_results.append({
                'query': query_item['query'],
                'results_count': len(results),
                'search_time': search_time,
                'hops': meta.get('hops', 0),
                'visited_nodes': meta.get('visited_nodes', 0)
            })
            
        metrics = legacy_system.get_metrics()
        graph_stats = legacy_system.get_graph_stats()
        
        return {
            'system': 'legacy_graph',
            'workload_size': len(workload),
            'avg_insert_time': statistics.mean(insert_times),
            'p95_insert_time': statistics.quantiles(insert_times, n=20)[18] if len(insert_times) > 20 else max(insert_times),
            'avg_search_time': metrics['avg_search_time'],
            'avg_hops': metrics['avg_hops'],
            'hit_rate': metrics['hit_rate'],
            'total_searches': len(queries),
            'graph_stats': graph_stats,
            'search_results': search_results
        }
    
    def run_branch_benchmark(self, workload: List[Dict], queries: List[Dict]) -> Dict[str, Any]:
        """브랜치 기반 시스템 벤치마크"""
        print("🌳 Running Branch-based System Benchmark...")
        
        branch_system = BranchManager()
        
        # 프로젝트별 슬롯 할당 시뮬레이션
        project_slots = {}
        slots = ['A', 'B', 'C']
        
        # 데이터 입력 성능
        insert_times = []
        for item in workload:
            # 프로젝트별 슬롯 배정
            project = item['project']
            if project not in project_slots:
                project_slots[project] = slots[len(project_slots) % len(slots)]
                
            start_time = time.time()
            branch_system.add_block(
                content=item['content'],
                root=project,
                slot=project_slots[project],
                tags={'labels': item['keywords']},
                importance=0.5
            )
            insert_times.append((time.time() - start_time) * 1000)
            
        # 검색 성능
        search_results = []
        for query_item in queries:
            # 프로젝트 관련 슬롯에서 검색 시뮬레이션
            expected_project = query_item.get('expected_project')
            search_slot = project_slots.get(expected_project, 'A')
            
            start_time = time.time()
            result = branch_system.search(
                query=query_item['query'], 
                slot=search_slot,
                k=10,
                fallback=True
            )
            search_time = (time.time() - start_time) * 1000
            
            search_results.append({
                'query': query_item['query'],
                'results_count': len(result.items),
                'search_time': search_time,
                'search_type': result.meta.get('search_type', 'unknown'),
                'hops': result.meta.get('hops', 0),
                'slot_used': search_slot
            })
            
        metrics = branch_system.get_metrics()
        
        return {
            'system': 'branch_based',
            'workload_size': len(workload),
            'avg_insert_time': statistics.mean(insert_times),
            'p95_insert_time': statistics.quantiles(insert_times, n=20)[18] if len(insert_times) > 20 else max(insert_times),
            'avg_search_time': statistics.mean([r['search_time'] for r in search_results]),
            'avg_hops': metrics['avg_hops'],
            'local_hit_rate': metrics['local_hit_rate'],
            'fallback_rate': metrics.get('fallback_rate', 0.0),
            'total_searches': len(queries),
            'branch_stats': {
                'total_branches': len(branch_system.branches),
                'slot_distribution': project_slots
            },
            'search_results': search_results
        }
    
    def calculate_improvements(self, legacy_results: Dict, branch_results: Dict) -> Dict[str, Any]:
        """개선 지표 계산"""
        
        def percentage_improvement(old_val: float, new_val: float) -> float:
            if old_val == 0:
                return 0.0
            return ((old_val - new_val) / old_val) * 100
        
        improvements = {
            'search_time_improvement': percentage_improvement(
                legacy_results['avg_search_time'],
                branch_results['avg_search_time']
            ),
            'hops_reduction': percentage_improvement(
                legacy_results['avg_hops'],
                branch_results['avg_hops']
            ),
            'insert_time_improvement': percentage_improvement(
                legacy_results['avg_insert_time'],
                branch_results['avg_insert_time']
            ),
            'p95_insert_improvement': percentage_improvement(
                legacy_results['p95_insert_time'],
                branch_results['p95_insert_time']
            ),
            'hit_rate_comparison': {
                'legacy': legacy_results['hit_rate'],
                'branch': branch_results.get('local_hit_rate', 0.0),
                'improvement': branch_results.get('local_hit_rate', 0.0) - legacy_results['hit_rate']
            }
        }
        
        # 검색 유형별 분석
        branch_search_types = {}
        for result in branch_results['search_results']:
            search_type = result['search_type']
            if search_type not in branch_search_types:
                branch_search_types[search_type] = {'count': 0, 'total_time': 0, 'total_hops': 0}
            branch_search_types[search_type]['count'] += 1
            branch_search_types[search_type]['total_time'] += result['search_time']
            branch_search_types[search_type]['total_hops'] += result['hops']
        
        # 평균 계산
        for search_type, stats in branch_search_types.items():
            if stats['count'] > 0:
                stats['avg_time'] = stats['total_time'] / stats['count']
                stats['avg_hops'] = stats['total_hops'] / stats['count']
                
        improvements['search_type_analysis'] = branch_search_types
        
        return improvements
    
    def run_comparative_benchmark(self, workload_size: int = 100) -> Dict[str, Any]:
        """비교 벤치마크 실행"""
        print(f"🚀 Starting Comparative Performance Benchmark (workload: {workload_size})")
        
        # 워크로드 생성
        workload = self.generate_realistic_workload(
            num_sessions=workload_size // 20,
            blocks_per_session=20
        )
        queries = self.generate_search_queries(workload)
        
        print(f"📊 Generated {len(workload)} blocks and {len(queries)} queries")
        
        # 기존 시스템 벤치마크
        legacy_results = self.run_legacy_benchmark(workload, queries)
        
        # 브랜치 시스템 벤치마크  
        branch_results = self.run_branch_benchmark(workload, queries)
        
        # 개선 지표 계산
        improvements = self.calculate_improvements(legacy_results, branch_results)
        
        # 종합 결과
        comprehensive_results = {
            'timestamp': time.time(),
            'workload_size': len(workload),
            'query_count': len(queries),
            'legacy_results': legacy_results,
            'branch_results': branch_results,
            'improvements': improvements,
            'summary': {
                'search_time_improvement_pct': improvements['search_time_improvement'],
                'avg_hops_reduction_pct': improvements['hops_reduction'],
                'local_hit_rate': branch_results.get('local_hit_rate', 0.0),
                'fallback_rate': branch_results.get('fallback_rate', 0.0)
            }
        }
        
        return comprehensive_results
    
    def print_results_summary(self, results: Dict[str, Any]):
        """결과 요약 출력"""
        print("\n" + "="*60)
        print("📈 PERFORMANCE BENCHMARK RESULTS")
        print("="*60)
        
        legacy = results['legacy_results']
        branch = results['branch_results']
        improvements = results['improvements']
        
        print(f"\n🔢 Workload: {results['workload_size']} blocks, {results['query_count']} queries")
        
        print(f"\n🔍 Search Performance:")
        print(f"  Legacy Avg Time:    {legacy['avg_search_time']:.2f}ms")
        print(f"  Branch Avg Time:    {branch['avg_search_time']:.2f}ms")
        print(f"  ⚡ Improvement:      {improvements['search_time_improvement']:.1f}%")
        
        print(f"\n🔗 Navigation Efficiency:")
        print(f"  Legacy Avg Hops:    {legacy['avg_hops']:.1f}")
        print(f"  Branch Avg Hops:    {branch['avg_hops']:.1f}")
        print(f"  ⚡ Reduction:        {improvements['hops_reduction']:.1f}%")
        
        print(f"\n💾 Insert Performance:")
        print(f"  Legacy Avg Time:    {legacy['avg_insert_time']:.2f}ms")
        print(f"  Branch Avg Time:    {branch['avg_insert_time']:.2f}ms")
        print(f"  ⚡ Improvement:      {improvements['insert_time_improvement']:.1f}%")
        
        print(f"\n🎯 Hit Rate Analysis:")
        print(f"  Legacy Hit Rate:    {legacy['hit_rate']:.3f}")
        print(f"  Branch Local Hit:   {branch.get('local_hit_rate', 0):.3f}")
        print(f"  Branch Fallback:    {branch.get('fallback_rate', 0):.3f}")
        
        if 'search_type_analysis' in improvements:
            print(f"\n🌳 Branch Search Type Distribution:")
            for search_type, stats in improvements['search_type_analysis'].items():
                print(f"  {search_type:12}: {stats['count']:3} searches, {stats.get('avg_time', 0):.1f}ms avg, {stats.get('avg_hops', 0):.1f} hops avg")
        
        print(f"\n📊 Summary:")
        summary = results['summary']
        print(f"  🚀 Search Speed Up:   {summary['search_time_improvement_pct']:+.1f}%")
        print(f"  📉 Hops Reduction:    {summary['avg_hops_reduction_pct']:+.1f}%") 
        print(f"  🎯 Local Hit Rate:    {summary['local_hit_rate']:.1%}")
        print(f"  🔄 Fallback Rate:     {summary['fallback_rate']:.1%}")
        
        print("="*60)


def main():
    """메인 벤치마크 실행"""
    benchmark = PerformanceBenchmark()
    
    # 다양한 크기로 테스트
    test_sizes = [50, 100, 200]
    
    all_results = []
    
    for size in test_sizes:
        print(f"\n{'='*20} Testing with {size} blocks {'='*20}")
        results = benchmark.run_comparative_benchmark(workload_size=size)
        benchmark.print_results_summary(results)
        all_results.append(results)
        
    # 결과 저장
    output_file = f"benchmark_results_{int(time.time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    return all_results


if __name__ == "__main__":
    results = main()