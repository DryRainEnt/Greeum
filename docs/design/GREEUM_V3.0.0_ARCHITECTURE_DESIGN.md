# Greeum v3.0.0 Architecture Design
## 연상 기반 지능형 메모리 시스템

---

## 🏗️ **시스템 아키텍처**

### 핵심 설계 원칙
1. **연상 우선**: 단순 매칭이 아닌 연상 네트워크
2. **LLM 협력**: 추론은 LLM이, 데이터는 Greeum이
3. **점진적 확장**: MVP부터 시작, 단계적 기능 추가
4. **v2 호환성**: 기존 시스템과 병행 운영 가능

---

## 📊 **데이터베이스 스키마**

### 1. Core Tables

```sql
-- 메모리 노드 (기본 단위)
CREATE TABLE memory_nodes (
    node_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content TEXT NOT NULL,
    
    -- 구조화된 정보 (선택적)
    subject TEXT,           -- 주체
    action TEXT,            -- 행동
    object TEXT,            -- 객체
    
    -- 메타데이터
    importance REAL DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    
    -- 다차원 인덱스
    temporal_index INTEGER,  -- 시간축 위치
    emotional_tone REAL,     -- -1(부정) ~ 1(긍정)
    context_hash TEXT,       -- 맥락 식별자
    
    INDEX idx_temporal (temporal_index),
    INDEX idx_subject (subject),
    INDEX idx_context (context_hash)
);

-- 연상 연결 (가중치 그래프)
CREATE TABLE associations (
    assoc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_node INTEGER NOT NULL,
    target_node INTEGER NOT NULL,
    
    -- 연결 타입과 강도
    assoc_type TEXT NOT NULL,  -- semantic, temporal, causal, subject, object
    strength REAL DEFAULT 0.5,  -- 0.0 ~ 1.0
    
    -- 활성화 정보
    activation_count INTEGER DEFAULT 0,
    last_activated TIMESTAMP,
    
    -- 학습 정보
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,  -- user, system, learned
    
    FOREIGN KEY (source_node) REFERENCES memory_nodes(node_id),
    FOREIGN KEY (target_node) REFERENCES memory_nodes(node_id),
    UNIQUE(source_node, target_node, assoc_type),
    INDEX idx_source (source_node),
    INDEX idx_target (target_node),
    INDEX idx_strength (strength DESC)
);

-- 활성화 이력 (세션별 활성화 패턴)
CREATE TABLE activation_history (
    activation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    node_id INTEGER NOT NULL,
    activation_level REAL NOT NULL,  -- 0.0 ~ 1.0
    activation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trigger_node INTEGER,  -- 활성화를 유발한 노드
    
    FOREIGN KEY (node_id) REFERENCES memory_nodes(node_id),
    INDEX idx_session (session_id),
    INDEX idx_time (activation_time DESC)
);

-- 맥락 세션 (대화/작업 단위)
CREATE TABLE context_sessions (
    session_id TEXT PRIMARY KEY,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    
    -- 세션 메타데이터
    session_type TEXT,  -- conversation, task, exploration
    primary_topics TEXT,  -- JSON array of main topics
    total_activations INTEGER DEFAULT 0,
    
    -- 세션 상태
    active_nodes TEXT,  -- JSON array of currently active node IDs
    context_vector TEXT  -- JSON array of context weights
);
```

### 2. Indexing Tables

```sql
-- 키워드 인덱스 (빠른 초기 검색)
CREATE TABLE keyword_index (
    keyword TEXT NOT NULL,
    node_id INTEGER NOT NULL,
    frequency INTEGER DEFAULT 1,
    
    PRIMARY KEY (keyword, node_id),
    FOREIGN KEY (node_id) REFERENCES memory_nodes(node_id)
);

-- 시간 윈도우 인덱스 (시간 기반 검색)
CREATE TABLE temporal_windows (
    window_id INTEGER PRIMARY KEY,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    node_count INTEGER DEFAULT 0,
    summary TEXT,
    
    INDEX idx_time_range (start_time, end_time)
);

-- 클러스터 인덱스 (주제별 그룹)
CREATE TABLE memory_clusters (
    cluster_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_name TEXT,
    centroid_node INTEGER,
    member_count INTEGER DEFAULT 0,
    
    FOREIGN KEY (centroid_node) REFERENCES memory_nodes(node_id)
);

CREATE TABLE cluster_members (
    cluster_id INTEGER NOT NULL,
    node_id INTEGER NOT NULL,
    distance_to_centroid REAL,
    
    PRIMARY KEY (cluster_id, node_id),
    FOREIGN KEY (cluster_id) REFERENCES memory_clusters(cluster_id),
    FOREIGN KEY (node_id) REFERENCES memory_nodes(node_id)
);
```

---

## 🧠 **핵심 컴포넌트 설계**

