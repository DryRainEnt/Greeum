"""
Ultra-Optimized Branch System Performance Test
초극적 최적화 브랜치 시스템 성능 테스트 (Phase 3)
"""

import time
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmark.optimized_benchmark import OptimizedBenchmark
import logging

# 로깅 설정
logging.basicConfig(level=logging.WARNING)

class UltraOptimizedBenchmark(OptimizedBenchmark):
    """초극적 최적화된 성능 벤치마크"""
    
    def run_ultra_optimized_branch_benchmark(self, workload: list, queries: list) -> dict:
        """초극적 최적화 브랜치 시스템 벤치마크"""
        print("🔥 Running ULTRA-OPTIMIZED Branch-based System Benchmark...")
        print(f"📋 New Parameters:")
        print(f"   - DEPTH_DEFAULT: 6 (was 4)")
        print(f"   - K_DEFAULT: 20 (was 12)")
        print(f"   - SIMILARITY_THRESHOLD: 0.02 (was 0.05)")
        print(f"   - MIN_SIMILARITY_SCORE: 0.1 (new)")
        print(f"   - Bidirectional DFS + Sibling search")
        
        from greeum.core.branch_manager import BranchManager
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
                importance=0.6
            )
            insert_times.append((time.time() - start_time) * 1000)
            
        # 검색 성능 (캐시 효과 테스트 포함)
        search_results = []
        repeated_queries = queries + queries[:len(queries)//3]  # 캐시 테스트용 반복 쿼리
        
        for query_item in repeated_queries:
            expected_project = query_item.get('expected_project')
            search_slot = project_slots.get(expected_project, 'A')
            
            start_time = time.time()
            result = branch_system.search(
                query=query_item['query'],
                slot=search_slot,
                k=10,
                fallback=True,
                depth=6  # 초극적 최적화된 깊이
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
            'system': 'ultra_optimized_branch',
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
            'ultra_optimizations': {
                'depth_default': 6,
                'k_default': 20,
                'similarity_threshold': 0.02,
                'min_similarity_score': 0.1,
                'bidirectional_dfs': True,
                'sibling_search': True
            },
            'search_results': search_results
        }
    
    def run_four_way_comparison_test(self, workload_size: int = 100) -> dict:
        """4-way 비교 테스트: Legacy vs Original vs Optimized vs Ultra-Optimized"""
        print(f"🚀 Running 4-Way Ultra-Performance Comparison (workload: {workload_size})")
        
        # 워크로드 생성
        workload = self.generate_realistic_workload(
            num_sessions=workload_size // 20,
            blocks_per_session=20
        )
        queries = self.generate_search_queries(workload)
        
        print(f"📊 Generated {len(workload)} blocks and {len(queries)} queries")
        
        # 1. Legacy 시스템
        legacy_results = self.run_legacy_benchmark(workload, queries)
        
        # 2. Original Branch 시스템
        original_results = self.run_branch_benchmark(workload, queries)
        
        # 3. Optimized Branch 시스템
        optimized_results = self.run_optimized_branch_benchmark(workload, queries)
        
        # 4. Ultra-Optimized Branch 시스템
        ultra_results = self.run_ultra_optimized_branch_benchmark(workload, queries)
        
        # 비교 분석
        comparison = {
            'timestamp': time.time(),
            'workload_size': len(workload),
            'query_count': len(queries),
            'legacy_results': legacy_results,
            'original_branch_results': original_results,
            'optimized_branch_results': optimized_results,
            'ultra_optimized_results': ultra_results,
            'improvements': {
                'original_vs_legacy': self._safe_calculate_improvements(legacy_results, original_results),
                'optimized_vs_legacy': self._safe_calculate_improvements(legacy_results, optimized_results),
                'ultra_vs_legacy': self._safe_calculate_improvements(legacy_results, ultra_results),
                'ultra_vs_optimized': self._safe_calculate_improvements(optimized_results, ultra_results)
            }
        }
        
        return comparison
    
    def print_four_way_comparison(self, results: dict):
        """4-way 비교 결과 출력"""
        print("\n" + "="*90)
        print("🚀 FOUR-WAY ULTRA PERFORMANCE COMPARISON")
        print("="*90)
        
        legacy = results['legacy_results']
        original = results['original_branch_results']
        optimized = results['optimized_branch_results']
        ultra = results['ultra_optimized_results']
        
        print(f"\n🔢 Workload: {results['workload_size']} blocks, {results['query_count']} queries")
        
        print(f"\n🔍 Search Performance Comparison:")
        print(f"  System                     Avg Time    Avg Hops    Hit Rate    Cache Rate")
        print(f"  -------------------------- ----------- ----------- ----------- -----------")
        print(f"  Legacy Graph               {legacy['avg_search_time']:>8.2f}ms {legacy['avg_hops']:>8.1f}    {legacy['hit_rate']:>8.1%}           -")
        print(f"  Original Branch            {original['avg_search_time']:>8.2f}ms {original['avg_hops']:>8.1f}    {original.get('local_hit_rate', 0):>8.1%}           -")
        print(f"  Optimized Branch           {optimized['avg_search_time']:>8.2f}ms {optimized['avg_hops']:>8.1f}    {optimized.get('local_hit_rate', 0):>8.1%}    {optimized.get('cache_hit_rate', 0):>8.1%}")
        print(f"  ULTRA-Optimized Branch     {ultra['avg_search_time']:>8.2f}ms {ultra['avg_hops']:>8.1f}    {ultra.get('local_hit_rate', 0):>8.1%}    {ultra.get('cache_hit_rate', 0):>8.1%}")
        
        print(f"\n📈 Ultimate Optimization Impact:")
        ultra_vs_legacy = results['improvements']['ultra_vs_legacy']
        ultra_vs_optimized = results['improvements']['ultra_vs_optimized']
        
        print(f"  Ultra-Optimized vs Legacy Graph:")
        print(f"    Search Time:       {ultra_vs_legacy['search_time_improvement']:>+8.1f}%")
        print(f"    Hops Reduction:    {ultra_vs_legacy['hops_reduction']:>+8.1f}%")
        print(f"    Hit Rate Delta:    {ultra_vs_legacy['hit_rate_comparison']['improvement']:>+8.3f}")
        
        print(f"  Ultra-Optimized vs Previous Optimized:")
        print(f"    Search Time:       {ultra_vs_optimized['search_time_improvement']:>+8.1f}%")
        print(f"    Hops Reduction:    {ultra_vs_optimized['hops_reduction']:>+8.1f}%")
        print(f"    Hit Rate Delta:    {ultra_vs_optimized['hit_rate_comparison']['improvement']:>+8.3f}")
        
        # Ultra Optimizations Applied
        if 'ultra_optimizations' in ultra:
            print(f"\n🔥 Ultra Optimizations Applied:")
            opts = ultra['ultra_optimizations']
            print(f"    Depth Limit:       {opts['depth_default']} (was 4)")
            print(f"    Candidate Limit:   {opts['k_default']} (was 12)")
            print(f"    Similarity Thres:  {opts['similarity_threshold']} (was 0.05)")
            print(f"    Min Score:         {opts['min_similarity_score']} (new)")
            print(f"    Bidirectional:     {opts['bidirectional_dfs']}")
            print(f"    Sibling Search:    {opts['sibling_search']}")
        
        # Search Type Distribution (Ultra)
        if 'search_type_distribution' in ultra:
            print(f"\n🌳 Ultra-Optimized Search Types:")
            for search_type, stats in ultra['search_type_distribution'].items():
                print(f"    {search_type:15}: {stats['count']:>3} searches, "
                      f"{stats.get('avg_time', 0):>5.1f}ms avg, "
                      f"{stats.get('avg_hops', 0):>4.1f} hops avg")
        
        print(f"\n💾 Final Performance Metrics:")
        print(f"    Local Hit Rate:     {ultra.get('local_hit_rate', 0):>8.1%}")
        print(f"    Cache Hit Rate:     {ultra.get('cache_hit_rate', 0):>8.1%}")
        print(f"    Fallback Rate:      {ultra.get('fallback_rate', 0):>8.1%}")
        print(f"    Cache Size:         {ultra['branch_stats'].get('cache_size', 0):>8} entries")
        
        print("="*90)


def main():
    """초극적 최적화 벤치마크 실행"""
    benchmark = UltraOptimizedBenchmark()
    
    # 테스트 크기들
    test_sizes = [100, 200]
    
    all_results = []
    
    for size in test_sizes:
        print(f"\n{'='*30} Ultra-Testing {size} blocks {'='*30}")
        results = benchmark.run_four_way_comparison_test(workload_size=size)
        benchmark.print_four_way_comparison(results)
        all_results.append(results)
    
    # 결과 저장
    output_file = f"ultra_optimized_benchmark_results_{int(time.time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Ultra-optimized results saved to: {output_file}")
    
    # 최종 요약
    print(f"\n{'='*90}")
    print("🔥 ULTRA-OPTIMIZATION SUMMARY")
    print("="*90)
    
    final_result = all_results[-1]['ultra_optimized_results']
    print(f"🎯 Final Local Hit Rate: {final_result.get('local_hit_rate', 0):.1%}")
    print(f"⚡ Final Search Time: {final_result['avg_search_time']:.2f}ms")
    print(f"🎯 Final Cache Hit Rate: {final_result.get('cache_hit_rate', 0):.1%}")
    print(f"🔗 Final Hop Count: {final_result['avg_hops']:.1f}")
    print("="*90)
    
    return all_results


if __name__ == "__main__":
    results = main()