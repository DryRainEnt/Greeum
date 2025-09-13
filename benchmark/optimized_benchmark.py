"""
Optimized Branch System Performance Test
최적화된 브랜치 시스템 성능 테스트
"""

import time
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.performance_benchmark import PerformanceBenchmark
from benchmark.legacy_graph_system import LegacyGraphManager
from greeum.core.branch_manager import BranchManager
import logging

# 로깅 설정
logging.basicConfig(level=logging.WARNING)

class OptimizedBenchmark(PerformanceBenchmark):
    """최적화된 성능 벤치마크"""
    
    def run_optimized_branch_benchmark(self, workload: list, queries: list) -> dict:
        """최적화된 브랜치 시스템 벤치마크"""
        print("🚀 Running OPTIMIZED Branch-based System Benchmark...")
        
        branch_system = BranchManager()
        
        # 프로젝트별 슬롯 할당 최적화
        project_slots = {}
        slots = ['A', 'B', 'C']
        
        # 데이터 입력 성능
        insert_times = []
        for item in workload:
            project = item['project']
            if project not in project_slots:
                project_slots[project] = slots[len(project_slots) % len(slots)]
                
            start_time = time.time()
            branch_system.add_block(
                content=item['content'],
                root=project,
                slot=project_slots[project],
                tags={'labels': item['keywords']},
                importance=0.6  # 약간 더 높은 중요도
            )
            insert_times.append((time.time() - start_time) * 1000)
            
        # 검색 성능 (캐시 효과 테스트 포함)
        search_results = []
        repeated_queries = queries + queries[:len(queries)//3]  # 일부 쿼리 반복 (캐시 테스트)
        
        for query_item in repeated_queries:
            expected_project = query_item.get('expected_project')
            search_slot = project_slots.get(expected_project, 'A')
            
            start_time = time.time()
            result = branch_system.search(
                query=query_item['query'],
                slot=search_slot,
                k=10,
                fallback=True,
                depth=4  # 최적화된 깊이
            )
            search_time = (time.time() - start_time) * 1000
            
            search_results.append({
                'query': query_item['query'],
                'results_count': len(result.items),
                'search_time': search_time,
                'search_type': result.meta.get('search_type', 'unknown'),
                'hops': result.meta.get('hops', 0),
                'from_cache': result.meta.get('from_cache', False),
                'slot_used': search_slot
            })
            
        metrics = branch_system.get_metrics()
        
        # 검색 유형별 통계
        search_type_stats = {}
        for result in search_results:
            search_type = result['search_type']
            if search_type not in search_type_stats:
                search_type_stats[search_type] = {
                    'count': 0, 'total_time': 0, 'total_hops': 0
                }
            search_type_stats[search_type]['count'] += 1
            search_type_stats[search_type]['total_time'] += result['search_time']
            search_type_stats[search_type]['total_hops'] += result['hops']
            
        # 평균 계산
        for stats in search_type_stats.values():
            if stats['count'] > 0:
                stats['avg_time'] = stats['total_time'] / stats['count']
                stats['avg_hops'] = stats['total_hops'] / stats['count']
        
        # 캐시 통계
        cache_hits = sum(1 for r in search_results if r.get('from_cache', False))
        cache_hit_rate = cache_hits / len(search_results) if search_results else 0
        
        import statistics
        return {
            'system': 'optimized_branch',
            'workload_size': len(workload),
            'avg_insert_time': statistics.mean(insert_times),
            'p95_insert_time': statistics.quantiles(insert_times, n=20)[18] if len(insert_times) > 20 else max(insert_times),
            'avg_search_time': statistics.mean([r['search_time'] for r in search_results]),
            'avg_hops': metrics['avg_hops'],
            'local_hit_rate': metrics['local_hit_rate'],
            'fallback_rate': metrics.get('fallback_rate', 0.0),
            'cache_hit_rate': cache_hit_rate,
            'total_searches': len(search_results),
            'search_type_distribution': search_type_stats,
            'branch_stats': {
                'total_branches': len(branch_system.branches),
                'slot_distribution': project_slots,
                'cache_size': len(branch_system.search_cache)
            },
            'search_results': search_results
        }
    
    def run_comparison_test(self, workload_size: int = 100) -> dict:
        """3-way 비교 테스트: Legacy vs Original Branch vs Optimized Branch"""
        print(f"🔥 Running 3-Way Performance Comparison (workload: {workload_size})")
        
        # 워크로드 생성
        workload = self.generate_realistic_workload(
            num_sessions=workload_size // 20,
            blocks_per_session=20
        )
        queries = self.generate_search_queries(workload)
        
        print(f"📊 Generated {len(workload)} blocks and {len(queries)} queries")
        
        # 1. Legacy 시스템
        legacy_results = self.run_legacy_benchmark(workload, queries)
        
        # 2. Original Branch 시스템 (임시로 백업용 생성)
        original_results = self.run_branch_benchmark(workload, queries)
        
        # 3. Optimized Branch 시스템
        optimized_results = self.run_optimized_branch_benchmark(workload, queries)
        
        # 비교 분석
        comparison = {
            'timestamp': time.time(),
            'workload_size': len(workload),
            'query_count': len(queries),
            'legacy_results': legacy_results,
            'original_branch_results': original_results,
            'optimized_branch_results': optimized_results,
            'improvements': {
                'original_vs_legacy': self._safe_calculate_improvements(legacy_results, original_results),
                'optimized_vs_legacy': self._safe_calculate_improvements(legacy_results, optimized_results),
                'optimized_vs_original': self._safe_calculate_improvements(original_results, optimized_results)
            }
        }
        
        return comparison
    
    def print_three_way_comparison(self, results: dict):
        """3-way 비교 결과 출력"""
        print("\n" + "="*80)
        print("🔥 THREE-WAY PERFORMANCE COMPARISON")
        print("="*80)
        
        legacy = results['legacy_results']
        original = results['original_branch_results']
        optimized = results['optimized_branch_results']
        
        print(f"\n🔢 Workload: {results['workload_size']} blocks, {results['query_count']} queries")
        
        print(f"\n🔍 Search Performance Comparison:")
        print(f"  System               Avg Time    Avg Hops    Hit Rate    Cache Rate")
        print(f"  -------------------- ----------- ----------- ----------- -----------")
        print(f"  Legacy Graph         {legacy['avg_search_time']:>8.2f}ms {legacy['avg_hops']:>8.1f}    {legacy['hit_rate']:>8.1%}           -")
        print(f"  Original Branch      {original['avg_search_time']:>8.2f}ms {original['avg_hops']:>8.1f}    {original.get('local_hit_rate', 0):>8.1%}           -")
        print(f"  Optimized Branch     {optimized['avg_search_time']:>8.2f}ms {optimized['avg_hops']:>8.1f}    {optimized.get('local_hit_rate', 0):>8.1%}    {optimized.get('cache_hit_rate', 0):>8.1%}")
        
        print(f"\n📈 Optimization Impact:")
        opt_vs_orig = results['improvements']['optimized_vs_original']
        opt_vs_legacy = results['improvements']['optimized_vs_legacy']
        
        print(f"  Optimized vs Original Branch:")
        print(f"    Search Time:       {opt_vs_orig['search_time_improvement']:>+8.1f}%")
        print(f"    Hops Reduction:    {opt_vs_orig['hops_reduction']:>+8.1f}%")
        print(f"    Hit Rate Delta:    {opt_vs_orig['hit_rate_comparison']['improvement']:>+8.3f}")
        
        print(f"  Optimized vs Legacy Graph:")
        print(f"    Search Time:       {opt_vs_legacy['search_time_improvement']:>+8.1f}%")
        print(f"    Hops Reduction:    {opt_vs_legacy['hops_reduction']:>+8.1f}%")
        print(f"    Hit Rate Delta:    {opt_vs_legacy['hit_rate_comparison']['improvement']:>+8.3f}")
        
        # Search Type Distribution (Optimized)
        if 'search_type_distribution' in optimized:
            print(f"\n🌳 Optimized Branch Search Types:")
            for search_type, stats in optimized['search_type_distribution'].items():
                print(f"    {search_type:15}: {stats['count']:>3} searches, "
                      f"{stats.get('avg_time', 0):>5.1f}ms avg, "
                      f"{stats.get('avg_hops', 0):>4.1f} hops avg")
        
        print(f"\n💾 Cache Performance:")
        print(f"    Cache Hit Rate:     {optimized.get('cache_hit_rate', 0):>8.1%}")
        print(f"    Cache Size:         {optimized['branch_stats'].get('cache_size', 0):>8} entries")
        
        print("="*80)
    
    def _safe_calculate_improvements(self, old_results: dict, new_results: dict) -> dict:
        """안전한 개선 지표 계산"""
        
        def safe_percentage_improvement(old_val: float, new_val: float) -> float:
            if old_val == 0:
                return 0.0
            return ((old_val - new_val) / old_val) * 100
        
        improvements = {
            'search_time_improvement': safe_percentage_improvement(
                old_results.get('avg_search_time', 0),
                new_results.get('avg_search_time', 0)
            ),
            'hops_reduction': safe_percentage_improvement(
                old_results.get('avg_hops', 0),
                new_results.get('avg_hops', 0)
            ),
            'insert_time_improvement': safe_percentage_improvement(
                old_results.get('avg_insert_time', 0),
                new_results.get('avg_insert_time', 0)
            ),
            'hit_rate_comparison': {
                'old': old_results.get('hit_rate', old_results.get('local_hit_rate', 0)),
                'new': new_results.get('hit_rate', new_results.get('local_hit_rate', 0)),
                'improvement': (new_results.get('hit_rate', new_results.get('local_hit_rate', 0)) - 
                              old_results.get('hit_rate', old_results.get('local_hit_rate', 0)))
            }
        }
        
        return improvements


def main():
    """최적화된 벤치마크 실행"""
    benchmark = OptimizedBenchmark()
    
    # 테스트 크기들
    test_sizes = [100, 200]
    
    all_results = []
    
    for size in test_sizes:
        print(f"\n{'='*30} Testing {size} blocks {'='*30}")
        results = benchmark.run_comparison_test(workload_size=size)
        benchmark.print_three_way_comparison(results)
        all_results.append(results)
        
        # 개별 결과도 요약 출력
        benchmark.print_results_summary({
            'workload_size': results['workload_size'],
            'query_count': results['query_count'],
            'legacy_results': results['legacy_results'],
            'branch_results': results['optimized_branch_results'],
            'improvements': results['improvements']['optimized_vs_legacy'],
            'summary': {
                'search_time_improvement_pct': results['improvements']['optimized_vs_legacy']['search_time_improvement'],
                'avg_hops_reduction_pct': results['improvements']['optimized_vs_legacy']['hops_reduction'],
                'local_hit_rate': results['optimized_branch_results'].get('local_hit_rate', 0.0),
                'fallback_rate': results['optimized_branch_results'].get('fallback_rate', 0.0)
            }
        })
    
    # 결과 저장
    output_file = f"optimized_benchmark_results_{int(time.time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Optimized results saved to: {output_file}")
    
    return all_results


if __name__ == "__main__":
    results = main()