# Greeum v3.0.0: 실전 구현 계획
## 기존 코드를 최대한 활용한 Context-Dependent Memory

---

## 🎯 **핵심 전략**

**"v2.6.4의 좋은 부분은 살리고, 부족한 부분만 추가"**

### 재사용 가능한 것들:
- ✅ BlockManager (LTM 저장소로)
- ✅ STMManager (Active Context로 진화)
- ✅ DatabaseManager (스키마만 확장)
- ✅ SearchEngine (여전히 유용)

### 새로 만들 것들:
- 🆕 ContextHub (활성 맥락 관리)
- 🆕 AutoConnector (자동 연결 생성)
- 🆕 ActivationEngine (Spreading Activation)

---

## 🔧 **구체적 수정 방안**

### 1. STMManager → ActiveContextManager

```python
# greeum/core/active_context.py

from greeum.stm_manager import STMManager

class ActiveContextManager(STMManager):
    """STMManager를 확장해서 Active Context로"""
    
    def __init__(self, db_manager):
        super().__init__(db_manager)
        
        # 추가 필드
        self.current_context_id = None
        self.context_trigger = None  # 무엇이 이 컨텍스트를 시작했나
        self.active_nodes = {}  # {node_id: activation_level}
        self.context_start_time = None
    
    def switch_context(self, trigger: str):
        """컨텍스트 전환 (기존 flush_to_ltm 활용)"""
        
        # 기존 컨텍스트 저장
        if self.current_context_id:
            self.save_context_to_ltm()
        
        # 새 컨텍스트 시작
        self.current_context_id = f"ctx_{time.time()}"
        self.context_trigger = trigger
        self.context_start_time = time.time()
        self.active_nodes = {}
        
        logger.info(f"Context switched: {trigger}")
    
    def add_memory(self, content: str, **kwargs):
        """메모리 추가시 자동으로 현재 컨텍스트에 연결"""
        
        # 기존 STM 추가 로직
        memory_id = super().add_memory(content, **kwargs)
        
        # 현재 활성 노드들과 연결
        for active_id, activation in self.active_nodes.items():
            if activation > 0.3:  # 임계값
                # 연결 생성 (새 테이블에)
                self._create_connection(memory_id, active_id, activation * 0.5)
        
        # 이 메모리도 활성화
        self.active_nodes[memory_id] = 1.0
        
        return memory_id
```

### 2. 데이터베이스 스키마 확장 (호환성 유지)

```python
# greeum/core/database_manager.py 에 추가

def _create_v3_context_tables(self):
    """v3 테이블 추가 (기존 테이블은 그대로)"""
    
    cursor = self.conn.cursor()
    
    # 컨텍스트 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contexts (
            context_id TEXT PRIMARY KEY,
            trigger TEXT,
            start_time REAL,
            end_time REAL,
            memory_count INTEGER DEFAULT 0,
            metadata TEXT
        )
    ''')
    
    # 메모리 연결 테이블 (네트워크 구조)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory_connections (
            from_memory INTEGER,
            to_memory INTEGER,
            weight REAL DEFAULT 0.5,
            connection_type TEXT,  -- 'context', 'semantic', 'temporal'
            created_at REAL,
            context_id TEXT,
            PRIMARY KEY (from_memory, to_memory),
            FOREIGN KEY (from_memory) REFERENCES blocks(block_index),
            FOREIGN KEY (to_memory) REFERENCES blocks(block_index),
            FOREIGN KEY (context_id) REFERENCES contexts(context_id)
        )
    ''')
    
    # 활성화 로그 (학습용)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activation_log (
            memory_id INTEGER,
            activation_level REAL,
            context_id TEXT,
            timestamp REAL,
            trigger_memory INTEGER
        )
    ''')
    
    # 인덱스
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_connections_context ON memory_connections(context_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_connections_weight ON memory_connections(weight)')
```

### 3. Spreading Activation 구현

```python
# greeum/core/activation_engine.py

class ActivationEngine:
    """간단한 Spreading Activation"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.decay_rate = 0.5
        self.threshold = 0.1
    
    def activate(self, source_memory_id: int, depth: int = 3):
        """메모리 활성화 전파"""
        
        activations = {source_memory_id: 1.0}
        current_layer = [source_memory_id]
        
        for d in range(depth):
            next_layer = []
            
            for memory_id in current_layer:
                # 연결된 메모리 찾기
                connections = self.db.get_connections(memory_id)
                
                for conn in connections:
                    target_id = conn['to_memory']
                    spread = activations[memory_id] * conn['weight'] * self.decay_rate
                    
                    if spread > self.threshold:
                        if target_id not in activations:
                            activations[target_id] = 0
                        activations[target_id] += spread
                        next_layer.append(target_id)
            
            current_layer = next_layer
            if not current_layer:
                break
        
        return activations
```

### 4. 하이브리드 검색 (기존 + 네트워크)