### 1. AssociationNetwork (연상 네트워크)

```python
class AssociationNetwork:
    """
    메모리 노드 간 연상 관계를 관리하는 핵심 엔진
    """
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.cache = AssociationCache()  # 자주 사용되는 연결 캐싱
        
    def create_association(self, source_id: int, target_id: int, 
                         assoc_type: str, strength: float = 0.5):
        """두 노드 간 연상 연결 생성"""
        # 중복 체크
        if self.has_association(source_id, target_id, assoc_type):
            return self.strengthen_association(source_id, target_id, strength * 0.1)
        
        # 새 연결 생성
        self.db.execute("""
            INSERT INTO associations (source_node, target_node, assoc_type, strength)
            VALUES (?, ?, ?, ?)
        """, (source_id, target_id, assoc_type, strength))
        
        # 캐시 무효화
        self.cache.invalidate(source_id)
        
    def find_associations(self, node_id: int, max_depth: int = 2) -> Dict:
        """
        특정 노드에서 시작하는 연상 네트워크 탐색
        BFS 방식으로 depth만큼 확장
        """
        visited = set()
        network = {
            "center": node_id,
            "layers": []
        }
        
        current_layer = [node_id]
        
        for depth in range(max_depth):
            next_layer = []
            layer_associations = []
            
            for current_node in current_layer:
                if current_node in visited:
                    continue
                    
                visited.add(current_node)
                
                # 현재 노드의 모든 연결 조회
                associations = self.db.query("""
                    SELECT target_node, assoc_type, strength
                    FROM associations
                    WHERE source_node = ?
                    ORDER BY strength DESC
                    LIMIT 10
                """, (current_node,))
                
                for assoc in associations:
                    if assoc['target_node'] not in visited:
                        next_layer.append(assoc['target_node'])
                        layer_associations.append({
                            "from": current_node,
                            "to": assoc['target_node'],
                            "type": assoc['assoc_type'],
                            "strength": assoc['strength']
                        })
            
            if layer_associations:
                network["layers"].append({
                    "depth": depth + 1,
                    "associations": layer_associations
                })
            
            current_layer = next_layer
            
        return network
    
    def strengthen_association(self, source_id: int, target_id: int, delta: float):
        """연결 강도 증가 (사용할수록 강해짐)"""
        self.db.execute("""
            UPDATE associations 
            SET strength = MIN(1.0, strength + ?),
                activation_count = activation_count + 1,
                last_activated = CURRENT_TIMESTAMP
            WHERE source_node = ? AND target_node = ?
        """, (delta, source_id, target_id))
    
    def decay_associations(self, decay_rate: float = 0.95):
        """시간에 따른 연결 강도 감쇠 (미사용 연결 약화)"""
        self.db.execute("""
            UPDATE associations
            SET strength = strength * ?
            WHERE last_activated < datetime('now', '-7 days')
        """, (decay_rate,))
```

### 2. SpreadingActivation (활성화 확산)

```python
class SpreadingActivation:
    """
    하나의 기억이 활성화되면 연관된 기억들도 함께 활성화
    인간의 연상 작용을 모방
    """
    
    def __init__(self, network: AssociationNetwork):
        self.network = network
        self.activation_threshold = 0.3  # 최소 활성화 수준
        self.decay_factor = 0.7  # 거리에 따른 감쇠
        
    def activate(self, trigger_nodes: List[int], session_id: str) -> Dict[int, float]:
        """
        트리거 노드들로부터 활성화 확산
        
        Returns:
            {node_id: activation_level} 형태의 활성화 맵
        """
        activation_map = {}
        
        # 초기 활성화 (트리거 노드들은 1.0)
        for node in trigger_nodes:
            activation_map[node] = 1.0
            self._record_activation(session_id, node, 1.0, None)
        
        # 3단계까지 확산
        for depth in range(1, 4):
            new_activations = {}
            decay = self.decay_factor ** depth
            
            for active_node, activation_level in activation_map.items():
                if activation_level < self.activation_threshold:
                    continue
                
                # 연결된 노드들 활성화
                associations = self.network.find_associations(active_node, max_depth=1)
                
                for layer in associations.get("layers", []):
                    for assoc in layer["associations"]:
                        target = assoc["to"]
                        
                        # 연결 강도와 거리를 고려한 활성화 수준 계산
                        propagated_activation = activation_level * assoc["strength"] * decay
                        
                        if target not in activation_map:
                            new_activations[target] = propagated_activation
                        else:
                            # 여러 경로로 활성화되면 최대값 사용
                            new_activations[target] = max(
                                new_activations.get(target, 0),
                                propagated_activation
                            )
            
            # 새로 활성화된 노드들 기록
            for node, level in new_activations.items():
                if level >= self.activation_threshold:
                    activation_map[node] = level
                    self._record_activation(session_id, node, level, active_node)
        
        return activation_map
    
    def _record_activation(self, session_id: str, node_id: int, 
                          level: float, trigger: Optional[int]):
        """활성화 이력 기록"""
        self.network.db.execute("""
            INSERT INTO activation_history 
            (session_id, node_id, activation_level, trigger_node)
            VALUES (?, ?, ?, ?)
        """, (session_id, node_id, level, trigger))
```

