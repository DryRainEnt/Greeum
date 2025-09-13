# Greeum v3.0.0: Neural Memory Network
## 진짜 단순한 신경망 메모리 시스템

---

## 🧠 **핵심 아이디어**

**"메모리는 노드, 관계는 엣지, 활성화는 전파"**

구조화하지 말고, 연결하자.

---

## 📐 **극단적으로 단순한 설계**

### 1. **메모리 노드 (Memory Node)**

```python
@dataclass
class MemoryNode:
    """가장 단순한 메모리 단위"""
    
    node_id: str          # 고유 ID
    content: str          # 원본 텍스트 그대로
    timestamp: datetime   # 언제
    activation: float = 0.0  # 현재 활성화 수준
    
    # 그게 다임. 진짜로.
```

### 2. **연결 (Connection)**

```python
@dataclass  
class Connection:
    """메모리 간 연결"""
    
    from_node: str      # 출발 노드
    to_node: str        # 도착 노드
    weight: float       # 연결 강도 (-1 ~ 1)
    created_by: str     # 'temporal', 'semantic', 'causal', 'user'
    
    # 역시 그게 다임.
```

### 3. **신경망 작동 원리**

```python
class NeuralMemory:
    """신경망처럼 작동하는 메모리"""
    
    def activate(self, text: str):
        """새 입력이 들어오면"""
        
        # 1. 새 노드 생성
        new_node = MemoryNode(
            node_id=generate_id(),
            content=text,
            timestamp=now(),
            activation=1.0  # 새 메모리는 최대 활성화
        )
        
        # 2. 기존 노드들과 연결 생성
        for existing in self.nodes:
            similarity = self.ai_compute_similarity(text, existing.content)
            if similarity > 0.3:  # 임계값
                self.connect(new_node, existing, weight=similarity)
        
        # 3. 활성화 전파 (Spreading Activation)
        self.propagate_activation(new_node)
        
        return new_node
    
    def propagate_activation(self, source_node, depth=3):
        """활성화가 네트워크를 따라 퍼짐"""
        
        current_layer = [source_node]
        
        for _ in range(depth):
            next_layer = []
            for node in current_layer:
                # 연결된 노드들에게 활성화 전달
                for conn in self.get_connections(node):
                    target = self.get_node(conn.to_node)
                    # 활성화 전달 (가중치 곱하고 감쇠)
                    target.activation += node.activation * conn.weight * 0.5
                    next_layer.append(target)
            current_layer = next_layer
    
    def recall(self, query: str, top_k=5):
        """기억 회상"""
        
        # 1. 쿼리를 임시 노드로
        query_node = MemoryNode("temp", query, now(), 1.0)
        
        # 2. 활성화 전파
        self.propagate_activation(query_node)
        
        # 3. 가장 활성화된 노드들 반환
        return sorted(self.nodes, key=lambda n: n.activation, reverse=True)[:top_k]
```

---

## 🔄 **인과관계는 어떻게?**

### 시간적 인접성 (Temporal Proximity)

```python
def detect_temporal_causality(self, time_window=3600):  # 1시간
    """시간적으로 가까운 메모리들을 연결"""
    
    for i, node1 in enumerate(self.nodes):
        for node2 in self.nodes[i+1:]:
            time_diff = abs(node2.timestamp - node1.timestamp)
            
            if time_diff < time_window:
                # 시간적으로 가까우면 약한 인과관계 가능성
                weight = 1.0 - (time_diff / time_window)  # 가까울수록 강함
                self.connect(node1, node2, weight * 0.3, 'temporal')
```

### 의미적 연결 (Semantic Chaining)

```python
def detect_semantic_causality(self):
    """AI가 의미적 연결 발견"""
    
    for node1 in self.nodes:
        for node2 in self.nodes:
            # AI에게 물어봄: 이 둘이 인과관계인가?
            prompt = f"""
            A: {node1.content}
            B: {node2.content}
            
            A가 B의 원인일 가능성은? (0-1)
            """
            
            causality_score = self.ai_evaluate(prompt)
            
            if causality_score > 0.5:
                self.connect(node1, node2, causality_score, 'causal')
```

