# Greeum 성능 테스트 계획

## 1. 목적 및 개요

이 문서는 Greeum 메모리 시스템의 효율성, 토큰 사용량 절감 및 응답 품질 향상 효과를 객관적으로 검증하기 위한 테스트 계획을 설명합니다. 

### 주요 검증 목표:
- 토큰 사용량 감소 효과 (비용 효율성)
- 응답 품질 향상 (정확성, 일관성, 구체성)
- 응답 속도 변화
- 장기 기억 유지 능력
- 다양한 상황에서의 성능 일관성

## 2. 테스트 환경 설계

### 변인 통제

**절대적으로 통제되어야 할 변인:**
- **동일한 LLM 모델 및 파라미터**: 모든 테스트는 정확히 동일한 LLM API, 모델 버전, 온도(temperature) 설정을 사용
- **동일한 테스트 시나리오**: 각 테스트 케이스에서 정확히 동일한 질문과 시나리오 사용
- **동일한 평가 기준**: 객관적이고 일관된 측정 기준 적용
- **실행 환경**: 동일한 하드웨어 및 네트워크 환경에서 테스트 실행

**주요 독립 변수:**
- Greeum 메모리 시스템 사용 여부 (있음/없음)
- 메모리 구성 방식 (전체 컨텍스트 vs 선택적 메모리)

## 3. 테스트 레포지토리 구조

```
greeum-benchmark/
├── config/
│   ├── test_scenarios.json    # 테스트 시나리오 정의
│   ├── llm_config.json        # LLM API 설정
│   └── benchmark_config.json  # 벤치마크 파라미터
├── scenarios/
│   ├── simple_qa.json         # 단순 Q&A 시나리오
│   ├── multi_turn.json        # 여러 차례 이어지는 대화
│   └── long_term_recall.json  # 장기 기억 테스트
├── metrics/
│   ├── token_counter.py       # 토큰 사용량 측정
│   ├── response_evaluator.py  # 응답 품질 평가
│   └── time_tracker.py        # 응답 시간 측정
├── runners/
│   ├── baseline_runner.py     # 기본 LLM 실행
│   └── greeum_runner.py       # Greeum 통합 LLM 실행
├── analysis/
│   ├── visualizer.py          # 결과 시각화
│   └── stats_calculator.py    # 통계적 유의성 분석
├── results/                   # 테스트 결과 저장소
├── requirements.txt           # 의존성 정의 (greeum 포함)
└── main.py                    # 벤치마크 실행 스크립트
```

## 4. Greeum 통합 및 구현

### 의존성 관리

```python
# requirements.txt
greeum==0.4.1  # 정확한 버전 명시로 재현 가능성 보장
openai==1.0.0
anthropic==0.5.0
numpy==1.24.0
pandas==2.0.0
matplotlib==3.7.0
pytest==7.3.1
```

### Greeum 명시적 임포트 및 사용

```python
# runners/greeum_runner.py
from greeum import BlockManager, STMManager, CacheManager, PromptWrapper
from greeum.text_utils import process_user_input, extract_keywords
from greeum.temporal_reasoner import TemporalReasoner

class GreeumRunner:
    def __init__(self, llm_config):
        # Greeum 컴포넌트 초기화
        self.block_manager = BlockManager()
        self.stm_manager = STMManager()
        self.cache_manager = CacheManager(
            block_manager=self.block_manager,
            stm_manager=self.stm_manager
        )
        self.prompt_wrapper = PromptWrapper(
            cache_manager=self.cache_manager,
            stm_manager=self.stm_manager
        )
        
        # LLM 설정
        self.llm_config = llm_config
        self.llm_client = self._init_llm_client()
    
    def _init_llm_client(self):
        # 설정에 따라 적절한 LLM 클라이언트 초기화
        if self.llm_config['provider'] == 'openai':
            from openai import OpenAI
            return OpenAI(api_key=self.llm_config['api_key'])
        elif self.llm_config['provider'] == 'anthropic':
            import anthropic
            return anthropic.Anthropic(api_key=self.llm_config['api_key'])
        # 다른 제공자 추가 가능
    
    def run_scenario(self, scenario):
        responses = []
        total_tokens = 0
        
        for turn in scenario['turns']:
            user_input = turn['user']
            
            # 1. 사용자 입력 처리
            processed = process_user_input(user_input)
            
            # 2. 캐시 업데이트 및 관련 기억 검색
            blocks = self.cache_manager.update_cache(
                user_input=user_input,
                query_embedding=processed['embedding'],
                extracted_keywords=processed['keywords']
            )
            
            # 3. 시간 건너뛰기 시뮬레이션 (있는 경우)
            if 'time_skip' in turn:
                # 시간 건너뛰기 처리 로직
                pass
            
            # 4. 프롬프트 생성
            prompt = self.prompt_wrapper.compose_prompt(user_input)
            
            # 5. LLM 호출
            if self.llm_config['provider'] == 'openai':
                response = self.llm_client.chat.completions.create(
                    model=self.llm_config['model'],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.llm_config['temperature']
                )
                answer = response.choices[0].message.content
                tokens = response.usage.total_tokens
            else:
                # 다른 제공자 처리
                pass
            
            # 6. 응답 저장
            responses.append(answer)
            total_tokens += tokens
            
            # 7. 단기 기억에 대화 저장
            self.stm_manager.add_memory({
                "content": user_input,
                "speaker": "user"
            })
            self.stm_manager.add_memory({
                "content": answer,
                "speaker": "assistant"
            })
        
        return responses, total_tokens
```

