"""
Thread-Safe Database Manager Implementation for Phase 2

이 모듈은 SQLite 스레딩 오류를 해결하기 위한 thread-safe 데이터베이스 관리자를 구현합니다.
기존 DatabaseManager와 100% API 호환성을 유지하면서 동시 접근 문제를 해결합니다.

핵심 설계 원칙:
1. threading.local()을 사용한 스레드별 연결 관리
2. WAL 모드 활성화로 동시 읽기 최적화
3. 기존 API 완전 호환성 유지
4. 기능 플래그를 통한 안전한 전환

Progressive Replacement Plan Phase 2의 핵심 구현체입니다.
"""

import os
import sqlite3
import json
import threading
import queue
import datetime
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Callable, TypeVar
import logging

from .branch_schema import BranchSchemaSQL
from .stm_anchor_store import STMAnchorStore
from .db_integrity import (
    backup_database_files,
    is_corruption_error,
    rebuild_empty_sqlite_database,
    remove_database_files,
)

logger = logging.getLogger(__name__)

WriteResult = TypeVar("WriteResult")
WriteTask = Tuple[
    Optional[Callable[[sqlite3.Connection], WriteResult]],
    Optional[List[WriteResult]],
    Optional[List[BaseException]],
    threading.Event,
]


class ThreadSafeDatabaseManager:
    """
    Thread-safe SQLite database manager using threading.local()
    
    이 클래스는 SQLite의 "objects can only be used in the same thread" 오류를 해결합니다.
    각 스레드마다 독립적인 데이터베이스 연결을 유지하여 동시 접근을 안전하게 처리합니다.
    """
    
    def __init__(self, connection_string=None, db_type='sqlite'):
        """
        Thread-safe 데이터베이스 관리자 초기화
        
        Args:
            connection_string: 데이터베이스 연결 문자열 (기본값: data/memory.db)
            db_type: 데이터베이스 타입 (현재는 sqlite만 지원)
        """
        self.db_type = db_type
        self.connection_string = self._resolve_connection_string(connection_string)
        
        # Thread-local storage for database connections
        self.local = threading.local()
        
        # 데이터 디렉토리 생성
        self._ensure_data_dir()
        self._ensure_anchor_env()
        
        # WAL 모드 설정 (동시 읽기 최적화)
        self._setup_wal_mode()
        
        # Legacy 호환 매니저 (지연 생성)
        self._legacy_manager = None

        # 초기 연결에서 무결성 확인 및 스키마 생성
        conn = self._get_connection()
        conn = self._ensure_integrity(conn)
        self._create_schemas(conn)

        # Sequential write queue ensures SQLite writes are serialized
        self._write_queue: queue.Queue[Tuple[Optional[Callable[[sqlite3.Connection], WriteResult]], Optional[List[WriteResult]], Optional[List[BaseException]], threading.Event]] = queue.Queue()
        self._write_thread = threading.Thread(
            target=self._write_worker,
            name="GreeumWriteWorker",
            daemon=True,
        )
        self._write_thread.start()

        logger.info(f"ThreadSafeDatabaseManager 초기화 완료: {self.connection_string} (type: {self.db_type})")
    
    def _ensure_data_dir(self):
        """데이터 디렉토리 존재 확인"""
        data_dir = os.path.dirname(self.connection_string)
        if data_dir:
            os.makedirs(data_dir, exist_ok=True)

    def _ensure_anchor_env(self) -> None:
        """Ensure STM anchor database follows the same base directory."""
        if "GREEUM_STM_DB" in os.environ:
            return

        try:
            db_dir = Path(self.connection_string).expanduser().resolve().parent
        except Exception:  # noqa: BLE001
            return

        anchor_path = db_dir / "stm_anchors.db"
        os.environ.setdefault("GREEUM_STM_DB", str(anchor_path))

    def _resolve_connection_string(self, explicit: Optional[str]) -> str:
        """Resolve the database path, honoring environment overrides."""
        if explicit:
            return explicit

        env_dir = os.environ.get('GREEUM_DATA_DIR')
        if env_dir:
            direct_path = os.path.join(env_dir, 'memory.db')
            if os.path.exists(direct_path):
                logger.info(f"[DB] Using environment variable path: {direct_path}")
                return direct_path

            sub_path = os.path.join(env_dir, 'data', 'memory.db')
            if os.path.exists(sub_path):
                logger.info(f"[DB] Using environment variable path: {sub_path}")
                return sub_path

            os.makedirs(os.path.join(env_dir, 'data'), exist_ok=True)
            logger.info(f"[DB] Creating database at environment path: {sub_path}")
            return sub_path

        cwd = os.getcwd()
        local_db_path = os.path.join(cwd, 'data', 'memory.db')
        if os.path.exists(local_db_path) or 'greeum' in cwd.lower():
            logger.info(f"[DB] Using local project database: {local_db_path}")
            return local_db_path

        home_dir = os.path.expanduser('~')
        user_db_path = os.path.join(home_dir, '.greeum', 'memory.db')
        logger.info(f"[DB] Using global user database: {user_db_path}")
        return user_db_path
    
    def _setup_wal_mode(self):
        """
        WAL(Write-Ahead Logging) 모드 설정
        
        WAL 모드는 다음과 같은 이점을 제공합니다:
        - 동시 읽기 작업 허용
        - 쓰기 작업 중에도 읽기 가능
        - 더 나은 동시성 성능
        """
        if self.db_type == 'sqlite':
            try:
                # 임시 연결로 WAL 모드 설정
                temp_conn = sqlite3.connect(self.connection_string)
                temp_conn.execute("PRAGMA journal_mode=WAL")
                temp_conn.execute("PRAGMA synchronous=NORMAL")  # 성능 최적화
                temp_conn.execute("PRAGMA temp_store=MEMORY")   # 임시 데이터 메모리 저장
                temp_conn.execute("PRAGMA mmap_size=268435456") # 256MB 메모리 맵
                temp_conn.commit()
                temp_conn.close()
                logger.info("WAL 모드 설정 완료 - 동시 접근 최적화 활성화")
            except Exception as e:
                logger.warning(f"WAL 모드 설정 실패: {e}")
    
    def _get_connection(self):
        """
        현재 스레드에 대한 데이터베이스 연결 반환
        
        threading.local()을 사용하여 각 스레드마다 독립적인 연결을 유지합니다.
        이것이 SQLite 스레딩 오류를 해결하는 핵심 메커니즘입니다.
        
        Returns:
            sqlite3.Connection: 현재 스레드용 데이터베이스 연결
        """
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            if self.db_type == 'sqlite':
                timeout = float(os.getenv('GREEUM_SQLITE_TIMEOUT', '10'))
                self.local.conn = sqlite3.connect(
                    self.connection_string,
                    check_same_thread=False,  # 스레드 체크 비활성화
                    timeout=timeout,
                )
                self.local.conn.row_factory = sqlite3.Row
                
                # 연결별 최적화 설정
                try:
                    self.local.conn.execute("PRAGMA foreign_keys=ON")
                    self.local.conn.execute("PRAGMA cache_size=10000")
                    self.local.conn.execute("PRAGMA journal_mode=WAL")
                    self.local.conn.execute("PRAGMA synchronous=NORMAL")
                    busy_ms = int(float(os.getenv('GREEUM_SQLITE_BUSY_TIMEOUT', '0.2')) * 1000)
                    self.local.conn.execute(f'PRAGMA busy_timeout = {busy_ms}')
                except sqlite3.OperationalError as pragma_error:
                    logger.debug("Thread-safe PRAGMA setup skipped: %s", pragma_error)
                except sqlite3.DatabaseError as exc:
                    if is_corruption_error(exc):
                        logger.warning(
                            "Encountered corrupt database while applying PRAGMA (%s). Rebuilding %s.",
                            exc,
                            self.connection_string,
                        )
                        return self._repair_corrupt_database(str(exc))
                    raise

                logger.debug(f"새 스레드 연결 생성: {threading.current_thread().name}")
                self.local._integrity_checked = False
            else:
                raise ValueError(f"지원하지 않는 데이터베이스 타입: {self.db_type}")

        if not getattr(self.local, '_integrity_checked', False):
            conn = self._ensure_integrity(self.local.conn)
            self.local.conn = conn
            self.local._integrity_checked = True

        return self.local.conn

    def _ensure_integrity(self, conn: sqlite3.Connection) -> sqlite3.Connection:
        """Validate SQLite integrity and rebuild the database when corrupted."""

        if self.db_type != 'sqlite':
            return conn

        try:
            row = conn.execute("PRAGMA integrity_check").fetchone()
        except sqlite3.DatabaseError as exc:
            if not is_corruption_error(exc):
                raise
            logger.warning(
                "Thread-safe manager detected corrupt database (%s). Rebuilding %s.",
                exc,
                self.connection_string,
            )
            return self._repair_corrupt_database(str(exc))

        if not row:
            raise sqlite3.DatabaseError("integrity_check returned no rows")

        result = (row[0] or "").lower()
        if result != 'ok':
            exc = sqlite3.DatabaseError(result)
            if not is_corruption_error(exc):
                raise exc
            logger.warning(
                "integrity_check reported '%s'. Rebuilding database %s.",
                result,
                self.connection_string,
            )
            return self._repair_corrupt_database(result)

        return conn

    def _repair_corrupt_database(self, reason: str) -> sqlite3.Connection:
        """Backup the corrupted DB, rebuild, and return a fresh connection."""

        db_path = Path(self.connection_string)
        current_conn = getattr(self.local, 'conn', None)
        if current_conn is not None:
            try:
                current_conn.close()
            except Exception:  # pragma: no cover
                pass
        self.local.conn = None

        backup_path = backup_database_files(db_path, label='malformed')
        if backup_path:
            logger.info("Backed up corrupt database to %s", backup_path)

        remove_database_files(db_path)
        rebuild_empty_sqlite_database(db_path)

        timeout = float(os.getenv('GREEUM_SQLITE_TIMEOUT', '10'))
        new_conn = sqlite3.connect(
            self.connection_string,
            check_same_thread=False,
            timeout=timeout,
        )
        new_conn.row_factory = sqlite3.Row
        try:
            new_conn.execute("PRAGMA foreign_keys=ON")
            new_conn.execute("PRAGMA cache_size=10000")
            new_conn.execute("PRAGMA journal_mode=WAL")
            new_conn.execute("PRAGMA synchronous=NORMAL")
            busy_ms = int(float(os.getenv('GREEUM_SQLITE_BUSY_TIMEOUT', '0.2')) * 1000)
            new_conn.execute(f'PRAGMA busy_timeout = {busy_ms}')
        except sqlite3.OperationalError as pragma_error:
            logger.debug("Thread-safe PRAGMA setup skipped after repair: %s", pragma_error)

        self.local.conn = new_conn
        logger.info("Thread-safe database rebuilt after corruption (%s)", reason)
        self.local._integrity_checked = True
        return new_conn

    def _write_worker(self) -> None:
        """Background worker that serializes SQLite write operations."""
        conn = self._get_connection()
        while True:
            operation, result_container, error_container, event = self._write_queue.get()
            try:
                if operation is None:
                    if event:
                        event.set()
                    return

                try:
                    result = operation(conn)
                    if result_container is not None:
                        result_container.append(result)
                except Exception as exc:  # pragma: no cover - propagated to caller
                    if error_container is not None:
                        error_container.append(exc)
                finally:
                    if event:
                        event.set()
            finally:
                self._write_queue.task_done()

    def _execute_write(self, operation: Callable[[sqlite3.Connection], WriteResult]) -> WriteResult:
        """Submit a write operation to the queue and wait for the result."""
        result_container: List[WriteResult] = []
        error_container: List[BaseException] = []
        event = threading.Event()
        self._write_queue.put((operation, result_container, error_container, event))
        event.wait()
        if error_container:
            raise error_container[0]
        return result_container[0] if result_container else None

    def run_serialized(self, func: Callable[[], WriteResult]) -> WriteResult:
        """Execute callable inside the write queue, reusing the worker connection."""

        def operation(conn: sqlite3.Connection) -> WriteResult:
            # Connection already bound to worker thread; just execute callable
            return func()

        if threading.current_thread() is getattr(self, "_write_thread", None):
            return func()
        return self._execute_write(operation)

    # ------------------------------------------------------------------
    # Compatibility search helpers
    # ------------------------------------------------------------------

    def search_blocks_by_keyword(self, keywords: List[str], limit: int = 100) -> List[Dict[str, Any]]:
        """Keyword-based block search compatible with DatabaseManager."""

        if not keywords:
            return []

        cursor = self._get_connection().cursor()
        block_indices: set[int] = set()

        for keyword in keywords:
            if not keyword:
                continue
            kw_lower = keyword.lower()

            cursor.execute(
                "SELECT DISTINCT block_index FROM block_keywords WHERE lower(keyword) LIKE ?",
                (f"%{kw_lower}%",),
            )
            block_indices.update(row[0] for row in cursor.fetchall())

            cursor.execute(
                "SELECT block_index FROM blocks WHERE lower(context) LIKE ? LIMIT ?",
                (f"%{kw_lower}%", limit),
            )
            block_indices.update(row[0] for row in cursor.fetchall())

        results: List[Dict[str, Any]] = []
        for index in block_indices:
            block = self.get_block(index)
            if block:
                results.append(block)

        return results[:limit]

    def search_blocks_by_embedding(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        min_similarity: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Embedding-based block search compatible with DatabaseManager."""

        if not query_embedding:
            return []

        query_vector = np.asarray(query_embedding, dtype=np.float32)
        if query_vector.ndim > 1:
            query_vector = query_vector.reshape(-1)

        query_norm = float(np.linalg.norm(query_vector))
        if query_norm == 0.0:
            return []

        cursor = self._get_connection().cursor()
        cursor.execute("SELECT block_index, embedding, embedding_dim FROM block_embeddings")

        scored: List[Tuple[int, float]] = []
        for block_index, embedding_blob, embedding_dim in cursor.fetchall():
            if not embedding_blob:
                continue

            block_vector = np.frombuffer(embedding_blob, dtype=np.float32)
            if embedding_dim:
                block_vector = block_vector[:embedding_dim]

            if block_vector.shape != query_vector.shape:
                continue

            block_norm = float(np.linalg.norm(block_vector))
            if block_norm == 0.0:
                continue

            similarity = float(np.dot(query_vector, block_vector) / (query_norm * block_norm))
            if similarity < min_similarity:
                continue

            scored.append((block_index, similarity))

        scored.sort(key=lambda item: item[1], reverse=True)

        results: List[Dict[str, Any]] = []
        for block_index, similarity in scored[:top_k]:
            block = self.get_block(block_index)
            if block:
                block["similarity"] = similarity
                results.append(block)

        return results

    def get_blocks_since_time(self, since_timestamp: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch blocks stored after the provided ISO timestamp."""

        if not since_timestamp:
            return []

        cursor = self._get_connection().cursor()
        cursor.execute(
            """
            SELECT block_index FROM blocks
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (since_timestamp, limit),
        )

        results: List[Dict[str, Any]] = []
        for (block_index,) in cursor.fetchall():
            block = self.get_block(block_index)
            if block:
                results.append(block)

        return results

    def _create_schemas(self, conn):
        """
        필요한 테이블 생성
        
        기존 DatabaseManager와 동일한 스키마를 생성하여 완전한 호환성을 보장합니다.
        """
        cursor = conn.cursor()
        
        # 블록 테이블
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            block_index INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            context TEXT NOT NULL,
            importance REAL NOT NULL,
            hash TEXT NOT NULL,
            prev_hash TEXT NOT NULL
        )
        ''')
        
        # 키워드 테이블 (M:N 관계)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS block_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_index INTEGER NOT NULL,
            keyword TEXT NOT NULL,
            FOREIGN KEY (block_index) REFERENCES blocks(block_index),
            UNIQUE(block_index, keyword)
        )
        ''')
        
        # 태그 테이블 (M:N 관계)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS block_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_index INTEGER NOT NULL,
            tag TEXT NOT NULL,
            FOREIGN KEY (block_index) REFERENCES blocks(block_index),
            UNIQUE(block_index, tag)
        )
        ''')
        
        # 메타데이터 테이블 (JSON 저장)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS block_metadata (
            block_index INTEGER PRIMARY KEY,
            metadata TEXT NOT NULL,
            FOREIGN KEY (block_index) REFERENCES blocks(block_index)
        )
        ''')
        
        # 임베딩 테이블
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS block_embeddings (
            block_index INTEGER PRIMARY KEY,
            embedding BLOB NOT NULL,
            embedding_model TEXT,
            embedding_dim INTEGER,
            FOREIGN KEY (block_index) REFERENCES blocks(block_index)
        )
        ''')
        
        # 단기 기억 테이블 (legacy compatibility)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS short_term_memories (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            content TEXT NOT NULL,
            speaker TEXT,
            metadata TEXT
        )
        ''')

        # 인덱스 생성 (성능 최적화)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocks_timestamp ON blocks(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_block_keywords ON block_keywords(keyword)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_block_tags ON block_tags(tag)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stm_timestamp ON short_term_memories(timestamp)')

        # Branch schema and additional tables
        try:
            if BranchSchemaSQL.check_migration_needed(cursor):
                for stmt in BranchSchemaSQL.get_migration_sql():
                    cursor.execute(stmt)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Branch schema migration skipped: {exc}")

        self._create_v3_tables(cursor)
        self._initialize_branch_structures(cursor)

        conn.commit()
        logger.debug("Thread-safe 데이터베이스 스키마 생성 완료")

    def _initialize_branch_structures(self, cursor) -> None:
        """Migrate legacy stm_slots table to the anchor store when present."""
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='stm_slots'"
            )
            if not cursor.fetchone():
                return

            cursor.execute(
                "SELECT slot_name, block_hash, branch_root, updated_at FROM stm_slots"
            )
            rows = cursor.fetchall()

            anchor_path = Path(os.environ.get("GREEUM_STM_DB", "")).expanduser()
            if not anchor_path:
                anchor_path = Path(self.connection_string).expanduser().resolve().parent / "stm_anchors.db"

            anchor_store = STMAnchorStore(anchor_path)
            for slot_name, block_hash, branch_root, updated_at in rows:
                anchor_store.upsert_slot(
                    slot_name=slot_name,
                    anchor_block=block_hash,
                    topic_vec=None,
                    summary=branch_root or "",
                    last_seen=updated_at or 0,
                    hysteresis=0,
                )

            try:
                anchor_store.close()
            except Exception:  # noqa: BLE001
                pass

            cursor.execute("DROP TABLE IF EXISTS stm_slots")
            logger.info("Migrated legacy stm_slots table into stm_anchors store")

        except sqlite3.OperationalError as exc:
            logger.debug(f"stm_slots migration skipped: {exc}")

    def _create_v3_tables(self, cursor) -> None:
        """Create newer association and actant tables used by the engine."""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_nodes (
                node_id TEXT PRIMARY KEY,
                memory_id INTEGER,
                node_type TEXT,
                content TEXT,
                embedding TEXT,
                activation_level REAL DEFAULT 0.0,
                last_activated TEXT,
                metadata TEXT,
                created_at TEXT,
                FOREIGN KEY (memory_id) REFERENCES blocks(block_index)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS associations (
                association_id TEXT PRIMARY KEY,
                source_node_id TEXT,
                target_node_id TEXT,
                association_type TEXT,
                strength REAL DEFAULT 0.5,
                weight REAL DEFAULT 1.0,
                created_at TEXT,
                last_activated TEXT,
                activation_count INTEGER DEFAULT 0,
                metadata TEXT,
                FOREIGN KEY (source_node_id) REFERENCES memory_nodes(node_id),
                FOREIGN KEY (target_node_id) REFERENCES memory_nodes(node_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activation_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT,
                activation_level REAL,
                trigger_type TEXT,
                trigger_source TEXT,
                timestamp TEXT,
                session_id TEXT,
                FOREIGN KEY (node_id) REFERENCES memory_nodes(node_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS context_sessions (
                session_id TEXT PRIMARY KEY,
                active_nodes TEXT,
                activation_snapshot TEXT,
                created_at TEXT,
                last_updated TEXT,
                metadata TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_actants (
                actant_id TEXT PRIMARY KEY,
                memory_id INTEGER,
                subject_raw TEXT,
                subject_hash TEXT,
                action_raw TEXT,
                action_hash TEXT,
                object_raw TEXT,
                object_hash TEXT,
                sender_raw TEXT,
                sender_hash TEXT,
                receiver_raw TEXT,
                receiver_hash TEXT,
                helper_raw TEXT,
                helper_hash TEXT,
                opponent_raw TEXT,
                opponent_hash TEXT,
                confidence REAL DEFAULT 0.5,
                parser_version TEXT,
                parsed_at TEXT,
                metadata TEXT,
                FOREIGN KEY (memory_id) REFERENCES blocks(block_index)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actant_entities (
                entity_hash TEXT PRIMARY KEY,
                entity_type TEXT,
                canonical_form TEXT,
                variations TEXT,
                first_seen TEXT,
                last_seen TEXT,
                occurrence_count INTEGER DEFAULT 1,
                metadata TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actant_actions (
                action_hash TEXT PRIMARY KEY,
                action_type TEXT,
                canonical_form TEXT,
                variations TEXT,
                tense TEXT,
                aspect TEXT,
                first_seen TEXT,
                last_seen TEXT,
                occurrence_count INTEGER DEFAULT 1,
                metadata TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actant_relations (
                relation_id TEXT PRIMARY KEY,
                source_actant_id TEXT,
                target_actant_id TEXT,
                relation_type TEXT,
                strength REAL DEFAULT 0.5,
                evidence_count INTEGER DEFAULT 1,
                created_at TEXT,
                last_updated TEXT,
                metadata TEXT,
                FOREIGN KEY (source_actant_id) REFERENCES memory_actants(actant_id),
                FOREIGN KEY (target_actant_id) REFERENCES memory_actants(actant_id)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_memory ON memory_nodes(memory_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_activation ON memory_nodes(activation_level)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_associations_source ON associations(source_node_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_associations_target ON associations(target_node_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_associations_strength ON associations(strength)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_activation_history_node ON activation_history(node_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_activation_history_session ON activation_history(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_actants_memory ON memory_actants(memory_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_actants_subject ON memory_actants(subject_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_actants_action ON memory_actants(action_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_actants_object ON memory_actants(object_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_entities_type ON actant_entities(entity_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_actions_type ON actant_actions(action_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_relations_source ON actant_relations(source_actant_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_relations_target ON actant_relations(target_actant_id)')
    
    def close(self):
        """
        현재 스레드의 데이터베이스 연결 종료

        모든 스레드의 연결을 정리하는 것은 복잡하므로, 현재 스레드의 연결만 정리합니다.
        일반적으로 프로그램 종료 시 자동으로 정리됩니다.
        """
        if hasattr(self.local, 'conn') and self.local.conn:
            self.local.conn.close()
            self.local.conn = None
            logger.debug(f"스레드별 데이터베이스 연결 종료: {threading.current_thread().name}")

    def shutdown(self):
        """Gracefully stop the background write worker."""
        if not hasattr(self, '_write_queue') or self._write_queue is None:
            return
        event = threading.Event()
        self._write_queue.put((None, None, None, event))
        event.wait()
        try:
            self._write_thread.join(timeout=1.0)
        except RuntimeError:
            pass
        self._write_queue = None
    
    def health_check(self) -> bool:
        """
        Thread-safe 데이터베이스 상태 및 무결성 검사
        
        Returns:
            bool: 데이터베이스가 정상 상태이면 True
        """
        import time
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 1. 기본 연결 테스트
            cursor.execute("SELECT 1")
            
            # 2. 필수 테이블 존재 확인
            required_tables = ['blocks', 'block_keywords', 'block_tags', 'block_metadata']
            for table in required_tables:
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table,))
                if not cursor.fetchone():
                    logger.error(f"Required table '{table}' not found")
                    return False
            
            # 3. 테이블 스키마 검증 (blocks 테이블)
            cursor.execute("PRAGMA table_info(blocks)")
            columns = {row[1] for row in cursor.fetchall()}
            required_columns = {
                'block_index', 'timestamp', 'context', 
                'importance', 'hash', 'prev_hash'
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
            logger.info(f"Thread-safe database health check passed - Thread: {threading.current_thread().name}")
            return True
        
        except Exception as e:
            logger.error(f"Thread-safe database health check failed: {e}")
            return False
    
    # Delegate methods to maintain compatibility with legacy DatabaseManager
    def get_block(self, block_index: int) -> Optional[Dict[str, Any]]:
        cursor = self._get_connection().cursor()
        cursor.execute("SELECT * FROM blocks WHERE block_index = ?", (block_index,))
        row = cursor.fetchone()
        if not row:
            logger.warning(f"Block retrieval failed: index={block_index} not found")
            return None

        block = dict(row)

        cursor.execute("SELECT keyword FROM block_keywords WHERE block_index = ?", (block_index,))
        block['keywords'] = [keyword for (keyword,) in cursor.fetchall()]

        cursor.execute("SELECT tag FROM block_tags WHERE block_index = ?", (block_index,))
        block['tags'] = [tag for (tag,) in cursor.fetchall()]

        cursor.execute("SELECT metadata FROM block_metadata WHERE block_index = ?", (block_index,))
        metadata_row = cursor.fetchone()
        block['metadata'] = json.loads(metadata_row[0]) if metadata_row and metadata_row[0] else {}

        cursor.execute(
            """
            SELECT embedding, embedding_dim, embedding_model
            FROM block_embeddings
            WHERE block_index = ?
            """,
            (block_index,),
        )
        embedding_row = cursor.fetchone()
        if embedding_row:
            embedding_blob, embedding_dim, embedding_model = embedding_row
            embedding_array = np.frombuffer(embedding_blob, dtype=np.float32)
            if embedding_dim:
                embedding_array = embedding_array[:embedding_dim]
            block['embedding'] = embedding_array.tolist()
            block['embedding_model'] = embedding_model

        return block

    def _add_block_direct(self, block_data: Dict[str, Any]) -> Optional[int]:
        conn = self._get_connection()
        cursor = conn.cursor()

        block_index = block_data.get('block_index')
        started_transaction = False

        try:
            if not conn.in_transaction:
                conn.execute("BEGIN TRANSACTION")
                started_transaction = True

            cursor.execute("PRAGMA table_info(blocks)")
            columns = {row[1] for row in cursor.fetchall()}

            base_columns = {'block_index', 'timestamp', 'context', 'importance', 'hash', 'prev_hash'}
            branch_columns = {
                'root', 'before', 'after', 'xref', 'branch_depth', 'visit_count', 'last_seen_at'
            }
            extended_branch_columns = branch_columns | {'slot', 'branch_similarity', 'branch_created_at'}

            if not base_columns.issubset(columns):
                raise sqlite3.OperationalError("blocks table missing required columns")

            insert_columns = [
                'block_index', 'timestamp', 'context', 'importance', 'hash', 'prev_hash'
            ]
            values = [
                block_data.get('block_index'),
                block_data.get('timestamp'),
                block_data.get('context'),
                block_data.get('importance', 0.0),
                block_data.get('hash'),
                block_data.get('prev_hash', '')
            ]

            if branch_columns.issubset(columns):
                insert_columns.extend(['root', 'before', 'after', 'xref', 'branch_depth', 'visit_count', 'last_seen_at'])
                values.extend([
                    block_data.get('root'),
                    block_data.get('before'),
                    json.dumps(block_data.get('after', [])),
                    json.dumps(block_data.get('xref', [])),
                    block_data.get('branch_depth', 0),
                    block_data.get('visit_count', 0),
                    block_data.get('last_seen_at', 0)
                ])

            if extended_branch_columns.issubset(columns):
                insert_columns.extend(['slot', 'branch_similarity', 'branch_created_at'])
                values.extend([
                    block_data.get('slot'),
                    block_data.get('branch_similarity', 0.0),
                    block_data.get('branch_created_at', 0.0)
                ])

            placeholders = ', '.join(['?'] * len(insert_columns))
            cursor.execute(
                f"INSERT INTO blocks ({', '.join(insert_columns)}) VALUES ({placeholders})",
                tuple(values)
            )

            keywords = block_data.get('keywords', [])
            for keyword in keywords:
                cursor.execute(
                    "INSERT OR IGNORE INTO block_keywords (block_index, keyword) VALUES (?, ?)",
                    (block_index, keyword)
                )

            tags = block_data.get('tags', [])
            for tag in tags:
                cursor.execute(
                    "INSERT OR IGNORE INTO block_tags (block_index, tag) VALUES (?, ?)",
                    (block_index, tag)
                )

            metadata = block_data.get('metadata', {})
            if metadata:
                cursor.execute(
                    "INSERT INTO block_metadata (block_index, metadata) VALUES (?, ?)",
                    (block_index, json.dumps(metadata))
                )

            embedding = block_data.get('embedding')
            if embedding:
                embedding_array = np.array(embedding, dtype=np.float32) if isinstance(embedding, list) else embedding
                cursor.execute(
                    """
                    INSERT INTO block_embeddings (block_index, embedding, embedding_model, embedding_dim)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        block_index,
                        embedding_array.tobytes(),
                        block_data.get('embedding_model', 'default'),
                        len(embedding_array),
                    )
                )

            if started_transaction:
                conn.commit()

            verification_cursor = conn.cursor()
            verification_cursor.execute(
                "SELECT block_index FROM blocks WHERE block_index = ?",
                (block_index,),
            )
            if not verification_cursor.fetchone():
                raise RuntimeError(
                    f"Post-commit verification failed: Block {block_index} not found after commit"
                )

            return block_index

        except sqlite3.IntegrityError as integrity_error:
            if started_transaction and conn.in_transaction:
                conn.rollback()
            logger.error(f"Integrity error adding block {block_index}: {integrity_error}")
            raise
        except Exception as exc:
            if started_transaction and conn.in_transaction:
                conn.rollback()
            logger.error(f"Failed to add block {block_index}: {exc}")
            raise

    def add_block(self, block_data: Dict[str, Any], connection: Optional[Any] = None) -> Optional[int]:
        try:
            if hasattr(self, '_write_thread') and threading.current_thread() is self._write_thread:
                return self._add_block_direct(block_data)
            return self.run_serialized(lambda: self._add_block_direct(block_data))
        except Exception as exc:  # pragma: no cover - error already logged upstream
            logger.error(f"Failed to add block via serialized queue: {exc}")
            return None
    
    def get_last_block_info(self) -> Optional[Dict[str, Any]]:
        """Return metadata for the most recently added block."""
        cursor = self._get_connection().cursor()
        cursor.execute(
            """
            SELECT block_index, timestamp, context, importance, hash, prev_hash
            FROM blocks
            ORDER BY block_index DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        if not row:
            return None

        columns = [column[0] for column in cursor.description]
        return dict(zip(columns, row))

    def get_blocks(
        self,
        start_idx: Optional[int] = None,
        end_idx: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "block_index",
        order: str = "asc",
    ) -> List[Dict[str, Any]]:
        """List blocks with optional range and sorting, mirroring legacy behaviour."""
        cursor = self._get_connection().cursor()

        valid_sort_fields = {"block_index", "timestamp", "importance"}
        if sort_by not in valid_sort_fields:
            sort_by = "block_index"
        order = order.upper()
        if order not in {"ASC", "DESC"}:
            order = "ASC"

        params: List[Any] = []
        query = "SELECT block_index FROM blocks"

        conditions: List[str] = []
        if start_idx is not None:
            conditions.append("block_index >= ?")
            params.append(start_idx)
        if end_idx is not None:
            conditions.append("block_index <= ?")
            params.append(end_idx)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        if sort_by == "importance":
            query += f" ORDER BY importance {order}"
        else:
            query += f" ORDER BY {sort_by} {order}"

        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, tuple(params))
        block_indices = [row[0] for row in cursor.fetchall()]

        blocks: List[Dict[str, Any]] = []
        for block_index in block_indices:
            block = self.get_block(block_index)
            if block:
                blocks.append(block)
        return blocks

    # ------------------------------------------------------------------
    # Short-term memory helpers (avoid legacy fallback)
    # ------------------------------------------------------------------

    def add_short_term_memory(self, memory_data: Dict[str, Any]) -> str:
        def op() -> str:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO short_term_memories (id, timestamp, content, speaker, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    memory_data.get('id'),
                    memory_data.get('timestamp'),
                    memory_data.get('content'),
                    memory_data.get('speaker'),
                    json.dumps(memory_data.get('metadata', {})) if memory_data.get('metadata') else '{}'
                ),
            )
            self.conn.commit()
            return memory_data.get('id')

        if threading.current_thread() is getattr(self, "_write_thread", None):
            return op()
        return self.run_serialized(op)

    def get_recent_short_term_memories(self, count: int = 10) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, timestamp, content, speaker, metadata
            FROM short_term_memories
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (count,),
        )
        memories: List[Dict[str, Any]] = []
        for row in cursor.fetchall():
            memory = dict(row)
            if memory.get('metadata'):
                memory['metadata'] = json.loads(memory['metadata'])
            else:
                memory['metadata'] = {}
            memories.append(memory)
        return memories

    def delete_expired_short_term_memories(self, ttl_seconds: int) -> int:
        def op() -> int:
            cutoff_time = (datetime.datetime.now() - datetime.timedelta(seconds=ttl_seconds)).isoformat()
            cursor = self.conn.cursor()
            cursor.execute(
                "DELETE FROM short_term_memories WHERE timestamp < ?",
                (cutoff_time,),
            )
            deleted = cursor.rowcount
            self.conn.commit()
            return deleted

        if threading.current_thread() is getattr(self, "_write_thread", None):
            return op()
        return self.run_serialized(op)

    def clear_short_term_memories(self) -> int:
        def op() -> int:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM short_term_memories')
            deleted = cursor.rowcount
            self.conn.commit()
            return deleted

        if threading.current_thread() is getattr(self, "_write_thread", None):
            return op()
        return self.run_serialized(op)

    def delete_short_term_memory(self, memory_id: str) -> None:
        def op() -> None:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM short_term_memories WHERE id = ?', (memory_id,))
            self.conn.commit()

        if threading.current_thread() is getattr(self, "_write_thread", None):
            op()
        else:
            self.run_serialized(op)

    def get_short_term_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, timestamp, content, speaker, metadata FROM short_term_memories WHERE id = ?",
            (memory_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        memory = dict(row)
        memory['metadata'] = json.loads(memory['metadata']) if memory.get('metadata') else {}
        return memory

    def get_block(self, block_index: int) -> Optional[Dict[str, Any]]:
        """Fetch a single block with keywords, tags, metadata, and embedding."""
        cursor = self._get_connection().cursor()
        cursor.execute(
            "SELECT * FROM blocks WHERE block_index = ?",
            (block_index,),
        )
        row = cursor.fetchone()
        if not row:
            logger.warning(f"Block retrieval failed: index={block_index} not found")
            return None

        block = dict(row)

        cursor.execute(
            "SELECT keyword FROM block_keywords WHERE block_index = ?",
            (block_index,),
        )
        block["keywords"] = [keyword for (keyword,) in cursor.fetchall()]

        cursor.execute(
            "SELECT tag FROM block_tags WHERE block_index = ?",
            (block_index,),
        )
        block["tags"] = [tag for (tag,) in cursor.fetchall()]

        cursor.execute(
            "SELECT metadata FROM block_metadata WHERE block_index = ?",
            (block_index,),
        )
        metadata_row = cursor.fetchone()
        block["metadata"] = json.loads(metadata_row[0]) if metadata_row and metadata_row[0] else {}

        cursor.execute(
            """
            SELECT embedding, embedding_dim, embedding_model
            FROM block_embeddings
            WHERE block_index = ?
            """,
            (block_index,),
        )
        embedding_row = cursor.fetchone()
        if embedding_row:
            embedding_blob, embedding_dim, embedding_model = embedding_row
            embedding_array = np.frombuffer(embedding_blob, dtype=np.float32)
            if embedding_dim:
                embedding_array = embedding_array[:embedding_dim]
            block["embedding"] = embedding_array.tolist()
            block["embedding_model"] = embedding_model

        return block

    def get_block_by_index(self, block_index: int) -> Optional[Dict[str, Any]]:
        return self.get_block(block_index)

    def __getattr__(self, name):
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    @property
    def conn(self):
        """Compatibility accessor returning thread-local connection."""
        return self._get_connection()

    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetchone: bool = False,
    ):
        """Execute a read-only query using the thread-local connection."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        return cursor.fetchone() if fetchone else cursor.fetchall()

    def _get_legacy_manager(self):
        """Lazily instantiate and cache the legacy DatabaseManager."""
        if self._legacy_manager is None:
            logger.warning("ThreadSafeDatabaseManager: instantiating legacy DatabaseManager delegate")
            from .database_manager import DatabaseManager as LegacyDatabaseManager

            self._legacy_manager = LegacyDatabaseManager(
                connection_string=self.connection_string,
                db_type=self.db_type,
            )
        return self._legacy_manager


# 기능 플래그 설정 - v2.7.0에서 기본값을 true로 변경
GREEUM_THREAD_SAFE = os.getenv('GREEUM_THREAD_SAFE', 'true').lower() == 'true'

def get_database_manager_class():
    """
    환경 변수에 따라 적절한 DatabaseManager 클래스 반환
    
    이 함수는 Phase 3에서 점진적 활성화를 위해 사용됩니다.
    """
    if GREEUM_THREAD_SAFE:
        logger.info("Thread-safe database manager 사용 - GREEUM_THREAD_SAFE=true")
        return ThreadSafeDatabaseManager
    else:
        # 기존 DatabaseManager import (Phase 3에서 구현)
        logger.info("Legacy database manager 사용 - GREEUM_THREAD_SAFE=false")
        from .database_manager import DatabaseManager as LegacyDatabaseManager
        return LegacyDatabaseManager


if __name__ == "__main__":
    # 간단한 테스트
    import tempfile
    import threading
    
    def test_thread_safety():
        """Thread-safe 기능 간단 테스트"""
        temp_db = tempfile.mktemp(suffix='.db')
        
        db_manager = ThreadSafeDatabaseManager(temp_db)
        
        def worker(thread_id):
            """각 스레드에서 실행될 작업"""
            try:
                # 건강성 검사
                result = db_manager.health_check()
                print(f"Thread {thread_id}: Health check = {result}")
            except Exception as e:
                print(f"Thread {thread_id}: Error = {e}")
        
        # 3개 스레드로 동시 테스트
        threads = []
        for i in range(3):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        db_manager.close()
        os.unlink(temp_db)
        print("Thread-safe 테스트 완료")
    
    test_thread_safety()
