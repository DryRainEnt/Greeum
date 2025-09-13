# Greeum v3.0.0: Context-Dependent Memory System
## 인간 기억 구조 기반 설계

---

## 🧠 **연구 기반 핵심 발견**

### 1. **Context-Dependent Memory Formation**
> "When a new context is encountered, a unique hippocampal ensemble is recruited to represent it. Memories for events that occur in the context become associated with the hippocampal representation."

**번역**: 새로운 맥락을 만나면, 해마가 고유한 앙상블을 만들고, 그 맥락에서 일어난 모든 기억이 연결됨

### 2. **현재 활성화 위치 기반 기록**
> "Place-responsive cell activity was reinstated during episodic memory retrieval... similar to the activity that represented the locations where the memory was initially encoded."

**번역**: 기억은 **현재 활성화된 위치**에서 기록되고, 회상할 때도 그 위치가 다시 활성화됨

### 3. **Spreading Activation (연상 작용)**
> "The theory of spreading activation proposes that the activation of a semantic memory node may spread along bidirectional associative links to other related nodes."

**번역**: 하나의 기억이 활성화되면 연결된 다른 기억들도 자동으로 활성화됨

---

## 💡 **당신이 원했던 것 vs 현실**

### STM/LTM 분리의 의도 (좋았음)
- ✅ STM = 현재 활성화된 컨텍스트
- ✅ LTM = 영구 저장된 네트워크
- ✅ 의미/맥락 기반 연상

### 실제 구현의 문제 (엉성했음)
- ❌ STM이 그냥 임시 버퍼
- ❌ LTM이 그냥 일렬 나열
- ❌ 컨텍스트 연결 없음

---

## 🎯 **진짜 인간같은 메모리 시스템**

### 핵심 원리: Context as Hub

```python
class ContextDependentMemory:
    """인간 기억처럼 작동하는 시스템"""
    
    def __init__(self):
        # 현재 활성 컨텍스트 (STM 역할)
        self.active_context = None
        self.context_nodes = {}  # 활성화된 노드들
        
        # 전체 메모리 네트워크 (LTM)
        self.memory_network = {}
        self.connections = {}
    
    def new_context(self, trigger: str):
        """새로운 컨텍스트 시작 (장소 이동, 주제 변경)"""
        
        # 새 컨텍스트 허브 생성
        context_id = generate_id()
        self.active_context = {
            'id': context_id,
            'trigger': trigger,
            'time': now(),
            'active_nodes': set()
        }
        
        # 이전 컨텍스트와 약한 연결
        if self.previous_context:
            self.connect(context_id, self.previous_context['id'], 
                        weight=0.3, type='temporal')
    
    def encode_memory(self, content: str):
        """현재 활성 컨텍스트에 메모리 기록"""
        
        memory_id = generate_id()
        
        # 1. 현재 컨텍스트에 강하게 연결
        self.connect(memory_id, self.active_context['id'], 
                    weight=0.9, type='context')
        
        # 2. 현재 활성화된 다른 노드들과도 연결
        for active_node in self.context_nodes:
            if self.is_related(content, active_node):
                self.connect(memory_id, active_node, 
                           weight=0.5, type='associative')
        
        # 3. Spreading Activation
        self.spread_activation(memory_id)
        
        return memory_id
    
    def recall(self, cue: str):
        """연상 기반 회상"""
        
        # 1. Cue와 관련된 노드 찾기
        activated = self.find_related_nodes(cue)
        
        # 2. Spreading Activation
        for node in activated:
            self.spread_activation(node)
        
        # 3. 컨텍스트도 함께 활성화
        # "그때 그 장소에서..." 효과
        contexts = self.get_node_contexts(activated)
        for context in contexts:
            self.activate_context(context)
        
        return self.get_highly_activated()
```

---

## 🔬 **Bias 문제와 해결**

### 연구에서 확인된 Bias

> "Intrusion errors... the word cookie is semantically related to chocolate. When chocolate was processed, it may have activated cookie via spreading activation"

**문제**: 관련 없는 것도 연상으로 끼어듦

### 의도적 Bias 활용

