# Missing API Methods Implementation Design

## 🎯 목표
테스트에서 요구하는 누락된 API 메서드들의 완전한 구현

## 🔍 누락된 메서드 분석

### 1. DatabaseManager.health_check()
**테스트 요구사항**: `tests/test_v204_core.py:106`
```python
self.assertTrue(self.db_manager.health_check())
```

**예상 기능**:
- 데이터베이스 연결 상태 확인
- 기본 쿼리 실행 가능 여부 검증
- 스키마 무결성 체크

### 2. BlockManager.verify_integrity()
**테스트 요구사항**: `tests/test_v204_core.py:205`
```python
integrity_check = self.block_manager.verify_integrity()
self.assertTrue(integrity_check)
```

**예상 기능**:
- 블록체인 무결성 검증
- 해시 체인 연결 확인
- 데이터 일관성 검사

## 💡 구현 설계

### DatabaseManager.health_check() 구현
```python
def health_check(self) -> bool:
    """
    데이터베이스 상태 및 무결성 검사
    
    Returns:
        bool: 데이터베이스가 정상 상태이면 True
    """
    try:
        conn = self.get_connection()
        
        # 1. 기본 연결 테스트
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        
        # 2. 필수 테이블 존재 확인
        required_tables = ['blocks', 'metadata']
        for table in required_tables:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table,))
            if not cursor.fetchone():
                logger.error(f"Required table '{table}' not found")
                return False
        
        # 3. 테이블 스키마 검증
        cursor.execute("PRAGMA table_info(blocks)")
        columns = {row[1] for row in cursor.fetchall()}
        required_columns = {
            'block_index', 'timestamp', 'context', 
            'keywords', 'tags', 'embedding', 'importance', 
            'hash', 'prev_hash'
        }
        if not required_columns.issubset(columns):
            logger.error("Blocks table missing required columns")
            return False
        
        # 4. 기본 무결성 테스트
        cursor.execute("PRAGMA integrity_check(1)")
        result = cursor.fetchone()
        if result[0] != 'ok':
            logger.error(f"Database integrity check failed: {result[0]}")
            return False
        
        # 5. 읽기/쓰기 권한 테스트
        test_table = f"health_check_test_{int(time.time())}"
        cursor.execute(f"CREATE TEMP TABLE {test_table} (id INTEGER)")
        cursor.execute(f"INSERT INTO {test_table} VALUES (1)")
        cursor.execute(f"SELECT id FROM {test_table}")
        if cursor.fetchone()[0] != 1:
            return False
        cursor.execute(f"DROP TABLE {test_table}")
        
        conn.commit()
        logger.info("Database health check passed")
        return True
    
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
```

### BlockManager.verify_integrity() 구현
```python
def verify_integrity(self) -> bool:
    """
    블록체인 무결성 검증
    
    Returns:
        bool: 블록체인이 무결성을 유지하면 True
    """
    try:
        # 1. 모든 블록 조회 (인덱스 순)
        blocks = self.db_manager.get_blocks()
        if not blocks:
            logger.info("No blocks to verify")
            return True
        
        # 2. 정렬 및 연속성 확인
        sorted_blocks = sorted(blocks, key=lambda x: x['block_index'])
        
        prev_hash = ""
        for i, block in enumerate(sorted_blocks):
            # 인덱스 연속성 확인
            expected_index = i
            if block['block_index'] != expected_index:
                logger.error(f"Block index discontinuity: expected {expected_index}, got {block['block_index']}")
                return False
            
            # 해시 체인 검증
            if block['prev_hash'] != prev_hash:
                logger.error(f"Hash chain broken at block {i}: expected prev_hash '{prev_hash}', got '{block['prev_hash']}'")
                return False
            
            # 현재 블록 해시 재계산 및 검증
            calculated_hash = self._compute_hash({
                'block_index': block['block_index'],
                'timestamp': block['timestamp'],
                'context': block['context'],
                'keywords': block['keywords'],
                'tags': block['tags'],
                'embedding': block['embedding'],
                'importance': block['importance'],
                'prev_hash': block['prev_hash']
            })
            
            if calculated_hash != block['hash']:
                logger.error(f"Block {i} hash mismatch: calculated '{calculated_hash}', stored '{block['hash']}'")
                return False
            
            prev_hash = block['hash']
        
        # 3. 메타데이터 일관성 확인
        total_blocks = len(sorted_blocks)
        last_block_index = sorted_blocks[-1]['block_index'] if sorted_blocks else -1
        
        # 데이터베이스 메타데이터와 비교
        metadata = self.db_manager.get_metadata()
        if metadata:
            stored_count = metadata.get('total_blocks', 0)
            stored_last_index = metadata.get('last_block_index', -1)
            
            if stored_count != total_blocks:
                logger.error(f"Metadata count mismatch: stored {stored_count}, actual {total_blocks}")
                return False
            
            if stored_last_index != last_block_index:
                logger.error(f"Metadata last index mismatch: stored {stored_last_index}, actual {last_block_index}")
                return False
        
        logger.info(f"Blockchain integrity verified: {total_blocks} blocks")
        return True
    
    except Exception as e:
        logger.error(f"Integrity verification failed: {e}")
        return False
```

### 추가 지원 메서드들
```python
# DatabaseManager에 추가
def get_metadata(self) -> Dict[str, Any]:
    """메타데이터 테이블에서 시스템 정보 조회"""
    
def update_metadata(self, key: str, value: Any):
    """메타데이터 업데이트"""

# BlockManager에 추가  
def repair_integrity(self) -> bool:
    """가능한 범위에서 블록체인 무결성 복구"""
    
def get_integrity_report(self) -> Dict[str, Any]:
    """상세한 무결성 검사 리포트"""
```

## 🧪 테스트 케이스 설계

### health_check() 테스트
```python
def test_health_check_normal(self):
    """정상 상태에서 health_check"""
    
def test_health_check_missing_table(self):
    """테이블 누락 상황"""
    
def test_health_check_corrupted_schema(self):
    """스키마 손상 상황"""
    
def test_health_check_no_permissions(self):
    """권한 부족 상황"""
```

### verify_integrity() 테스트
```python
def test_verify_integrity_empty_chain(self):
    """빈 블록체인"""
    
def test_verify_integrity_valid_chain(self):
    """정상 블록체인"""
    
def test_verify_integrity_broken_hash_chain(self):
    """해시 체인 손상"""
    
def test_verify_integrity_missing_blocks(self):
    """블록 누락"""
    
def test_verify_integrity_tampered_data(self):
    """데이터 변조 감지"""
```

## 📋 구현 계획

### Day 1: 기본 구현
- [ ] DatabaseManager.health_check() 구현
- [ ] BlockManager.verify_integrity() 구현  
- [ ] 기본 단위 테스트 작성

### Day 2: 고급 기능
- [ ] 상세 에러 리포팅
- [ ] 복구 기능 구현
- [ ] 성능 최적화

### Day 3: 통합 테스트
- [ ] 전체 시스템 통합 테스트
- [ ] 엣지 케이스 처리
- [ ] 문서화

이 설계로 완전하고 견고한 API가 구현됩니다.