### 3. ContextManager (맥락 관리자)

```python
class ContextManager:
    """
    대화/작업의 맥락을 추적하고 관련 기억을 지속적으로 제공
    """
    
    def __init__(self, network: AssociationNetwork, activation: SpreadingActivation):
        self.network = network
        self.activation = activation
        self.active_context = {}
        
    def start_session(self, session_type: str = "conversation") -> str:
        """새 맥락 세션 시작"""
        session_id = self._generate_session_id()
        
        self.network.db.execute("""
            INSERT INTO context_sessions (session_id, session_type)
            VALUES (?, ?)
        """, (session_id, session_type))
        
        self.active_context[session_id] = {
            "active_nodes": [],
            "context_vector": {},
            "turn_count": 0
        }
        
        return session_id
    
    def update_context(self, session_id: str, new_input: str) -> Dict:
        """
        새 입력에 따라 맥락 업데이트 및 관련 기억 반환
        """
        context = self.active_context.get(session_id, {})
        
        # 1. 새 입력에서 관련 노드 검색
        relevant_nodes = self._find_relevant_nodes(new_input)
        
        # 2. 활성화 확산으로 연관 기억 찾기
        activation_map = self.activation.activate(relevant_nodes, session_id)
        
        # 3. 기존 활성 노드 감쇠
        for node in context.get("active_nodes", []):
            if node not in activation_map:
                activation_map[node] = context["context_vector"].get(node, 0) * 0.7
        
        # 4. 맥락 업데이트
        context["active_nodes"] = list(activation_map.keys())
        context["context_vector"] = activation_map
        context["turn_count"] += 1
        
        # 5. 상위 N개 활성화된 기억 반환
        top_memories = self._get_top_memories(activation_map, limit=20)
        
        return {
            "direct_matches": relevant_nodes,
            "associated_memories": top_memories,
            "context_strength": self._calculate_context_coherence(activation_map)
        }
    
    def _find_relevant_nodes(self, text: str) -> List[int]:
        """텍스트와 관련된 초기 노드들 검색"""
        # 키워드 추출
        keywords = self._extract_keywords(text)
        
        # 키워드 기반 노드 검색
        nodes = []
        for keyword in keywords:
            results = self.network.db.query("""
                SELECT DISTINCT node_id 
                FROM keyword_index
                WHERE keyword = ?
                LIMIT 5
            """, (keyword,))
            nodes.extend([r['node_id'] for r in results])
        
        return list(set(nodes))
    
    def _get_top_memories(self, activation_map: Dict[int, float], 
                         limit: int = 20) -> List[Dict]:
        """활성화 수준이 높은 상위 N개 기억 조회"""
        sorted_nodes = sorted(
            activation_map.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:limit]
        
        memories = []
        for node_id, activation_level in sorted_nodes:
            memory = self.network.db.query_one("""
                SELECT content, subject, action, object, emotional_tone
                FROM memory_nodes
                WHERE node_id = ?
            """, (node_id,))
            
            if memory:
                memories.append({
                    "node_id": node_id,
                    "activation": activation_level,
                    "content": memory['content'],
                    "structure": {
                        "subject": memory['subject'],
                        "action": memory['action'],
                        "object": memory['object']
                    },
                    "emotion": memory['emotional_tone']
                })
        
        return memories
```

### 4. MemoryIndexer (다차원 인덱싱)

