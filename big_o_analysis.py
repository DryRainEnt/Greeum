#!/usr/bin/env python3
"""
Greeum 인과관계 시스템 Big-O 복잡도 분석

성능 테스트 데이터를 기반으로 알고리즘의 시간 복잡도를 
수학적으로 분석하고 Big-O 노테이션으로 표현
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import math

class BigOAnalyzer:
    """Big-O 복잡도 분석 도구"""
    
    def __init__(self):
        """성능 테스트 결과 데이터 초기화"""
        
        # 성능 테스트에서 얻은 실제 데이터
        self.performance_data = {
            # 메모리 개수 → 분석 시간(초)
            10: 0.002,
            50: 0.073,
            100: 0.330,
            200: 1.335,
            # 확장성 테스트 데이터 (평균 분석 시간)
            100: 0.320,  # 실제 확장성 테스트 결과
            300: 1.159,
            500: 1.318,
            700: 1.297,
            1000: 1.275
        }
        
        # 정제된 데이터 (중복 제거 및 정렬)
        self.n_values = np.array([10, 50, 100, 200, 300, 500, 700, 1000])
        self.time_values = np.array([0.002, 0.073, 0.320, 1.335, 1.159, 1.318, 1.297, 1.275])
        
        print(f"📊 Big-O 복잡도 분석 시작")
        print(f"   분석 데이터 포인트: {len(self.n_values)}개")
        
    def analyze_complexity_patterns(self):
        """다양한 복잡도 패턴과의 매칭 분석"""
        
        print(f"\n🔍 복잡도 패턴 매칭 분석")
        
        # 다양한 복잡도 함수 정의
        def constant(n, c):
            return c * np.ones_like(n)
        
        def linear(n, a, b):
            return a * n + b
            
        def quadratic(n, a, b, c):
            return a * n**2 + b * n + c
            
        def logarithmic(n, a, b):
            return a * np.log(n) + b
            
        def n_log_n(n, a, b):
            return a * n * np.log(n) + b
            
        def cubic(n, a, b, c, d):
            return a * n**3 + b * n**2 + c * n + d
        
        # 각 복잡도에 대해 피팅 시도
        complexity_functions = {
            'O(1) - Constant': (constant, 1),
            'O(log n) - Logarithmic': (logarithmic, 2),
            'O(n) - Linear': (linear, 2),
            'O(n log n) - Linearithmic': (n_log_n, 2),
            'O(n²) - Quadratic': (quadratic, 3),
            'O(n³) - Cubic': (cubic, 4)
        }
        
        results = {}
        
        for name, (func, param_count) in complexity_functions.items():
            try:
                # 곡선 피팅
                if param_count <= 4:  # 매개변수가 너무 많으면 과적합 위험
                    popt, pcov = curve_fit(func, self.n_values, self.time_values, 
                                         maxfev=5000)
                    
                    # 예측값 계산
                    predicted = func(self.n_values, *popt)
                    
                    # R² 스코어 계산 (결정계수)
                    ss_res = np.sum((self.time_values - predicted) ** 2)
                    ss_tot = np.sum((self.time_values - np.mean(self.time_values)) ** 2)
                    r_squared = 1 - (ss_res / ss_tot)
                    
                    # RMSE 계산
                    rmse = np.sqrt(np.mean((self.time_values - predicted) ** 2))
                    
                    results[name] = {
                        'r_squared': r_squared,
                        'rmse': rmse,
                        'parameters': popt,
                        'predicted': predicted,
                        'function': func
                    }
                    
                    print(f"   {name:25}: R² = {r_squared:.4f}, RMSE = {rmse:.4f}")
                    
            except Exception as e:
                print(f"   {name:25}: 피팅 실패 - {e}")
        
        return results
    
    def identify_best_fit(self, results):
        """최적 복잡도 패턴 식별"""
        
        print(f"\n🎯 최적 복잡도 패턴 분석")
        
        if not results:
            print("   분석할 결과가 없습니다.")
            return None
        
        # R² 스코어 기준으로 정렬
        sorted_results = sorted(results.items(), 
                               key=lambda x: x[1]['r_squared'], 
                               reverse=True)
        
        print(f"📈 복잡도 매칭 결과 (R² 스코어 순):")
        for i, (name, data) in enumerate(sorted_results):
            status = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "  "
            print(f"   {status} {name:25}: R² = {data['r_squared']:.4f}")
        
        # 최적 매칭 분석
        best_name, best_data = sorted_results[0]
        
        print(f"\n🏆 최적 매칭: {best_name}")
        print(f"   R² 스코어: {best_data['r_squared']:.4f} (1.0에 가까울수록 좋음)")
        print(f"   RMSE: {best_data['rmse']:.4f} (0에 가까울수록 좋음)")
        
        # 실제 vs 예측값 비교
        print(f"\n📊 실제 vs 예측 비교:")
        print(f"{'메모리 수':>8} | {'실제(초)':>10} | {'예측(초)':>10} | {'오차':>8}")
        print("-" * 45)
        
        for n, actual, predicted in zip(self.n_values, self.time_values, best_data['predicted']):
            error = abs(actual - predicted) / actual * 100
            print(f"{n:>8} | {actual:>10.3f} | {predicted:>10.3f} | {error:>6.1f}%")
        
        return best_name, best_data
    
    def analyze_practical_implications(self, best_match):
        """실용적 의미 분석"""
        
        if not best_match:
            return
            
        best_name, best_data = best_match
        
        print(f"\n💡 실용적 의미 분석")
        print(f"현재 시스템의 복잡도: {best_name}")
        
        # 복잡도별 확장성 예측
        if 'O(n²)' in best_name or 'Quadratic' in best_name:
            print(f"   📈 특성: 메모리 개수 증가 시 처리 시간이 제곱에 비례해 증가")
            print(f"   ⚠️  주의: 대용량 데이터에서 성능 저하 가능성")
            
            # 10,000개 메모리 예측
            func = best_data['function']
            params = best_data['parameters']
            predicted_10k = func(10000, *params)
            print(f"   🔮 예측: 10,000개 메모리 분석 시간 ≈ {predicted_10k:.1f}초")
            
        elif 'O(n log n)' in best_name or 'Linearithmic' in best_name:
            print(f"   📈 특성: 효율적인 복잡도 - 대부분의 고성능 알고리즘 수준")
            print(f"   ✅ 평가: 대용량 데이터에도 적합한 복잡도")
            
        elif 'O(n)' in best_name or 'Linear' in best_name:
            print(f"   📈 특성: 선형 복잡도 - 매우 효율적")
            print(f"   🌟 평가: 이상적인 확장성")
            
        elif 'O(log n)' in best_name or 'Logarithmic' in best_name:
            print(f"   📈 특성: 로그 복잡도 - 극도로 효율적")
            print(f"   🚀 평가: 최고 수준의 성능")
        
        # 병목 지점 분석
        print(f"\n🔍 성능 병목 분석:")
        
        # 메모리 개수별 성능 변화율 계산
        for i in range(1, len(self.n_values)):
            n_ratio = self.n_values[i] / self.n_values[i-1]
            time_ratio = self.time_values[i] / self.time_values[i-1]
            
            print(f"   {self.n_values[i-1]:4d} → {self.n_values[i]:4d}: "
                  f"크기 {n_ratio:.1f}배 증가 → 시간 {time_ratio:.1f}배 증가")
        
        # 최적화 권장사항
        print(f"\n🎯 최적화 권장사항:")
        
        if best_data['r_squared'] < 0.8:
            print(f"   ⚠️  일관성 부족: 복잡도 패턴이 불안정함 (R² < 0.8)")
            print(f"      → 알고리즘 내부 최적화 필요")
        
        # 특이 구간 식별
        largest_jump = 0
        largest_jump_point = 0
        
        for i in range(1, len(self.time_values)):
            ratio = self.time_values[i] / self.time_values[i-1]
            if ratio > largest_jump:
                largest_jump = ratio
                largest_jump_point = self.n_values[i]
        
        if largest_jump > 5:  # 5배 이상 급증
            print(f"   🚨 성능 급감 지점: {largest_jump_point}개 메모리에서 {largest_jump:.1f}배 급증")
            print(f"      → 이 지점에서 알고리즘 동작 방식 변경 추정")
    
    def theoretical_complexity_analysis(self):
        """이론적 복잡도 분석"""
        
        print(f"\n🧠 이론적 복잡도 분석")
        
        print(f"인과관계 분석 시스템의 구성 요소:")
        print(f"   1. 벡터 유사도 계산: O(d) where d = embedding_dim (128)")
        print(f"   2. 후보 필터링: O(n) where n = memory_count")  
        print(f"   3. 인과관계 점수 계산: O(k) where k = candidates (≈11)")
        print(f"   4. 브릿지 탐지: O(k²) for candidate pairs")
        
        print(f"\n전체 복잡도 구성:")
        print(f"   • 단일 메모리 분석: O(n) + O(k²) ≈ O(n) (k는 작은 상수)")
        print(f"   • 벡터 필터링이 97% 계산 절약 → 실제로는 O(k) ≈ O(1)")
        print(f"   • 하지만 k는 n에 비례하여 증가 가능 → 실질적으로 O(n)")
        
        print(f"\n실측 데이터와 이론의 차이:")
        print(f"   이론: O(n) - 선형 증가 예상")
        print(f"   실측: 분석 결과에 따라 달라짐")
    
    def visualize_complexity(self, results):
        """복잡도 시각화"""
        
        print(f"\n📊 복잡도 패턴 시각화")
        
        if not results:
            print("   시각화할 데이터가 없습니다.")
            return
        
        # 상위 3개 복잡도 패턴만 시각화
        sorted_results = sorted(results.items(), 
                               key=lambda x: x[1]['r_squared'], 
                               reverse=True)[:3]
        
        plt.figure(figsize=(12, 8))
        
        # 실제 데이터 플롯
        plt.scatter(self.n_values, self.time_values, 
                   color='red', s=100, zorder=5, label='실제 데이터')
        
        # 각 복잡도 패턴의 예측 곡선 플롯
        colors = ['blue', 'green', 'orange']
        x_smooth = np.linspace(10, 1000, 200)
        
        for i, (name, data) in enumerate(sorted_results):
            try:
                func = data['function']
                params = data['parameters']
                y_smooth = func(x_smooth, *params)
                
                plt.plot(x_smooth, y_smooth, 
                        color=colors[i], linewidth=2,
                        label=f'{name} (R²={data["r_squared"]:.3f})')
            except:
                continue
        
        plt.xlabel('메모리 개수 (n)', fontsize=12)
        plt.ylabel('분석 시간 (초)', fontsize=12)
        plt.title('Greeum 인과관계 시스템 복잡도 분석', fontsize=14)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.yscale('log')  # 로그 스케일로 보기
        plt.xscale('log')
        
        plt.tight_layout()
        plt.savefig('complexity_analysis.png', dpi=300, bbox_inches='tight')
        print(f"   시각화 저장: complexity_analysis.png")
        plt.close()

def main():
    """메인 분석 실행"""
    
    print("🔬 Greeum 인과관계 시스템 Big-O 복잡도 분석")
    print("=" * 60)
    
    analyzer = BigOAnalyzer()
    
    # 1단계: 복잡도 패턴 매칭
    results = analyzer.analyze_complexity_patterns()
    
    # 2단계: 최적 매칭 식별
    best_match = analyzer.identify_best_fit(results)
    
    # 3단계: 실용적 의미 분석
    analyzer.analyze_practical_implications(best_match)
    
    # 4단계: 이론적 분석
    analyzer.theoretical_complexity_analysis()
    
    # 5단계: 시각화
    analyzer.visualize_complexity(results)
    
    print(f"\n🎉 Big-O 복잡도 분석 완료!")

if __name__ == "__main__":
    main()