### 베이스라인 구현 (Greeum 없이)

```python
# runners/baseline_runner.py
class BaselineRunner:
    def __init__(self, llm_config):
        self.llm_config = llm_config
        self.llm_client = self._init_llm_client()
        self.conversation_history = []
    
    def _init_llm_client(self):
        # GreeumRunner와 동일한 코드로 LLM 클라이언트 초기화
        # 이로써 두 러너 간에 정확히 동일한 LLM 클라이언트 사용 보장
        if self.llm_config['provider'] == 'openai':
            from openai import OpenAI
            return OpenAI(api_key=self.llm_config['api_key'])
        elif self.llm_config['provider'] == 'anthropic':
            import anthropic
            return anthropic.Anthropic(api_key=self.llm_config['api_key'])
    
    def run_scenario(self, scenario):
        responses = []
        total_tokens = 0
        
        for turn in scenario['turns']:
            user_input = turn['user']
            
            # 시간 건너뛰기는 대화 히스토리 유지에 영향 없음
            # 1. 대화 히스토리에 사용자 입력 추가
            self.conversation_history.append({
                "role": "user", 
                "content": user_input
            })
            
            # 2. 대화 히스토리를 포함한 LLM 호출
            if self.llm_config['provider'] == 'openai':
                response = self.llm_client.chat.completions.create(
                    model=self.llm_config['model'],
                    messages=self.conversation_history,
                    temperature=self.llm_config['temperature']
                )
                answer = response.choices[0].message.content
                tokens = response.usage.total_tokens
            else:
                # 다른 제공자 처리
                pass
            
            # 3. 대화 히스토리에 응답 추가
            self.conversation_history.append({
                "role": "assistant", 
                "content": answer
            })
            
            # 4. 응답 저장
            responses.append(answer)
            total_tokens += tokens
        
        return responses, total_tokens
```

## 5. 테스트 시나리오 예시

### 장기 기억 테스트 시나리오

```json
{
  "name": "long_term_recall",
  "description": "장기 기억력 테스트 - 초기 대화에서 제공된 정보를 나중에 잘 기억하는지 테스트",
  "turns": [
    {
      "user": "안녕하세요! 제 이름은 김민수이고 서울 강남구에 살고 있어요. 취미는 등산과 사진 찍기입니다.",
      "expected_response_keywords": ["만나다", "반갑다", "김민수", "등산", "사진"]
    },
    {
      "user": "제가 가장 최근에 다녀온 산은 북한산이었어요. 정말 경치가 좋더라고요.",
      "expected_response_keywords": ["북한산", "경치", "좋다", "등산"]
    },
    {
      "user": "이번 주말에는 지리산에 가볼까 생각 중이에요.",
      "expected_response_keywords": ["지리산", "주말", "여행", "계획"]
    },
    {
      "time_skip": "3 days",
      "user": "저번에 말했던 주말 계획 기억나세요?",
      "expected_response_keywords": ["지리산", "등산", "주말"],
      "expected_facts": ["사용자는 지리산에 가려고 계획했다"]
    },
    {
      "time_skip": "1 week",
      "user": "제 이름이 뭐였죠?",
      "expected_response_keywords": ["김민수", "이름"],
      "expected_facts": ["사용자 이름은 김민수다"]
    },
    {
      "time_skip": "2 weeks",
      "user": "제가 어디 살고 있다고 했었죠?",
      "expected_response_keywords": ["서울", "강남구"],
      "expected_facts": ["사용자는 서울 강남구에 살고 있다"]
    }
  ],
  "expected_facts": [
    "사용자 이름은 김민수다",
    "사용자는 서울 강남구에 살고 있다",
    "사용자의 취미는 등산과 사진이다",
    "사용자는 최근 북한산에 다녀왔다",
    "사용자는 지리산에 가려고 계획했다"
  ]
}
```

