#!/usr/bin/env python3
"""
Greeum v3.0.0 Migration System
기존 v2.6.4 데이터베이스를 v3.0.0 스키마로 자동 마이그레이션
"""

import os
import sqlite3
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class V300MigrationManager:
    """v2.6.4 → v3.0.0 데이터 마이그레이션 관리자"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.backup_path = f"{db_path}.v264_backup_{int(time.time())}"
        
    def migrate_to_v300(self) -> bool:
        """전체 마이그레이션 프로세스 실행"""
        
        print("\n" + "="*70)
        print("🔄 Greeum v2.6.4 → v3.0.0 Migration")
        print("="*70)
        
        try:
            # 1. 백업 생성
            self._create_backup()
            
            # 2. v3.0.0 스키마 추가
            self._add_v300_schema()
            
            # 3. 기존 데이터 분석
            migration_stats = self._analyze_existing_data()
            
            # 4. 데이터 마이그레이션
            self._migrate_blocks_to_v300(migration_stats)
            
            # 5. 검증
            success = self._verify_migration()
            
            if success:
                print(f"\n✅ 마이그레이션 완료!")
                print(f"   백업: {self.backup_path}")
                print(f"   v3.0.0 기능 사용 준비 완료")
            else:
                print(f"\n❌ 마이그레이션 실패 - 백업에서 복원하세요")
                
            return success
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            print(f"\n❌ 마이그레이션 중 오류: {e}")
            print(f"백업 파일: {self.backup_path}")
            return False
    
    def _create_backup(self):
        """기존 데이터베이스 백업"""
        print(f"\n📦 Creating backup...")
        
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        import shutil
        shutil.copy2(self.db_path, self.backup_path)
        print(f"   ✅ Backup created: {self.backup_path}")
    
    def _add_v300_schema(self):
        """v3.0.0 스키마 추가 (기존 테이블 유지)"""
        print(f"\n🏗️  Adding v3.0.0 schema...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # v3.0.0 새 테이블들 추가
            v300_tables = [
                '''
                CREATE TABLE IF NOT EXISTS contexts (
                    context_id TEXT PRIMARY KEY,
                    trigger TEXT,
                    start_time REAL,
                    end_time REAL,
                    memory_count INTEGER DEFAULT 0,
                    metadata TEXT
                )
                ''',
                '''
                CREATE TABLE IF NOT EXISTS memory_connections (
                    from_memory INTEGER,
                    to_memory INTEGER,
                    weight REAL DEFAULT 0.5,
                    connection_type TEXT,
                    created_at REAL,
                    context_id TEXT,
                    PRIMARY KEY (from_memory, to_memory)
                )
                ''',
                '''
                CREATE TABLE IF NOT EXISTS activation_log (
                    memory_id INTEGER,
                    activation_level REAL,
                    context_id TEXT,
                    timestamp REAL,
                    trigger_memory INTEGER
                )
                ''',
                '''
                CREATE TABLE IF NOT EXISTS tag_definitions (
                    tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag_name TEXT UNIQUE NOT NULL,
                    tag_level INTEGER,
                    usage_count INTEGER DEFAULT 0,
                    last_used REAL,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    is_active INTEGER DEFAULT 1
                )
                ''',
                '''
                CREATE TABLE IF NOT EXISTS memory_tags (
                    memory_id INTEGER,
                    tag_name TEXT,
                    tag_type TEXT,
                    confidence REAL DEFAULT 1.0,
                    added_by TEXT DEFAULT 'migration',
                    added_at REAL DEFAULT (strftime('%s', 'now')),
                    PRIMARY KEY (memory_id, tag_name, tag_type)
                )
                ''',
                '''
                CREATE TABLE IF NOT EXISTS tag_synonyms (
                    synonym TEXT PRIMARY KEY,
                    canonical TEXT NOT NULL
                )
                '''
            ]
            
            for table_sql in v300_tables:
                cursor.execute(table_sql)
            
            conn.commit()
            print(f"   ✅ v3.0.0 schema added")
            
        finally:
            conn.close()
    
    def _analyze_existing_data(self) -> Dict:
        """기존 데이터 분석"""
        print(f"\n📊 Analyzing existing data...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        try:
            # 기존 블록 수
            cursor.execute("SELECT COUNT(*) FROM blocks")
            stats['total_blocks'] = cursor.fetchone()[0]
            
            # 기존 키워드 수
            cursor.execute("SELECT COUNT(*) FROM keywords")
            stats['total_keywords'] = cursor.fetchone()[0]
            
            # 기존 태그 수 (tags 테이블이 있다면)
            try:
                cursor.execute("SELECT COUNT(*) FROM tags")
                stats['total_tags'] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                stats['total_tags'] = 0
            
            # 중요도 분포
            cursor.execute("SELECT AVG(importance), MIN(importance), MAX(importance) FROM blocks")
            row = cursor.fetchone()
            stats['importance'] = {
                'avg': row[0] or 0,
                'min': row[1] or 0,
                'max': row[2] or 0
            }
            
            print(f"   📈 Found {stats['total_blocks']} blocks")
            print(f"   🔤 Found {stats['total_keywords']} keywords")
            print(f"   🏷️  Found {stats['total_tags']} tags")
            print(f"   ⭐ Importance range: {stats['importance']['min']:.1f} - {stats['importance']['max']:.1f}")
            
            return stats
            
        finally:
            conn.close()
    
    def _migrate_blocks_to_v300(self, stats: Dict):
        """기존 블록들을 v3.0.0 컨텍스트 시스템으로 마이그레이션"""
        print(f"\n🔄 Migrating {stats['total_blocks']} blocks to v3.0.0...")
        
        if stats['total_blocks'] == 0:
            print("   ℹ️  No blocks to migrate")
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 1. 기본 컨텍스트 생성
            migration_context_id = f"migration_v264_to_v300_{int(time.time())}"
            cursor.execute('''
                INSERT OR REPLACE INTO contexts (context_id, trigger, start_time, memory_count)
                VALUES (?, ?, ?, ?)
            ''', (migration_context_id, "v2.6.4 migration", time.time(), stats['total_blocks']))
            
            # 2. 기존 블록들 가져오기
            cursor.execute('''
                SELECT block_index, context, importance, timestamp 
                FROM blocks 
                ORDER BY block_index
            ''')
            blocks = cursor.fetchall()
            
            # 3. 연결 생성 (시간 순서대로 연결)
            connections_created = 0
            for i, (block_id, content, importance, timestamp) in enumerate(blocks):
                
                # 기본 태그 생성 (content 기반)
                self._create_basic_tags(cursor, block_id, content, importance)
                
                # 인접한 블록들과 연결 (시간 기반)
                if i > 0:
                    prev_block = blocks[i-1]
                    weight = min(0.8, importance * 0.6)  # 중요도 기반 연결 강도
                    
                    # 양방향 연결
                    cursor.execute('''
                        INSERT OR REPLACE INTO memory_connections
                        (from_memory, to_memory, weight, connection_type, created_at, context_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (block_id, prev_block[0], weight, 'temporal', time.time(), migration_context_id))
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO memory_connections
                        (from_memory, to_memory, weight, connection_type, created_at, context_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (prev_block[0], block_id, weight * 0.7, 'temporal', time.time(), migration_context_id))
                    
                    connections_created += 2
                
                if (i + 1) % 50 == 0:
                    print(f"   📈 Progress: {i+1}/{len(blocks)} blocks processed")
            
            conn.commit()
            print(f"   ✅ Created {connections_created} temporal connections")
            print(f"   ✅ All blocks migrated to v3.0.0 context system")
            
        finally:
            conn.close()
    
    def _create_basic_tags(self, cursor, block_id: int, content: str, importance: float):
        """기존 블록에 기본 태그 생성"""
        
        # 중요도 기반 카테고리
        if importance >= 0.8:
            category = "important"
        elif importance >= 0.5:
            category = "normal"
        else:
            category = "casual"
        
        # 내용 기반 간단한 활동 추론
        content_lower = content.lower()
        if any(word in content_lower for word in ['bug', '버그', 'fix', '수정', 'error', '오류']):
            activity = "fix"
        elif any(word in content_lower for word in ['implement', '구현', 'add', '추가', 'create', '생성']):
            activity = "create"
        elif any(word in content_lower for word in ['test', '테스트', 'check', '확인']):
            activity = "test"
        else:
            activity = "general"
        
        # 태그 저장
        tags = [
            (block_id, category, 'category', 0.9),
            (block_id, activity, 'activity', 0.8),
            (block_id, 'migrated', 'domain', 1.0)
        ]
        
        for memory_id, tag_name, tag_type, confidence in tags:
            cursor.execute('''
                INSERT OR REPLACE INTO memory_tags
                (memory_id, tag_name, tag_type, confidence, added_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (memory_id, tag_name, tag_type, confidence, 'migration'))
    
    def _verify_migration(self) -> bool:
        """마이그레이션 검증"""
        print(f"\n🔍 Verifying migration...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # v3.0.0 테이블 존재 확인
            required_tables = ['contexts', 'memory_connections', 'memory_tags']
            for table in required_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table}: {count} records")
            
            # 기존 데이터 보존 확인
            cursor.execute("SELECT COUNT(*) FROM blocks")
            blocks_count = cursor.fetchone()[0]
            
            # 연결 생성 확인
            cursor.execute("SELECT COUNT(*) FROM memory_connections")
            connections_count = cursor.fetchone()[0]
            
            print(f"   ✅ Original blocks preserved: {blocks_count}")
            print(f"   ✅ New connections created: {connections_count}")
            
            return blocks_count > 0  # 기존 데이터가 보존되었으면 성공
            
        finally:
            conn.close()


def auto_migrate_if_needed(db_path: str) -> bool:
    """필요시 자동 마이그레이션 실행"""
    
    if not os.path.exists(db_path):
        return True  # 새 데이터베이스는 마이그레이션 불필요
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # v3.0.0 테이블들이 있는지 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contexts'")
        has_v300_schema = cursor.fetchone() is not None
        
        # 기존 blocks 테이블이 있는지 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blocks'")
        has_v264_data = cursor.fetchone() is not None
        
        if has_v264_data and not has_v300_schema:
            print(f"\n🔄 v2.6.4 database detected - migration required")
            migrator = V300MigrationManager(db_path)
            return migrator.migrate_to_v300()
        
        return True  # 마이그레이션 불필요 또는 이미 완료
        
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python v300_migration.py <database_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    success = auto_migrate_if_needed(db_path)
    
    if success:
        print("\n✅ Ready for Greeum v3.0.0!")
    else:
        print("\n❌ Migration failed")
        sys.exit(1)