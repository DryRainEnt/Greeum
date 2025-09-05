"""
Phase 2 Compatibility Wrapper: Thread-Safe DatabaseManager

이 모듈은 기존 DatabaseManager와 100% API 호환성을 유지하면서 
ThreadSafeDatabaseManager의 thread-safe 기능을 제공합니다.

설계 원칙:
1. 기존 모든 메서드 시그니처 완전 유지
2. ThreadSafeDatabaseManager 상속으로 thread-safe 기능 획득
3. 기능 플래그를 통한 안전한 전환 제어
4. 기존 코드 0% 수정 요구

Progressive Replacement Plan Phase 2의 호환성 보장 구현체입니다.
"""

import os
import sqlite3
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

# Thread-safe 기반 클래스 import
from .thread_safe_db import ThreadSafeDatabaseManager

logger = logging.getLogger(__name__)


class DatabaseManager(ThreadSafeDatabaseManager):
    """
    Thread-Safe Database Manager with 100% Legacy API Compatibility
    
    기존 DatabaseManager의 모든 메서드를 그대로 유지하면서
    ThreadSafeDatabaseManager의 thread-safe 기능을 상속받습니다.
    
    이를 통해 기존 코드 수정 없이 SQLite 스레딩 오류를 해결합니다.
    """
    
    def __init__(self, connection_string=None, db_type='sqlite'):
        """
        데이터베이스 관리자 초기화 (기존 API 완전 호환)
        
        Args:
            connection_string: 데이터베이스 연결 문자열 (기본값: data/memory.db)
            db_type: 데이터베이스 타입 (sqlite, postgres 등)
        """
        # ThreadSafeDatabaseManager 초기화 호출
        super().__init__(connection_string, db_type)
        
        # 기존 코드와의 호환성을 위한 속성 설정
        self.conn = self._get_connection()  # Legacy 코드에서 self.conn 직접 접근 지원
        
        logger.info(f"Thread-Safe DatabaseManager 초기화 완료: {self.connection_string} (type: {self.db_type})")
    
    def _setup_connection(self):
        """
        데이터베이스 연결 설정 (Legacy 호환성 메서드)
        
        기존 코드에서 이 메서드를 호출할 수 있으므로 유지합니다.
        실제 구현은 ThreadSafeDatabaseManager._get_connection()을 사용합니다.
        """
        # ThreadSafeDatabaseManager의 연결 메커니즘 사용
        self.conn = self._get_connection()
    
    def _create_schemas(self, conn=None):
        """
        필요한 테이블 생성 (Legacy 호환성 메서드)
        
        기존 메서드 시그니처를 유지하면서 ThreadSafeDatabaseManager의 구현을 활용합니다.
        """
        if conn is None:
            conn = self._get_connection()
        
        # ThreadSafeDatabaseManager의 스키마 생성 호출
        super()._create_schemas(conn)
    
    def add_block(self, block_data: Dict[str, Any]) -> int:
        """
        새 블록 추가 (Thread-Safe 구현)
        
        Args:
            block_data: 블록 데이터
            
        Returns:
            추가된 블록의 인덱스
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        logger.debug(f"Thread-safe 새 블록 추가 시도: index={block_data.get('block_index')}")
        
        # 1. 블록 기본 정보 삽입
        cursor.execute('''
        INSERT INTO blocks (block_index, timestamp, context, importance, hash, prev_hash)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            block_data.get('block_index'),
            block_data.get('timestamp'),
            block_data.get('context'),
            block_data.get('importance', 0.0),
            block_data.get('hash'),
            block_data.get('prev_hash', '')
        ))
        
        block_index = block_data.get('block_index')
        
        # 2. 키워드 삽입
        keywords = block_data.get('keywords', [])
        for keyword in keywords:
            cursor.execute('''
            INSERT OR IGNORE INTO block_keywords (block_index, keyword)
            VALUES (?, ?)
            ''', (block_index, keyword))
        
        # 3. 태그 삽입
        tags = block_data.get('tags', [])
        for tag in tags:
            cursor.execute('''
            INSERT OR IGNORE INTO block_tags (block_index, tag)
            VALUES (?, ?)
            ''', (block_index, tag))
        
        # 4. 메타데이터 삽입
        metadata = block_data.get('metadata', {})
        if metadata:
            cursor.execute('''
            INSERT INTO block_metadata (block_index, metadata)
            VALUES (?, ?)
            ''', (block_index, json.dumps(metadata)))
        
        # 5. 임베딩 저장
        embedding = block_data.get('embedding')
        if embedding:
            # NumPy 배열로 변환 후 바이너리로 저장
            if isinstance(embedding, list):
                embedding_array = np.array(embedding, dtype=np.float32)
            else:
                embedding_array = embedding
                
            cursor.execute('''
            INSERT INTO block_embeddings (block_index, embedding, embedding_model, embedding_dim)
            VALUES (?, ?, ?, ?)
            ''', (
                block_index,
                embedding_array.tobytes(),
                block_data.get('embedding_model', 'default'),
                len(embedding_array)
            ))
        
        conn.commit()
        logger.info(f"Thread-safe 블록 추가 완료: index={block_index}")
        return block_index
    
    def get_block(self, block_index: int) -> Optional[Dict[str, Any]]:
        """
        블록 조회 (Thread-Safe 구현)
        
        Args:
            block_index: 블록 인덱스
            
        Returns:
            블록 데이터 (없으면 None)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        logger.debug(f"Thread-safe 블록 조회 시도: index={block_index}")
        
        # 1. 기본 블록 데이터 조회
        cursor.execute('''
        SELECT * FROM blocks WHERE block_index = ?
        ''', (block_index,))
        
        row = cursor.fetchone()
        if not row:
            logger.warning(f"Thread-safe 블록 조회 실패: index={block_index} 찾을 수 없음")
            return None
            
        # dict로 변환
        if self.db_type == 'sqlite':
            block = dict(row)
        else:
            block = row
        
        # 2. 키워드 조회
        cursor.execute('''
        SELECT keyword FROM block_keywords WHERE block_index = ?
        ''', (block_index,))
        keywords = [row[0] for row in cursor.fetchall()]
        block['keywords'] = keywords
        
        # 3. 태그 조회
        cursor.execute('''
        SELECT tag FROM block_tags WHERE block_index = ?
        ''', (block_index,))
        tags = [row[0] for row in cursor.fetchall()]
        block['tags'] = tags
        
        # 4. 메타데이터 조회
        cursor.execute('''
        SELECT metadata FROM block_metadata WHERE block_index = ?
        ''', (block_index,))
        row = cursor.fetchone()
        if row:
            block['metadata'] = json.loads(row[0])
        else:
            block['metadata'] = {}
        
        # 5. 임베딩 조회
        cursor.execute('''
        SELECT embedding, embedding_dim, embedding_model FROM block_embeddings WHERE block_index = ?
        ''', (block_index,))
        row = cursor.fetchone()
        if row:
            embedding_bytes = row[0]
            embedding_dim = row[1]
            embedding_model = row[2]
            
            # 바이너리에서 NumPy 배열로 변환
            embedding_array = np.frombuffer(embedding_bytes, dtype=np.float32)
            if embedding_dim:
                embedding_array = embedding_array[:embedding_dim]
                
            block['embedding'] = embedding_array.tolist()
            block['embedding_model'] = embedding_model
        
        logger.debug(f"Thread-safe 블록 조회 성공: index={block_index}")
        return block
    
    def get_blocks(self, start_idx: Optional[int] = None, end_idx: Optional[int] = None,
                  limit: int = 100, offset: int = 0,
                  sort_by: str = 'block_index', order: str = 'asc') -> List[Dict[str, Any]]:
        """
        블록 목록 조회 (Thread-Safe 구현)
        
        Args:
            start_idx: 시작 인덱스
            end_idx: 종료 인덱스
            limit: 최대 반환 개수
            offset: 시작 오프셋
            sort_by: 정렬 기준 필드
            order: 정렬 순서
            
        Returns:
            블록 목록
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 유효한 정렬 필드 및 순서인지 확인 (SQL Injection 방지)
        valid_sort_fields = ['block_index', 'timestamp', 'importance']
        if sort_by not in valid_sort_fields:
            sort_by = 'block_index'
        if order.lower() not in ['asc', 'desc']:
            order = 'asc'

        query = "SELECT block_index FROM blocks"
        params = []
        
        if start_idx is not None or end_idx is not None:
            conditions = []
            if start_idx is not None:
                conditions.append("block_index >= ?")
                params.append(start_idx)
            if end_idx is not None:
                conditions.append("block_index <= ?")
                params.append(end_idx)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        query += f" ORDER BY {sort_by} {order.upper()} LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, tuple(params))
        
        blocks = []
        block_indices = [row[0] for row in cursor.fetchall()]
        for block_index in block_indices:
            block = self.get_block(block_index)
            if block:
                blocks.append(block)
        return blocks
    
    def search_blocks_by_keyword(self, keywords: List[str], limit: int = 100) -> List[Dict[str, Any]]:
        """
        키워드로 블록 검색 (Thread-Safe 구현)
        
        Args:
            keywords: 검색할 키워드 목록
            limit: 최대 반환 개수
            
        Returns:
            매칭된 블록 목록
        """
        if not keywords:
            return []
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 각 키워드마다 부분 일치 검색
        block_indices = set()
        for keyword in keywords:
            kw_lower = keyword.lower()
            
            # 키워드 테이블에서 검색
            cursor.execute('''
            SELECT DISTINCT block_index FROM block_keywords 
            WHERE lower(keyword) LIKE ?
            ''', (f'%{kw_lower}%',))
            
            for row in cursor.fetchall():
                block_indices.add(row[0])
            
            # 컨텍스트에서도 검색
            cursor.execute('''
            SELECT block_index FROM blocks 
            WHERE lower(context) LIKE ?
            LIMIT ?
            ''', (f'%{kw_lower}%', limit))
            
            for row in cursor.fetchall():
                block_indices.add(row[0])
        
        # 결과 블록 조회
        blocks = []
        for block_index in block_indices:
            block = self.get_block(block_index)
            if block:
                blocks.append(block)
                
        # 너무 많은 경우 제한
        return blocks[:limit]
    
    def search_blocks_by_embedding(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        임베딩 유사도로 블록 검색 (Thread-Safe 구현)
        
        Args:
            query_embedding: 쿼리 임베딩
            top_k: 상위 k개 결과 반환
            
        Returns:
            유사도 높은 블록 목록
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 모든 임베딩 가져오기
        cursor.execute('''
        SELECT block_index, embedding, embedding_dim FROM block_embeddings
        ''')
        
        query_embedding = np.array(query_embedding, dtype=np.float32)
        blocks_with_similarity = []
        
        for row in cursor.fetchall():
            block_index = row[0]
            embedding_bytes = row[1]
            embedding_dim = row[2]
            
            # 바이너리에서 NumPy 배열로 변환
            block_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
            if embedding_dim:
                block_embedding = block_embedding[:embedding_dim]
            
            # 코사인 유사도 계산
            similarity = np.dot(query_embedding, block_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(block_embedding)
            )
            
            blocks_with_similarity.append((block_index, similarity))
        
        # 유사도 순으로 정렬
        blocks_with_similarity.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 k개 블록 조회
        result_blocks = []
        for block_index, similarity in blocks_with_similarity[:top_k]:
            block = self.get_block(block_index)
            if block:
                block['similarity'] = float(similarity)
                result_blocks.append(block)
        
        return result_blocks
    
    def get_last_block_info(self) -> Optional[Dict[str, Any]]:
        """
        가장 마지막으로 추가된 블록의 인덱스와 해시를 반환 (Thread-Safe 구현)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT block_index, hash FROM blocks 
        ORDER BY block_index DESC 
        LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def filter_blocks_by_importance(self, threshold: float, limit: int = 100, 
                                   sort_by: str = 'importance', order: str = 'desc') -> List[Dict[str, Any]]:
        """
        중요도 기준으로 블록 필터링 및 정렬 (Thread-Safe 구현)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        valid_sort_fields = ['block_index', 'timestamp', 'importance']
        if sort_by not in valid_sort_fields:
            sort_by = 'importance'
        if order.lower() not in ['asc', 'desc']:
            order = 'desc'

        query = f"""
            SELECT block_index 
            FROM blocks 
            WHERE importance >= ? 
            ORDER BY {sort_by} {order.upper()} 
            LIMIT ?
        """
        params = (threshold, limit)
        
        cursor.execute(query, params)
        block_indices = [row[0] for row in cursor.fetchall()]
        
        blocks = []
        for block_index in block_indices:
            block = self.get_block(block_index)
            if block:
                blocks.append(block)
        
        return blocks


# 기능 플래그 기반 DatabaseManager 팩토리
def create_database_manager(connection_string=None, db_type='sqlite'):
    """
    환경 변수에 따라 적절한 DatabaseManager 인스턴스 생성
    
    Returns:
        DatabaseManager: Thread-safe 또는 Legacy DatabaseManager
    """
    thread_safe_enabled = os.getenv('GREEUM_THREAD_SAFE', 'false').lower() == 'true'
    
    if thread_safe_enabled:
        logger.info("Thread-Safe DatabaseManager 생성 - GREEUM_THREAD_SAFE=true")
        return DatabaseManager(connection_string, db_type)
    else:
        # Legacy DatabaseManager 사용 (Phase 3에서 구현)
        logger.info("Legacy DatabaseManager 사용 - GREEUM_THREAD_SAFE=false")
        from .database_manager import DatabaseManager as LegacyDatabaseManager
        return LegacyDatabaseManager(connection_string, db_type)


if __name__ == "__main__":
    # Thread-safe DatabaseManager 호환성 테스트
    import tempfile
    import threading
    
    def test_compatibility():
        """기존 API 호환성 및 thread-safe 기능 테스트"""
        temp_db = tempfile.mktemp(suffix='.db')
        
        # Thread-safe DatabaseManager 인스턴스 생성
        db_manager = DatabaseManager(temp_db)
        
        def worker_thread(thread_id):
            """각 스레드에서 블록 추가 및 조회 테스트"""
            try:
                # 블록 추가
                block_data = {
                    'block_index': thread_id,
                    'timestamp': '2025-08-05T03:00:00',
                    'context': f'Thread {thread_id} test block',
                    'keywords': [f'thread{thread_id}', 'test'],
                    'tags': ['compatibility'],
                    'embedding': [0.1 * thread_id] * 128,
                    'importance': 0.5,
                    'hash': f'hash_{thread_id}',
                    'prev_hash': ''
                }
                
                added_index = db_manager.add_block(block_data)
                print(f"Thread {thread_id}: 블록 추가 성공 - index={added_index}")
                
                # 블록 조회
                retrieved_block = db_manager.get_block(thread_id)
                if retrieved_block:
                    print(f"Thread {thread_id}: 블록 조회 성공 - context='{retrieved_block['context']}'")
                
                # 건강성 검사
                health = db_manager.health_check()
                print(f"Thread {thread_id}: Health check = {health}")
                
            except Exception as e:
                print(f"Thread {thread_id}: 오류 발생 - {e}")
        
        # 5개 스레드로 동시 작업 테스트
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker_thread, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # 최종 상태 확인
        print(f"\n=== 최종 상태 확인 ===")
        all_blocks = db_manager.get_blocks()
        print(f"총 블록 수: {len(all_blocks)}")
        
        db_manager.close()
        os.unlink(temp_db)
        print("Thread-safe 호환성 테스트 완료")
    
    test_compatibility()