### 패턴 학습 (Pattern Learning)

```python
def learn_patterns(self):
    """반복되는 패턴을 찾아 연결 강화"""
    
    # 자주 함께 활성화되는 노드들
    co_activation_counts = {}
    
    for session in self.activation_history:
        activated_nodes = session.get_activated_nodes()
        for n1, n2 in combinations(activated_nodes, 2):
            pair = tuple(sorted([n1.id, n2.id]))
            co_activation_counts[pair] = co_activation_counts.get(pair, 0) + 1
    
    # 자주 함께 활성화되면 연결 강화
    for (n1_id, n2_id), count in co_activation_counts.items():
        if count > 3:  # 3번 이상 함께 활성화
            self.strengthen_connection(n1_id, n2_id, delta=0.1)
```

---

## 💡 **장점**

### 1. **진짜 단순함**
- 노드 = 텍스트 + 시간 + 활성화
- 연결 = 출발 + 도착 + 가중치
- 끝

### 2. **자연스러운 작동**
- 새 메모리 → 자동으로 관련 메모리와 연결
- 회상 → 활성화가 퍼지며 관련 기억 함께 떠오름
- 학습 → 자주 쓰는 연결은 강해짐

### 3. **창발적 지능**
- 구조를 강요하지 않음
- 패턴이 자연스럽게 나타남
- AI가 필요할 때만 개입

---

## 🗄️ **최소 DB 스키마**

```sql
-- 노드 테이블
CREATE TABLE nodes (
    node_id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    timestamp REAL NOT NULL,
    activation REAL DEFAULT 0.0
);

-- 연결 테이블  
CREATE TABLE connections (
    from_node TEXT,
    to_node TEXT,
    weight REAL DEFAULT 0.5,
    created_by TEXT,
    PRIMARY KEY (from_node, to_node)
);

-- 끝. 진짜 이게 다.
```

---

## 🚀 **구현 예시**

```python
# 사용 예시
memory = NeuralMemory()

# 메모리 추가 (자동으로 연결됨)
memory.activate("버그를 발견했다")
memory.activate("버그를 수정했다")  # 자동으로 이전 메모리와 연결
memory.activate("테스트 통과했다")  # 역시 연결

# 회상
results = memory.recall("버그 관련해서 뭐 했었지?")
# → 활성화가 퍼져서 관련 메모리들이 모두 떠오름

# 인과관계 추론
chain = memory.trace_causal_chain("테스트 통과")
# → "버그 발견" → "버그 수정" → "테스트 통과"
```

---

## 🎯 **핵심 차이점**

### 기존 접근 (Engram)
- 18개 필드 강제
- 구조화 집착
- AI가 억지로 채움

### 새 접근 (Neural Memory)
- 2개 필드만 (텍스트, 시간)
- 연결이 구조를 대체
- 패턴이 자연스럽게 창발

---

## 💭 **철학**

**"메모리는 구조가 아니라 네트워크다"**

- 인간 뇌도 노드와 시냅스
- 구조는 없고 연결만 있음
- 의미는 활성화 패턴에서 나옴

---

## ✅ **이게 진짜 v3.0.0**

1. **계층구조** ✓ 
   - 활성화 레벨이 자연스런 계층 형성
   - 중요한 노드는 많이 연결됨

2. **신경망** ✓
   - Spreading Activation
   - Weight 기반 연결
   - 학습을 통한 강화

3. **인과관계** ✓
   - 시간적 인접성
   - 의미적 연결
   - 패턴 학습

4. **단순함** ✓
   - 노드 2개 필드
   - 연결 3개 필드
   - 그게 전부

**복잡한 행동은 단순한 규칙의 상호작용에서 나온다**