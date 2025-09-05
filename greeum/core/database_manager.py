import os
import sqlite3
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """데이터베이스 연결 및 관리 클래스"""
    
    def __init__(self, connection_string=None, db_type='sqlite'):
        """
        데이터베이스 관리자 초기화
        
        Args:
            connection_string: 데이터베이스 연결 문자열 (기본값: data/memory.db)
            db_type: 데이터베이스 타입 (sqlite, postgres 등)
        """
        self.db_type = db_type
        
        # Smart Database Path Detection (옵션 3)
        if connection_string:
            self.connection_string = connection_string
        else:
            self.connection_string = self._get_smart_db_path()
        self._ensure_data_dir()
        self._setup_connection()
        self._create_schemas()
        logger.info(f"DatabaseManager 초기화 완료: {self.connection_string} (type: {self.db_type})")
    
    def _get_smart_db_path(self) -> str:
        """
        지능형 데이터베이스 경로 감지
        
        우선순위:
        1. GREEUM_DATA_DIR 환경변수 (명시적 설정)
        2. 현재 디렉토리의 data/memory.db (프로젝트 로컬)
        3. ~/greeum-global/data/memory.db (글로벌 폴백)
        
        Returns:
            str: 최적의 데이터베이스 파일 경로
        """
        # 1. 환경변수 우선 (명시적 설정)
        if 'GREEUM_DATA_DIR' in os.environ:
            env_path = os.path.join(os.environ['GREEUM_DATA_DIR'], 'data', 'memory.db')
            logger.info(f"📁 Using environment variable path: {env_path}")
            return env_path
        
        # 2. 현재 디렉토리에 기존 데이터베이스 존재하면 사용 (프로젝트 로컬)
        current_dir = os.getcwd()
        local_db_path = os.path.join(current_dir, 'data', 'memory.db')
        
        if os.path.exists(local_db_path):
            logger.info(f"📂 Found existing local database: {local_db_path}")
            return local_db_path
        
        # 3. 현재 디렉토리에 data 폴더가 있으면 사용 (새 프로젝트)
        data_dir_path = os.path.join(current_dir, 'data')
        if os.path.exists(data_dir_path) and os.path.isdir(data_dir_path):
            new_local_path = os.path.join(data_dir_path, 'memory.db')
            logger.info(f"📁 Using local data directory: {new_local_path}")
            return new_local_path
        
        # 4. 글로벌 디렉토리 폴백
        home_dir = os.path.expanduser('~')
        global_db_path = os.path.join(home_dir, 'greeum-global', 'data', 'memory.db')
        logger.info(f"🌐 Using global fallback path: {global_db_path}")
        return global_db_path
    
    def _ensure_data_dir(self):
        """데이터 디렉토리 존재 확인"""
        data_dir = os.path.dirname(self.connection_string)
        if data_dir:
            os.makedirs(data_dir, exist_ok=True)
    
    def _setup_connection(self):
        """데이터베이스 연결 설정"""
        if self.db_type == 'sqlite':
            self.conn = sqlite3.connect(self.connection_string)
            self.conn.row_factory = sqlite3.Row
        elif self.db_type == 'postgres':
            try:
                import psycopg2
                from psycopg2.extras import RealDictCursor
                self.conn = psycopg2.connect(self.connection_string)
                self.conn.cursor_factory = RealDictCursor
            except ImportError:
                raise ImportError("PostgreSQL 지원을 위해 psycopg2를 설치하세요.")
        else:
            raise ValueError(f"지원하지 않는 데이터베이스 타입: {self.db_type}")
    
    def _create_schemas(self):
        """필요한 테이블 생성"""
        cursor = self.conn.cursor()
        
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
        
        # 인덱스 생성
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocks_timestamp ON blocks(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_block_keywords ON block_keywords(keyword)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_block_tags ON block_tags(tag)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stm_timestamp ON short_term_memories(timestamp)')
        
        self.conn.commit()
    
    def add_block(self, block_data: Dict[str, Any]) -> int:
        """
        새 블록 추가
        
        Args:
            block_data: 블록 데이터
            
        Returns:
            추가된 블록의 인덱스
        """
        cursor = self.conn.cursor()
        logger.debug(f"새 블록 추가 시도: index={block_data.get('block_index')}")
        
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
        
        self.conn.commit()
        logger.info(f"Block added successfully: index={block_index}")
        return block_index
    
    def get_block(self, block_index: int) -> Optional[Dict[str, Any]]:
        """
        블록 조회
        
        Args:
            block_index: 블록 인덱스
            
        Returns:
            블록 데이터 (없으면 None)
        """
        cursor = self.conn.cursor()
        logger.debug(f"Attempting to retrieve block: index={block_index}")
        
        # 1. 기본 블록 데이터 조회
        cursor.execute('''
        SELECT * FROM blocks WHERE block_index = ?
        ''', (block_index,))
        
        row = cursor.fetchone()
        if not row:
            logger.warning(f"Block retrieval failed: index={block_index} not found")
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
        
        logger.debug(f"블록 조회 성공: index={block_index}")
        return block
    
    def get_blocks(self, start_idx: Optional[int] = None, end_idx: Optional[int] = None,
                  limit: int = 100, offset: int = 0,
                  sort_by: str = 'block_index', order: str = 'asc') -> List[Dict[str, Any]]:
        """
        블록 목록 조회
        
        Args:
            start_idx: 시작 인덱스
            end_idx: 종료 인덱스
            limit: 최대 반환 개수
            offset: 시작 오프셋
            sort_by: 정렬 기준 필드 (예: 'block_index', 'timestamp', 'importance')
            order: 정렬 순서 ('asc' 또는 'desc')
            
        Returns:
            블록 목록
        """
        cursor = self.conn.cursor()
        
        # 유효한 정렬 필드 및 순서인지 확인 (SQL Injection 방지)
        valid_sort_fields = ['block_index', 'timestamp', 'importance']
        if sort_by not in valid_sort_fields:
            sort_by = 'block_index' # 기본값
        if order.lower() not in ['asc', 'desc']:
            order = 'asc' # 기본값

        if sort_by == 'importance':
            # JOIN 없이 importance로 정렬된 block_index를 가져오려면 blocks 테이블에 직접 접근
            query = "SELECT block_index FROM blocks"
            params_build = [] # 임시 파라미터 리스트
            conditions = []
            if start_idx is not None:
                conditions.append("block_index >= ?")
                params_build.append(start_idx)
            if end_idx is not None:
                conditions.append("block_index <= ?")
                params_build.append(end_idx)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDER BY importance {order.upper()} LIMIT ? OFFSET ?"
            params_build.extend([limit, offset])
            params = params_build

        else:
            query = "SELECT block_index FROM blocks"
            params = [] # params 초기화 위치 변경
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
        키워드로 블록 검색
        
        Args:
            keywords: 검색할 키워드 목록
            limit: 최대 반환 개수
            
        Returns:
            매칭된 블록 목록
        """
        if not keywords:
            return []
            
        cursor = self.conn.cursor()
        
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
        임베딩 유사도로 블록 검색
        
        Args:
            query_embedding: 쿼리 임베딩
            top_k: 상위 k개 결과 반환
            
        Returns:
            유사도 높은 블록 목록
        """
        cursor = self.conn.cursor()
        
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
    
    def search_blocks_by_date_range(self, start_date, end_date, limit: int = 100) -> List[Dict[str, Any]]:
        """
        날짜 범위로 블록 검색
        
        Args:
            start_date: 시작 날짜 (ISO 형식 문자열 또는 datetime 객체)
            end_date: 종료 날짜 (ISO 형식 문자열 또는 datetime 객체)
            limit: 최대 반환 개수
            
        Returns:
            날짜 범위 내 블록 목록
        """
        # datetime 객체를 ISO 문자열로 변환
        if hasattr(start_date, 'isoformat'):
            start_date = start_date.isoformat()
        if hasattr(end_date, 'isoformat'):
            end_date = end_date.isoformat()
            
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT block_index FROM blocks
        WHERE timestamp >= ? AND timestamp <= ?
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (start_date, end_date, limit))
        
        blocks = []
        for row in cursor.fetchall():
            block_index = row[0]
            block = self.get_block(block_index)
            if block:
                blocks.append(block)
                
        return blocks
    
    def add_short_term_memory(self, memory_data: Dict[str, Any]) -> str:
        """
        단기 기억 추가
        
        Args:
            memory_data: 기억 데이터 (id, timestamp, content, speaker, metadata 포함)
            
        Returns:
            추가된 기억의 ID
        """
        cursor = self.conn.cursor()
        
        memory_id = memory_data.get('id')
        timestamp = memory_data.get('timestamp')
        content = memory_data.get('content')
        speaker = memory_data.get('speaker')
        metadata = memory_data.get('metadata', {})
        
        cursor.execute('''
        INSERT OR REPLACE INTO short_term_memories (id, timestamp, content, speaker, metadata)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            memory_id,
            timestamp,
            content,
            speaker,
            json.dumps(metadata) if metadata else '{}'
        ))
        
        self.conn.commit()
        return memory_id
    
    def get_recent_short_term_memories(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        최근 단기 기억 조회
        
        Args:
            count: 반환할 기억 개수
            
        Returns:
            최근 단기 기억 목록
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT id, timestamp, content, speaker, metadata
        FROM short_term_memories
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (count,))
        
        memories = []
        for row in cursor.fetchall():
            if self.db_type == 'sqlite':
                memory = dict(row)
            else:
                memory = row
                
            # 메타데이터 JSON 파싱
            if 'metadata' in memory and memory['metadata']:
                memory['metadata'] = json.loads(memory['metadata'])
                
            memories.append(memory)
            
        return memories
    
    def delete_expired_short_term_memories(self, ttl_seconds: int) -> int:
        """
        만료된 단기 기억 삭제
        
        Args:
            ttl_seconds: 유효 기간 (초)
            
        Returns:
            삭제된 기억 개수
        """
        import datetime
        
        # 현재 시간에서 TTL을 뺀 값보다 이전 타임스탬프 삭제
        cutoff_time = (datetime.datetime.now() - 
                      datetime.timedelta(seconds=ttl_seconds)).isoformat()
        
        cursor = self.conn.cursor()
        
        cursor.execute('''
        DELETE FROM short_term_memories
        WHERE timestamp < ?
        ''', (cutoff_time,))
        
        deleted_count = cursor.rowcount
        self.conn.commit()
        
        return deleted_count
    
    def clear_short_term_memories(self) -> int:
        """
        모든 단기 기억 삭제
        
        Returns:
            삭제된 기억 개수
        """
        cursor = self.conn.cursor()
        
        cursor.execute('DELETE FROM short_term_memories')
        
        deleted_count = cursor.rowcount
        self.conn.commit()
        
        return deleted_count
    
    def migrate_from_jsonl(self, block_file_path: str) -> int:
        """
        JSONL 파일에서 데이터베이스로 기존 블록 데이터 이전
        
        Args:
            block_file_path: 블록 JSONL 파일 경로
            
        Returns:
            이전된 블록 개수
        """
        import json
        
        if not os.path.exists(block_file_path):
            logger.warning(f"JSONL 마이그레이션 건너뜀: 파일 없음 - {block_file_path}")
            return 0
        logger.info(f"JSONL 파일 마이그레이션 시작: {block_file_path}")
            
        migrated_count = 0
        with open(block_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    block_data = json.loads(line)
                    self.add_block(block_data)
                    migrated_count += 1
                except json.JSONDecodeError:
                    continue
                    
        logger.info(f"JSONL 파일 마이그레이션 완료: {migrated_count}개 블록 이전됨")
        return migrated_count
    
    def close(self):
        """데이터베이스 연결 종료"""
        if self.conn:
            self.conn.close()
            logger.info(f"데이터베이스 연결 종료: {self.connection_string}")

    def get_short_term_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        ID로 단기 기억 조회

        Args:
            memory_id: 조회할 단기 기억의 ID

        Returns:
            단기 기억 데이터 (없으면 None)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT id, timestamp, content, speaker, metadata 
        FROM short_term_memories 
        WHERE id = ?
        """, (memory_id,))

        row = cursor.fetchone()
        if not row:
            return None
        
        memory = dict(row)
        if 'metadata' in memory and memory['metadata']:
            try:
                memory['metadata'] = json.loads(memory['metadata'])
            except json.JSONDecodeError:
                memory['metadata'] = {} # 파싱 실패 시 빈 객체
        return memory

    def get_last_block_info(self) -> Optional[Dict[str, Any]]:
        """
        가장 마지막으로 추가된 블록의 인덱스와 해시를 반환합니다.
        블록이 없을 경우 None을 반환합니다.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT block_index, hash FROM blocks 
        ORDER BY block_index DESC 
        LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            return dict(row) # {'block_index': ..., 'hash': ...}
        return None

    def filter_blocks_by_importance(self, threshold: float, limit: int = 100, 
                                   sort_by: str = 'importance', order: str = 'desc') -> List[Dict[str, Any]]:
        """
        중요도 기준으로 블록 필터링 및 정렬

        Args:
            threshold: 중요도 최소값
            limit: 반환할 최대 블록 수
            sort_by: 정렬 기준 필드
            order: 정렬 순서

        Returns:
            필터링 및 정렬된 블록 목록
        """
        cursor = self.conn.cursor()

        valid_sort_fields = ['block_index', 'timestamp', 'importance']
        if sort_by not in valid_sort_fields:
            sort_by = 'importance'
        if order.lower() not in ['asc', 'desc']:
            order = 'desc'

        # importance 필드로 필터링하고, 지정된 기준으로 정렬하여 block_index 목록을 가져옴
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
            block = self.get_block(block_index) # N+1 문제가 발생할 수 있음
            if block:
                blocks.append(block)
        
        return blocks
    
    def count_blocks(self) -> int:
        """
        전체 블록 개수 조회
        
        Returns:
            int: 전체 블록 개수
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM blocks")
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Failed to count blocks: {e}")
            return 0
    
    def get_recent_blocks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        최근 블록들 조회
        
        Args:
            limit: 조회할 블록 개수 (기본값: 10)
            
        Returns:
            List[Dict[str, Any]]: 최근 블록들의 리스트
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT block_index, timestamp, context, importance, hash, prev_hash
                FROM blocks 
                ORDER BY block_index DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            blocks = []
            
            for row in rows:
                block = {
                    'block_index': row[0],
                    'timestamp': row[1],
                    'context': row[2],
                    'keywords': [],  # 스키마에 없으므로 빈 리스트
                    'tags': [],      # 스키마에 없으므로 빈 리스트
                    'embedding': [], # 스키마에 없으므로 빈 리스트
                    'importance': row[3],
                    'hash': row[4],
                    'prev_hash': row[5]
                }
                blocks.append(block)
            
            return blocks
        except Exception as e:
            logger.error(f"Failed to get recent blocks: {e}")
            return []

    def health_check(self) -> bool:
        """
        데이터베이스 상태 및 무결성 검사
        
        Returns:
            bool: 데이터베이스가 정상 상태이면 True
        """
        import time
        
        try:
            cursor = self.conn.cursor()
            
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
            
            self.conn.commit()
            logger.info("Database health check passed")
            return True
        
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def update_block_metadata(self, block_index: int, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a specific block (M2 Implementation).
        
        Args:
            block_index: Block index to update
            metadata: New metadata dictionary
            
        Returns:
            bool: True if update successful
        """
        try:
            cursor = self.conn.cursor()
            
            # Update blocks table metadata column if it exists
            cursor.execute("PRAGMA table_info(blocks)")
            columns = {row[1] for row in cursor.fetchall()}
            
            if 'metadata' in columns:
                # Update metadata column in blocks table
                cursor.execute('''
                UPDATE blocks SET metadata = ? WHERE block_index = ?
                ''', (json.dumps(metadata), block_index))
            
            # Update/insert into block_metadata table (using existing schema)
            cursor.execute('''
            INSERT OR REPLACE INTO block_metadata (block_index, metadata)
            VALUES (?, ?)
            ''', (block_index, json.dumps(metadata)))
            
            self.conn.commit()
            logger.debug(f"Updated metadata for block {block_index}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metadata for block {block_index}: {e}")
            return False
    
    def get_block_by_index(self, block_index: int) -> Optional[Dict[str, Any]]:
        """
        Get block by index (alias for get_block for compatibility).
        """
        return self.get_block(block_index)
    
    def get_block_embedding(self, block_index: int) -> Optional[Dict[str, Any]]:
        """
        Get embedding data for a specific block.
        
        Args:
            block_index: Block index
            
        Returns:
            Dict with embedding data or None if not found
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT embedding, embedding_model, embedding_dim 
            FROM block_embeddings 
            WHERE block_index = ?
            ''', (block_index,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Convert binary embedding back to numpy array
            embedding_bytes = row[0]
            embedding_array = np.frombuffer(embedding_bytes, dtype=np.float32)
            
            return {
                'embedding': embedding_array.tolist(),
                'embedding_model': row[1],
                'embedding_dim': row[2]
            }
            
        except Exception as e:
            logger.debug(f"Failed to get embedding for block {block_index}: {e}")
            return None 