### 토큰 효율성 테스트 시나리오

```json
{
  "name": "token_efficiency",
  "description": "긴 대화 기록에서 토큰 효율성 테스트",
  "turns": [
    {"user": "안녕하세요! 오늘 날씨에 대해 이야기해 볼까요?"},
    {"user": "오늘은 매우 맑고 화창한 날씨네요. 기온은 약 25도 정도입니다."},
    {"user": "내일은 비가 올 예정이라고 합니다. 우산을 준비해야겠어요."},
    {"user": "다음 주에는 날씨가 어떨까요? 주간 예보에 따르면 화요일부터 더워진다고 합니다."},
    {"user": "여름 휴가 계획은 세우셨나요? 저는 다음 달에 제주도에 가려고 합니다."},
    {"user": "제주도는 여름이 아름답다고 하더라고요. 특히 해변과 산책로가 좋다고 합니다."},
    {"user": "혹시 제주도에서 꼭 가봐야 할 곳이 있을까요?"},
    {"user": "성산일출봉과 우도는 꼭 가봐야 한다고 하네요. 맛있는 음식점도 많다고 합니다."},
    {"user": "여행 일정은 5일로 계획 중입니다. 일정이 너무 빡빡하지 않게 구성하고 싶어요."},
    {"user": "렌터카를 빌리는 게 좋을까요, 아니면 대중교통을 이용하는 게 좋을까요?"},
    {"user": "렌터카가 편리하지만 주차가 어려울 수 있다고 하네요. 혼잡한 시즌에는 예약이 필요합니다."},
    {"user": "숙소는 서쪽과 동쪽 모두에 예약하는 게 좋을까요, 아니면 한 곳에 머무는 게 좋을까요?"},
    {"user": "일정에 따라 다르지만, 이동 시간을 줄이려면 지역별로 숙소를 옮기는 게 좋다고 합니다."},
    {"user": "제주도 여행을 위한 예산은 얼마나 준비해야 할까요?"},
    {"user": "4인 가족 기준으로 약 200만원 정도가 적절하다고 합니다. 항공권, 숙소, 식비, 액티비티 비용 포함입니다."},
    {"user": "오늘 날씨가 어떻다고 했었죠?"}
  ]
}
```

## 6. 측정 및 평가 방법

### 토큰 사용량 측정

```python
# metrics/token_counter.py
class TokenCounter:
    def __init__(self):
        self.baseline_tokens = []
        self.greeum_tokens = []
    
    def add_baseline_measurement(self, tokens):
        self.baseline_tokens.append(tokens)
    
    def add_greeum_measurement(self, tokens):
        self.greeum_tokens.append(tokens)
    
    def calculate_savings(self):
        avg_baseline = sum(self.baseline_tokens) / len(self.baseline_tokens)
        avg_greeum = sum(self.greeum_tokens) / len(self.greeum_tokens)
        
        absolute_saving = avg_baseline - avg_greeum
        percentage_saving = (absolute_saving / avg_baseline) * 100
        
        return {
            "avg_baseline_tokens": avg_baseline,
            "avg_greeum_tokens": avg_greeum,
            "absolute_saving": absolute_saving,
            "percentage_saving": percentage_saving
        }
```

### 응답 품질 평가

```python
# metrics/response_evaluator.py
class ResponseEvaluator:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client  # LLM을 사용한 평가를 위한 클라이언트
    
    def evaluate(self, responses, expected_facts):
        """응답 품질 평가"""
        results = {
            "accuracy": self._evaluate_accuracy(responses, expected_facts),
            "consistency": self._evaluate_consistency(responses),
            "specificity": self._evaluate_specificity(responses)
        }
        
        # 종합 점수 계산 (가중치 적용 가능)
        results["overall_score"] = (
            results["accuracy"] * 0.5 + 
            results["consistency"] * 0.3 + 
            results["specificity"] * 0.2
        )
        
        return results
    
    def _evaluate_accuracy(self, responses, expected_facts):
        # 예상된 사실들이 응답에 포함되어 있는지 평가
        # 정확한 구현은 키워드 매칭, NLI 모델 또는 LLM 기반 평가 사용 가능
        pass
    
    def _evaluate_consistency(self, responses):
        # 응답들 간의 일관성 평가
        pass
    
    def _evaluate_specificity(self, responses):
        # 응답의 구체성 평가
        pass
```