```python
# greeum/search_engine.py 수정

class EnhancedSearchEngine(SearchEngine):
    """기존 검색 + 네트워크 기반 연상"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.activation_engine = ActivationEngine(self.db_manager)
    
    def search_with_context(self, query: str, use_activation: bool = True):
        """컨텍스트 인식 검색"""
        
        # 1. 기존 검색 (키워드, 임베딩)
        base_results = self.search(query)
        
        if not use_activation:
            return base_results
        
        # 2. 활성화 전파
        all_activations = {}
        for result in base_results[:3]:  # 상위 3개만
            memory_id = result['block_index']
            activations = self.activation_engine.activate(memory_id)
            
            for mem_id, level in activations.items():
                if mem_id not in all_activations:
                    all_activations[mem_id] = 0
                all_activations[mem_id] += level
        
        # 3. 활성화된 메모리 추가
        activated_memories = []
        for mem_id, activation in all_activations.items():
            if activation > 0.2:  # 임계값
                memory = self.db_manager.get_block(mem_id)
                if memory:
                    memory['activation_score'] = activation
                    activated_memories.append(memory)
        
        # 4. 통합 결과
        return self._merge_results(base_results, activated_memories)
```

---

## 🔄 **마이그레이션 전략**

### Option 1: Lazy Migration (추천 ✅)

```python
class MigrationBridge:
    """사용하면서 점진적 마이그레이션"""
    
    def __init__(self):
        self.v2_db = DatabaseManager()  # 기존
        self.context_manager = ActiveContextManager(self.v2_db)
        self.processed = set()
    
    def get_memory(self, memory_id: int):
        """메모리 조회시 자동 연결 생성"""
        
        memory = self.v2_db.get_block(memory_id)
        
        if memory_id not in self.processed:
            # 첫 접근시 연결 생성
            self._create_connections_for(memory)
            self.processed.add(memory_id)
        
        return memory
    
    def _create_connections_for(self, memory):
        """과거 메모리에 대한 연결 추론"""
        
        # 시간적으로 가까운 메모리
        timestamp = memory['timestamp']
        nearby = self.v2_db.get_blocks_by_time_range(
            timestamp - 3600, 
            timestamp + 3600
        )
        
        for other in nearby:
            if other['block_index'] != memory['block_index']:
                # 간단한 연결 생성
                weight = 0.3 * (1 - abs(timestamp - other['timestamp']) / 3600)
                self.v2_db.create_connection(
                    memory['block_index'],
                    other['block_index'],
                    weight,
                    'temporal'
                )
```

### Option 2: 듀얼 모드 (안전 🛡️)

```python
class DualModeMemory:
    """v2.6.4와 v3.0 동시 운영"""
    
    def __init__(self):
        self.legacy_mode = BlockManager()  # v2.6.4
        self.context_mode = ContextMemory()  # v3.0
        self.mode = 'dual'  # 'legacy', 'context', 'dual'
    
    def add_memory(self, content: str):
        """두 시스템에 모두 저장"""
        
        if self.mode in ['legacy', 'dual']:
            self.legacy_mode.add_block(content)
        
        if self.mode in ['context', 'dual']:
            self.context_mode.add_memory(content)
    
    def search(self, query: str):
        """두 시스템 모두 검색"""
        
        results = []
        
        if self.mode in ['legacy', 'dual']:
            results.extend(self.legacy_mode.search(query))
        
        if self.mode in ['context', 'dual']:
            context_results = self.context_mode.search_with_activation(query)
            results.extend(context_results)
        
        return self._deduplicate(results)
```

---

## 📝 **구현 우선순위**

### Phase 1: 기반 작업 (1주)
1. ✅ 데이터베이스 스키마 확장
2. ✅ ActiveContextManager (STM 확장)
3. ✅ 연결 테이블 생성

### Phase 2: 핵심 기능 (1주)
1. ⬜ ActivationEngine 구현
2. ⬜ 자동 연결 생성
3. ⬜ 컨텍스트 전환 감지

### Phase 3: 통합 (1주)
1. ⬜ 하이브리드 검색
2. ⬜ Lazy Migration
3. ⬜ 성능 최적화

---

## 💡 **핵심 인사이트**

### 호환성 유지는 가능!

**이유:**
1. 기존 테이블 건드리지 않음
2. 새 테이블만 추가
3. 기존 API 그대로 유지
4. 점진적 마이그레이션

### 실용적 접근

```python
# 최소 변경으로 최대 효과
class MinimalChange:
    """정말 필요한 것만 추가"""
    
    def __init__(self):
        # 기존 그대로
        self.block_manager = BlockManager()
        self.stm_manager = STMManager()
        
        # 새로 추가
        self.connections = {}  # 메모리 연결
        self.active_context = None  # 현재 컨텍스트
    
    def add_memory_v3(self, content):
        """v3 방식 추가"""
        
        # 1. 기존 방식으로 저장
        block_id = self.block_manager.add_block(content)
        
        # 2. 현재 컨텍스트에 연결 (새 기능)
        if self.active_context:
            for active_id in self.active_context:
                self.connections[(block_id, active_id)] = 0.5
        
        # 3. 활성화 (새 기능)
        self.spread_activation(block_id)
        
        return block_id
```

---

## 🎯 **결론**

**호환성 유지하면서 v3.0 구현: 완전 가능**

1. **기존 코드 90% 재사용**
2. **새 기능만 추가**
3. **점진적 전환**
4. **리스크 최소화**

**핵심: 작게 시작해서 점진적 개선**

"Perfect is the enemy of good"