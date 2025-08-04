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
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


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
        self.connection_string = connection_string or os.path.join('data', 'memory.db')
        
        # Thread-local storage for database connections
        self.local = threading.local()
        
        # 데이터 디렉토리 생성
        self._ensure_data_dir()
        
        # WAL 모드 설정 (동시 읽기 최적화)
        self._setup_wal_mode()
        
        # 초기 연결에서 스키마 생성
        with self._get_connection() as conn:
            self._create_schemas(conn)
            
        logger.info(f"ThreadSafeDatabaseManager 초기화 완료: {self.connection_string} (type: {self.db_type})")
    
    def _ensure_data_dir(self):
        """데이터 디렉토리 존재 확인"""
        data_dir = os.path.dirname(self.connection_string)
        if data_dir:
            os.makedirs(data_dir, exist_ok=True)
    
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
                self.local.conn = sqlite3.connect(
                    self.connection_string,
                    check_same_thread=False  # 스레드 체크 비활성화
                )
                self.local.conn.row_factory = sqlite3.Row
                
                # 연결별 최적화 설정
                self.local.conn.execute("PRAGMA foreign_keys=ON")
                self.local.conn.execute("PRAGMA cache_size=10000")
                
                logger.debug(f"새 스레드 연결 생성: {threading.current_thread().name}")
            else:
                raise ValueError(f"지원하지 않는 데이터베이스 타입: {self.db_type}")
        
        return self.local.conn
    
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
        
        # 단기 기억 테이블
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
        
        conn.commit()
        logger.debug("Thread-safe 데이터베이스 스키마 생성 완료")
    
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


# 기능 플래그 설정
GREEUM_THREAD_SAFE = os.getenv('GREEUM_THREAD_SAFE', 'false').lower() == 'true'

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