```python
class MemoryIndexer:
    """
    메모리를 다양한 차원으로 인덱싱하여 빠른 접근 가능
    """
    
    def __init__(self, db_manager):
        self.db = db_manager
        
    def index_memory(self, node_id: int, content: str, metadata: Dict):
        """새 메모리 노드 인덱싱"""
        
        # 1. 키워드 인덱싱
        keywords = self._extract_keywords(content)
        for keyword in keywords:
            self.db.execute("""
                INSERT OR REPLACE INTO keyword_index (keyword, node_id, frequency)
                VALUES (?, ?, COALESCE(
                    (SELECT frequency + 1 FROM keyword_index 
                     WHERE keyword = ? AND node_id = ?), 1))
            """, (keyword, node_id, keyword, node_id))
        
        # 2. 시간 윈도우 할당
        timestamp = metadata.get('timestamp', datetime.now())
        window_id = self._get_or_create_time_window(timestamp)
        
        # 3. 감정 인덱싱
        emotional_tone = self._analyze_emotion(content)
        
        # 4. 구조적 요소 추출
        structure = self._extract_structure(content)
        
        # 노드 메타데이터 업데이트
        self.db.execute("""
            UPDATE memory_nodes
            SET temporal_index = ?,
                emotional_tone = ?,
                subject = ?,
                action = ?,
                object = ?
            WHERE node_id = ?
        """, (window_id, emotional_tone, 
              structure.get('subject'),
              structure.get('action'),
              structure.get('object'),
              node_id))
    
    def search_by_dimension(self, dimension: str, value: Any, limit: int = 10):
        """특정 차원으로 메모리 검색"""
        
        if dimension == "temporal":
            # 시간 기반 검색
            return self.db.query("""
                SELECT * FROM memory_nodes
                WHERE temporal_index = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (value, limit))
            
        elif dimension == "emotional":
            # 감정 기반 검색
            return self.db.query("""
                SELECT * FROM memory_nodes
                WHERE ABS(emotional_tone - ?) < 0.2
                ORDER BY ABS(emotional_tone - ?)
                LIMIT ?
            """, (value, value, limit))
            
        elif dimension == "subject":
            # 주체 기반 검색
            return self.db.query("""
                SELECT * FROM memory_nodes
                WHERE subject = ?
                ORDER BY importance DESC
                LIMIT ?
            """, (value, limit))
```

---

## 🔄 **통합 작동 플로우**

```python
class GreeumV3:
    """
    v3.0.0 메인 인터페이스
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.network = AssociationNetwork(self.db)
        self.activation = SpreadingActivation(self.network)
        self.context = ContextManager(self.network, self.activation)
        self.indexer = MemoryIndexer(self.db)
        
    def add_memory(self, content: str, metadata: Dict = None) -> int:
        """새 메모리 추가"""
        
        # 1. 노드 생성
        node_id = self.db.execute("""
            INSERT INTO memory_nodes (content, importance)
            VALUES (?, ?)
        """, (content, metadata.get('importance', 0.5)))
        
        # 2. 인덱싱
        self.indexer.index_memory(node_id, content, metadata or {})
        
        # 3. 자동 연상 연결 생성
        self._create_automatic_associations(node_id, content)
        
        return node_id
    
    def recall(self, query: str, session_id: str = None) -> Dict:
        """연상 기반 기억 회상"""
        
        # 세션 관리
        if not session_id:
            session_id = self.context.start_session()
        
        # 맥락 업데이트 및 연상 활성화
        result = self.context.update_context(session_id, query)
        
        return {
            "session_id": session_id,
            "memories": result["associated_memories"],
            "context_coherence": result["context_strength"],
            "association_map": self._visualize_associations(result)
        }
    
    def _create_automatic_associations(self, node_id: int, content: str):
        """새 메모리에 대한 자동 연상 연결 생성"""
        
        # 유사한 메모리 찾기
        similar = self._find_similar_memories(content, limit=5)
        
        for similar_node, similarity in similar:
            if similarity > 0.7:
                self.network.create_association(
                    node_id, similar_node,
                    "semantic", similarity
                )
        
        # 시간적으로 가까운 메모리 연결
        recent = self.db.query("""
            SELECT node_id FROM memory_nodes
            WHERE node_id != ?
            ORDER BY created_at DESC
            LIMIT 3
        """, (node_id,))
        
        for r in recent:
            self.network.create_association(
                node_id, r['node_id'],
                "temporal", 0.5
            )
```

---

## 📈 **성능 최적화 전략**

### 1. 캐싱
- 자주 활성화되는 연상 경로 캐싱
- 세션별 활성 노드 메모리 캐시
- 키워드-노드 매핑 캐시

### 2. 인덱싱
- 복합 인덱스로 다차원 검색 최적화
- 부분 인덱스로 메모리 효율성
- 정기적 인덱스 재구성

### 3. 배치 처리
- 연상 연결 배치 생성
- 활성화 이력 배치 기록
- 감쇠 연산 배치 실행

---

## 🎯 **구현 우선순위**

1. **Week 1-2**: 기본 스키마 및 노드 관리
2. **Week 3-4**: AssociationNetwork 구현
3. **Week 5-6**: SpreadingActivation 알고리즘
4. **Week 7-8**: ContextManager 및 통합
5. **Week 9-10**: 성능 최적화 및 테스트

---

## 📊 **예상 메트릭**

| 지표 | 목표 | 측정 방법 |
|------|------|-----------|
| 연상 정확도 | 70% | 관련 기억 비율 |
| 활성화 속도 | <100ms | 3단계 확산 시간 |
| 맥락 유지 | 10턴 | 대화 일관성 |
| 메모리 활용률 | 40% | 세션당 활성화 비율 |

이 구조는 진정한 **연상 기반 지능형 메모리 시스템**의 기반이 됩니다.