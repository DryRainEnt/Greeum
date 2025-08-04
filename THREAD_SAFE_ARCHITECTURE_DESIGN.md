# Thread-Safe Database Architecture Design

## 🎯 목표
SQLite 멀티스레드 환경에서 안전한 데이터베이스 액세스 아키텍처 설계

## 🔍 현재 문제점 분석

### 문제 1: 단일 연결 공유
```python
# 현재 문제 코드 (database_manager.py:38)
self.conn = sqlite3.connect(self.connection_string)  # 한 번만 생성
```

### 문제 2: 스레드 안전성 부족
- 20개 파일에서 DatabaseManager 사용
- 모든 컴포넌트가 동일한 연결 객체 공유
- 동시 접근 시 SQLite 스레드 오류 발생

## 💡 해결 방안 옵션

### Option A: Connection Pool 방식
```python
import threading
from queue import Queue

class ThreadSafeConnectionPool:
    def __init__(self, db_path, pool_size=10):
        self.db_path = db_path
        self.pool = Queue(maxsize=pool_size)
        self.local = threading.local()
        
        # 풀에 연결 미리 생성
        for _ in range(pool_size):
            conn = sqlite3.connect(db_path, check_same_thread=False)
            self.pool.put(conn)
    
    def get_connection(self):
        return self.pool.get()
    
    def return_connection(self, conn):
        self.pool.put(conn)
```

**장점**: 연결 재사용, 성능 최적화
**단점**: 복잡성 증가, 데드락 위험

### Option B: Thread-Local Connection 방식
```python
import threading

class ThreadSafeDatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.local = threading.local()
    
    def get_connection(self):
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(self.db_path)
            self.local.conn.row_factory = sqlite3.Row
        return self.local.conn
```

**장점**: 단순함, 스레드 격리 보장
**단점**: 연결당 메모리 사용량 증가

### Option C: WAL 모드 + check_same_thread=False 방식
```python
class WALDatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.lock = threading.RLock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        
        # WAL 모드 활성화
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
```

**장점**: 읽기 동시성 향상, 기존 코드 수정 최소화
**단점**: WAL 파일 관리 필요

## 🏗️ 권장 아키텍처: Hybrid 접근

### Phase 1: Thread-Local 기반 기본 구현
```python
class ThreadSafeDatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.local = threading.local()
        self._lock = threading.RLock()
        self._setup_wal_mode()
    
    def _setup_wal_mode(self):
        # 초기 WAL 모드 설정
        temp_conn = sqlite3.connect(self.db_path)
        temp_conn.execute("PRAGMA journal_mode=WAL")
        temp_conn.close()
    
    def get_connection(self):
        if not hasattr(self.local, 'conn'):
            self.local.conn = sqlite3.connect(self.db_path)
            self.local.conn.row_factory = sqlite3.Row
            # 연결별 설정
            self.local.conn.execute("PRAGMA foreign_keys=ON")
        return self.local.conn
    
    @contextmanager
    def transaction(self):
        conn = self.get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
```

### Phase 2: Connection Pool 최적화 (성능 향상)
고부하 환경에서 필요시 Connection Pool 추가

## 🧪 테스트 전략

### 1. 동시성 테스트 시나리오
```python
def test_concurrent_write():
    """100개 스레드가 동시에 블록 추가"""
    
def test_read_write_concurrency():
    """읽기/쓰기 동시 실행"""
    
def test_transaction_isolation():
    """트랜잭션 격리 수준 테스트"""
```

### 2. 성능 벤치마크
- 단일 스레드 vs 멀티스레드 성능 비교
- 메모리 사용량 측정
- 연결 누수 검사

## 📋 구현 로드맵

### Week 1: 아키텍처 재설계
1. ThreadSafeDatabaseManager 구현
2. 기존 DatabaseManager 호환성 유지
3. 단위 테스트 작성

### Week 2: 통합 및 검증
1. 전체 컴포넌트 통합 테스트
2. 성능 최적화
3. 문서화

### Week 3: 배포 및 모니터링
1. 단계별 배포
2. 실제 환경 모니터링
3. 피드백 반영

## 🚦 Migration 전략

### Backward Compatibility
```python
# 기존 코드 호환성 유지
class DatabaseManager(ThreadSafeDatabaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 기존 API 호환성 래퍼
```

### Feature Flag 방식
```python
ENABLE_THREAD_SAFE_DB = os.getenv('GREEUM_THREAD_SAFE', 'true').lower() == 'true'
```

이 설계로 점진적이고 안전한 마이그레이션이 가능합니다.