```python
class BiasAwareMemory:
    def __init__(self):
        self.recency_bias = 0.7  # 최근 기억 선호
        self.frequency_bias = 0.5  # 자주 접근한 기억 선호
        self.emotion_bias = 0.8  # 감정적 기억 선호
    
    def weighted_recall(self, cue: str):
        """편향을 고려한 회상"""
        
        candidates = self.find_candidates(cue)
        
        for memory in candidates:
            # 기본 관련성
            score = memory.relevance
            
            # Recency bias (최근일수록 강화)
            age = now() - memory.timestamp
            score *= (1 + self.recency_bias * exp(-age))
            
            # Frequency bias (자주 접근할수록 강화)
            score *= (1 + self.frequency_bias * memory.access_count)
            
            # Context bias (같은 맥락일수록 강화)
            if memory.context == self.active_context:
                score *= 2.0
            
            memory.final_score = score
        
        return sorted(candidates, key=lambda m: m.final_score)
```

---

## 🚀 **실제 구현 제안**

### 1. 단순하지만 맥락 있는 구조

```python
@dataclass
class ContextualMemory:
    # 최소 필드
    memory_id: str
    content: str
    context_id: str  # 어느 컨텍스트에서 생성됐나
    timestamp: float
    
    # 동적 필드
    activation: float = 0.0
    access_count: int = 0

class MemorySystem:
    def __init__(self):
        # 활성 컨텍스트 (STM 역할)
        self.active_context = None
        self.activation_buffer = {}  # 현재 활성화된 노드들
        
        # 메모리 저장소 (LTM)
        self.memories = {}
        self.contexts = {}
        self.edges = {}  # (from, to) -> weight
    
    def process_input(self, text: str):
        """새 입력 처리"""
        
        # 1. 컨텍스트 전환 감지
        if self.should_switch_context(text):
            self.create_new_context(text)
        
        # 2. 현재 컨텍스트에 메모리 추가
        mem = ContextualMemory(
            memory_id=generate_id(),
            content=text,
            context_id=self.active_context,
            timestamp=now()
        )
        
        # 3. 자동 연결 (현재 활성화된 것들과)
        for active_id in self.activation_buffer:
            if self.activation_buffer[active_id] > 0.3:
                weight = self.compute_relevance(text, self.memories[active_id].content)
                self.edges[(mem.memory_id, active_id)] = weight
        
        # 4. 활성화 전파
        self.spread_activation(mem.memory_id)
        
        return mem
```

### 2. AI 활용하되 구조는 유지

```python
def compute_relevance(self, text1: str, text2: str) -> float:
    """AI가 관련성 판단, 구조는 우리가 관리"""
    
    # MCP를 통해 Claude/GPT에게
    relevance = ai.evaluate_relevance(text1, text2)
    
    # 하지만 구조적 요인도 고려
    if same_context:
        relevance *= 1.5
    if temporal_proximity:
        relevance *= 1.2
    
    return min(1.0, relevance)
```

---

## 📊 **냉정한 평가**

### ✅ **이 방향의 장점** (80%)

1. **연구 기반**: 실제 뇌 작동 방식과 유사
2. **Context 중심**: 맥락이 자연스럽게 형성
3. **Bias 활용**: 단점이 아닌 특징으로
4. **STM/LTM 통합**: 분리가 아닌 협력

### ⚠️ **주의사항** (20%)

1. **컨텍스트 전환 감지**: AI 도움 필요
2. **연결 폭발 방지**: 임계값 관리 중요
3. **성능**: 활성화 전파 깊이 제한

---

## 🎯 **결론**

**당신의 직관이 맞았습니다:**

- ✅ 현재 활성 위치 기반 기록
- ✅ 연상 작용 (Spreading Activation)
- ✅ 맥락 의존적 메모리
- ✅ STM/LTM 개념

**문제는 구현이 엉성했을 뿐**

**해결책:**
1. Context를 명시적 허브로
2. 현재 활성화된 것들과 자동 연결
3. Bias를 버그가 아닌 feature로
4. AI는 관련성 판단에만 사용

**이렇게 하면 진짜 인간같은 메모리 시스템이 됩니다.**