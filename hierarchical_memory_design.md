# 계층적 다중참조 메모리 구조 설계안

## 🎯 핵심 아이디어
단순 선형 해시체인을 벗어나 계층적 다중참조 구조로 확장하여 인간 기억의 연상과 맥락성을 더 잘 모방

## 🏗️ 제안된 데이터 스키마

### 1. 체크포인트/앵커 블록 확장
```sql
-- 기존 blocks 테이블에 계층 정보 추가
ALTER TABLE blocks ADD COLUMN tier INTEGER DEFAULT 0;  -- 0: 일반, 1: 체크포인트, 2: 앵커
ALTER TABLE blocks ADD COLUMN cluster_weight REAL DEFAULT 1.0;  -- 클러스터 중심 가중치

-- 새 테이블: 계층적 관계
CREATE TABLE block_hierarchies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_block_index INTEGER NOT NULL,    -- 상위 체크포인트/앵커
    child_block_index INTEGER NOT NULL,     -- 하위 일반 블록
    relationship_type TEXT NOT NULL,        -- 'cluster', 'reference', 'temporal'
    relationship_strength REAL DEFAULT 1.0, -- 관계 강도
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_block_index) REFERENCES blocks(block_index),
    FOREIGN KEY (child_block_index) REFERENCES blocks(block_index),
    UNIQUE(parent_block_index, child_block_index, relationship_type)
);

-- 새 테이블: 클러스터 정의
CREATE TABLE memory_clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_name TEXT NOT NULL,
    anchor_block_index INTEGER NOT NULL,    -- 클러스터 중심 블록
    keywords TEXT NOT NULL,                 -- JSON array
    context_vector BLOB,                    -- 임베딩 벡터
    member_count INTEGER DEFAULT 1,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (anchor_block_index) REFERENCES blocks(block_index)
);
```

### 2. 다중참조 관계 매핑
```sql
-- 새 테이블: 블록 간 다중 관계
CREATE TABLE block_cross_references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_block_index INTEGER NOT NULL,
    target_block_index INTEGER NOT NULL,
    reference_type TEXT NOT NULL,           -- 'semantic', 'temporal', 'keyword', 'causal'
    similarity_score REAL DEFAULT 0.0,
    bidirectional BOOLEAN DEFAULT TRUE,
    weight REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_block_index) REFERENCES blocks(block_index),
    FOREIGN KEY (target_block_index) REFERENCES blocks(block_index)
);
```

## 🧠 작동 원리

### 1. 계층적 메모리 생성 프로세스
```python
class HierarchicalMemoryManager:
    def add_memory(self, context: str, tier: int = 0) -> Dict:
        # 1. 기존 블록 생성
        block = self.block_manager.add_block(context)
        
        # 2. 클러스터 분석 및 할당
        relevant_clusters = self.find_relevant_clusters(context)
        
        # 3. 다중 클러스터 참조 생성
        for cluster in relevant_clusters:
            self.create_hierarchy_link(cluster.anchor_block, block.index, 
                                     relationship_type='semantic')
        
        # 4. 체크포인트 승격 검사
        if self.should_promote_to_checkpoint(block):
            self.promote_to_checkpoint(block)
            
        return block

    def find_relevant_clusters(self, context: str) -> List[Cluster]:
        """맥락 기반으로 관련 클러스터들 찾기"""
        embedding = self.embed(context)
        keywords = self.extract_keywords(context)
        
        # 의미적 유사도 + 키워드 매칭
        semantic_clusters = self.cluster_manager.find_by_embedding(embedding)
        keyword_clusters = self.cluster_manager.find_by_keywords(keywords)
        
        # 다중 클러스터 반환 (하나의 기억이 여러 맥락에 속함)
        return list(set(semantic_clusters + keyword_clusters))
```

### 2. 계층적 검색 알고리즘
```python
def hierarchical_search(self, query: str, max_depth: int = 3) -> List[Dict]:
    """계층 우선 탐색으로 관련 기억 검색"""
    
    # 1. 관련 클러스터/체크포인트 찾기
    anchor_candidates = self.find_anchor_blocks(query)
    
    results = []
    for anchor in anchor_candidates:
        # 2. 각 앵커에서 BFS로 탐색
        cluster_results = self.bfs_from_anchor(anchor, query, max_depth)
        results.extend(cluster_results)
    
    # 3. 클러스터 간 중복 제거 및 랭킹
    return self.deduplicate_and_rank(results)

def bfs_from_anchor(self, anchor_block: Dict, query: str, max_depth: int) -> List[Dict]:
    """앵커 블록에서 시작하여 계층적 BFS 탐색"""
    queue = [(anchor_block, 0)]  # (block, depth)
    visited = set()
    results = []
    
    while queue:
        current_block, depth = queue.pop(0)
        
        if current_block['block_index'] in visited or depth > max_depth:
            continue
            
        visited.add(current_block['block_index'])
        
        # 쿼리 관련성 검사
        if self.is_relevant(current_block, query):
            results.append(current_block)
        
        # 하위 블록들 큐에 추가
        children = self.get_child_blocks(current_block['block_index'])
        for child in children:
            queue.append((child, depth + 1))
            
    return results
```

## 🎯 기대 효과

### 1. 검색 성능 개선
- **계층 우선 탐색**: 관련성 높은 클러스터부터 우선 검색
- **다중참조 활용**: 하나의 기억을 여러 경로로 접근 가능
- **캐시 최적화**: 자주 접근되는 앵커 블록 메모리 캐싱

### 2. 맥락 이해 강화
- **주제별 클러스터링**: 관련 기억들의 자연스러운 그룹화
- **연상 검색**: 직접 매칭되지 않아도 관련 맥락으로 접근
- **시간적 연속성**: 해시체인 + 의미적 클러스터 이중 구조

## ⚠️ 구현 복잡성

### 1. 기술적 도전과제
- **그래프 복잡도**: O(n²) 관계 매핑의 성능 최적화 필요
- **클러스터 동기화**: 새 메모리 추가 시 기존 클러스터 재계산
- **다중참조 일관성**: 순환참조 방지 및 무결성 보장

### 2. 점진적 구현 전략
```
Phase 1: 기본 계층 테이블 추가 (1-2주)
Phase 2: 단순 클러스터링 구현 (2-3주)  
Phase 3: 다중참조 시스템 (3-4주)
Phase 4: 계층적 검색 최적화 (2-3주)
```

## 🎯 결론

기술적으로 **구현 가능**하며, 현재 그리움 아키텍처와 **호환성** 유지하면서 점진적 확장 가능.

**핵심 가치**: 단순한 시간순 기억 → 인간처럼 연상하고 클러스터링하는 맥락적 기억 시스템