## 7. 결과 분석 및 보고

```python
# analysis/stats_calculator.py
import numpy as np
import scipy.stats as stats

def calculate_significance(baseline_results, greeum_results):
    """두 결과 세트 간의 통계적 유의성 계산"""
    significance_results = {}
    
    # 토큰 사용량 비교
    baseline_tokens = [r['token_usage'] for r in baseline_results]
    greeum_tokens = [r['token_usage'] for r in greeum_results]
    
    t_stat, p_value = stats.ttest_ind(baseline_tokens, greeum_tokens)
    significance_results['token_usage'] = {
        't_statistic': t_stat,
        'p_value': p_value,
        'significant': p_value < 0.05
    }
    
    # 응답 품질 비교 (정확성)
    baseline_accuracy = [r['quality_metrics']['accuracy'] for r in baseline_results]
    greeum_accuracy = [r['quality_metrics']['accuracy'] for r in greeum_results]
    
    t_stat, p_value = stats.ttest_ind(baseline_accuracy, greeum_accuracy)
    significance_results['accuracy'] = {
        't_statistic': t_stat,
        'p_value': p_value,
        'significant': p_value < 0.05
    }
    
    # 다른 메트릭들에 대해서도 동일하게 진행
    
    return significance_results
```

```python
# analysis/visualizer.py
import matplotlib.pyplot as plt
import numpy as np

def visualize_results(baseline_results, greeum_results):
    """결과 시각화"""
    # 토큰 사용량 비교 그래프
    scenarios = [r['scenario'] for r in baseline_results]
    baseline_tokens = [r['token_usage'] for r in baseline_results]
    greeum_tokens = [r['token_usage'] for r in greeum_results]
    
    plt.figure(figsize=(12, 6))
    x = np.arange(len(scenarios))
    width = 0.35
    
    plt.bar(x - width/2, baseline_tokens, width, label='Baseline')
    plt.bar(x + width/2, greeum_tokens, width, label='Greeum')
    
    plt.xlabel('Scenarios')
    plt.ylabel('Token Usage')
    plt.title('Token Usage Comparison')
    plt.xticks(x, scenarios, rotation=45)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('results/token_usage_comparison.png')
    
    # 다른 메트릭에 대한 시각화도 추가
```

## 8. 테스트 실행 방법

```python
# main.py (핵심 부분)
def run_benchmark():
    # 설정 로드
    with open('config/benchmark_config.json') as f:
        config = json.load(f)
    
    # 시나리오 로드
    scenarios = []
    for scenario_file in os.listdir('scenarios'):
        with open(f'scenarios/{scenario_file}') as f:
            scenarios.append(json.load(f))
    
    # 측정 도구 초기화
    token_counter = TokenCounter()
    response_evaluator = ResponseEvaluator()
    time_tracker = TimeTracker()
    
    # 기준 테스트 및 Greeum 테스트 실행
    # ...코드 구현...
    
    # 결과 저장 및 시각화
    # ...코드 구현...

if __name__ == "__main__":
    run_benchmark()
```

## 9. 확장 및 추가 테스트

1. **다양한 LLM 모델 테스트**
   - GPT-4, Claude, Llama 등 다양한 모델에서의 성능 비교

2. **대규모 대화 테스트**
   - 수백 턴의 대화에서 메모리 관리 효율성 테스트

3. **다국어 지원 테스트**
   - 한국어, 영어, 일본어 등 다양한 언어에서의 성능 비교

4. **실제 사용자 테스트**
   - 실제 사용자와의 상호작용을 시뮬레이션한 테스트

## 결론

이 테스트 계획을 통해 Greeum 메모리 시스템의 효과를 객관적이고 체계적으로 검증할 수 있습니다. 통제된 환경에서 정확한 변인 통제를 통해 신뢰할 수 있는 결과를 도출하고, 이를 바탕으로 Greeum 시스템의 개선 방향을 설정할 수 있을 것입니다.

특히 중요한 점은 모든 테스트가 정확히 동일한 조건에서 이루어져야 한다는 것이며, 이를 위해 Greeum 라이브러리를 정확히 동일한 버전으로 임포트하고, LLM API 호출 시 모든 파라미터를 일관되게 유지해야 합니다. 