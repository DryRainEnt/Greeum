#!/usr/bin/env python3
"""
Create legacy v2.5.2 database for testing AI-powered migration
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import random

def create_legacy_database(db_path: str):
    """Create v2.5.2 legacy database with test data"""
    
    # Remove existing file
    Path(db_path).unlink(missing_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create v2.5.2 legacy schema (WITHOUT actant columns)
    cursor.execute('''
        CREATE TABLE blocks (
            block_index INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            context TEXT NOT NULL,
            importance REAL NOT NULL,
            hash TEXT NOT NULL,
            prev_hash TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE block_embeddings (
            block_index INTEGER PRIMARY KEY,
            embedding BLOB,
            FOREIGN KEY (block_index) REFERENCES blocks (block_index)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE block_metadata (
            block_index INTEGER PRIMARY KEY,
            keywords TEXT,
            tags TEXT,
            metadata TEXT,
            FOREIGN KEY (block_index) REFERENCES blocks (block_index)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE block_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_index INTEGER,
            keyword TEXT,
            FOREIGN KEY (block_index) REFERENCES blocks (block_index)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE block_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_index INTEGER,
            tag TEXT,
            FOREIGN KEY (block_index) REFERENCES blocks (block_index)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE short_term_memories (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            importance REAL NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            ttl_seconds INTEGER
        )
    ''')
    
    # Insert test data - diverse memory contexts for testing AI parsing
    test_memories = [
        {
            "context": "사용자가 새로운 기능 추가를 요청했습니다",
            "importance": 0.8,
            "keywords": ["사용자", "기능", "요청"],
            "tags": ["feature_request", "user_feedback"]
        },
        {
            "context": "Claude가 v2.5.2 버그를 발견하고 수정 방법을 제안했습니다",
            "importance": 0.9,
            "keywords": ["Claude", "버그", "수정"],
            "tags": ["bug_fix", "ai_assistance"]
        },
        {
            "context": "시스템이 자동으로 백업을 생성했습니다",
            "importance": 0.6,
            "keywords": ["시스템", "백업", "자동"],
            "tags": ["system", "backup", "automatic"]
        },
        {
            "context": "개발팀이 마이그레이션 계획을 완료했습니다",
            "importance": 0.85,
            "keywords": ["개발팀", "마이그레이션", "계획"],
            "tags": ["development", "migration", "planning"]
        },
        {
            "context": "테스트 결과 98.9% 성공률을 달성했습니다",
            "importance": 0.7,
            "keywords": ["테스트", "성공률", "결과"],
            "tags": ["testing", "performance", "success"]
        },
        {
            "context": "액탄트 모델 구현을 위한 설계 문서가 작성되었습니다",
            "importance": 0.9,
            "keywords": ["액탄트", "모델", "설계"],
            "tags": ["actant_model", "design", "documentation"]
        },
        {
            "context": "인과관계 분석 엔진 개발이 완료되었습니다",
            "importance": 0.95,
            "keywords": ["인과관계", "분석", "엔진"],
            "tags": ["causality", "analysis", "engine"]
        },
        {
            "context": "메모리 검색 성능이 5배 향상되었습니다",
            "importance": 0.8,
            "keywords": ["메모리", "검색", "성능"],
            "tags": ["memory", "search", "performance"]
        },
        {
            "context": "AI 파서 정확도 테스트에서 87% 성공률 달성",
            "importance": 0.75,
            "keywords": ["AI", "파서", "정확도"],
            "tags": ["ai_parser", "accuracy", "testing"]
        },
        {
            "context": "데이터베이스 스키마 v2.5.3 업그레이드 준비 완료",
            "importance": 0.9,
            "keywords": ["데이터베이스", "스키마", "업그레이드"],
            "tags": ["database", "schema", "upgrade"]
        }
    ]
    
    prev_hash = ""
    
    for i, memory_data in enumerate(test_memories):
        timestamp = (datetime.now() - timedelta(days=10-i)).isoformat()
        
        # Create block hash
        block_data = {
            'block_index': i,
            'timestamp': timestamp,
            'context': memory_data['context'],
            'prev_hash': prev_hash
        }
        
        block_hash = hashlib.sha256(str(block_data).encode()).hexdigest()[:16]
        
        # Insert block
        cursor.execute('''
            INSERT INTO blocks (block_index, timestamp, context, importance, hash, prev_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (i, timestamp, memory_data['context'], memory_data['importance'], block_hash, prev_hash))
        
        # Insert keywords
        for keyword in memory_data['keywords']:
            cursor.execute('''
                INSERT INTO block_keywords (block_index, keyword)
                VALUES (?, ?)
            ''', (i, keyword))
        
        # Insert tags
        for tag in memory_data['tags']:
            cursor.execute('''
                INSERT INTO block_tags (block_index, tag)
                VALUES (?, ?)
            ''', (i, tag))
        
        # Insert metadata
        metadata = {
            "keywords": memory_data['keywords'],
            "tags": memory_data['tags'],
            "test_data": True
        }
        cursor.execute('''
            INSERT INTO block_metadata (block_index, keywords, tags, metadata)
            VALUES (?, ?, ?, ?)
        ''', (i, json.dumps(memory_data['keywords']), json.dumps(memory_data['tags']), json.dumps(metadata)))
        
        prev_hash = block_hash
    
    # Create indexes
    cursor.execute('CREATE INDEX idx_blocks_timestamp ON blocks(timestamp)')
    cursor.execute('CREATE INDEX idx_block_keywords_keyword ON block_keywords(keyword)')
    cursor.execute('CREATE INDEX idx_block_tags_tag ON block_tags(tag)')
    
    conn.commit()
    conn.close()
    
    print(f"✅ Legacy v2.5.2 database created: {db_path}")
    print(f"📊 {len(test_memories)} test memory blocks inserted")
    print("🎯 Ready for AI-powered migration testing!")

if __name__ == "__main__":
    db_path = Path(__file__).parent / "data" / "memory.db"
    db_path.parent.mkdir(exist_ok=True)
    
    create_legacy_database(str(db_path))
    
    print("\n" + "="*50)
    print("🧪 Test Database Summary")
    print("="*50)
    
    # Verify creation
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM blocks")
    block_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM block_keywords")
    keyword_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM block_tags")
    tag_count = cursor.fetchone()[0]
    
    print(f"📊 Blocks: {block_count}")
    print(f"🏷️  Keywords: {keyword_count}")
    print(f"🔖 Tags: {tag_count}")
    
    # Show sample data
    print("\n📝 Sample Memory Contexts:")
    cursor.execute("SELECT block_index, LEFT(context, 80) FROM blocks LIMIT 3")
    for idx, context in cursor.fetchall():
        print(f"  {idx}: {context}...")
    
    conn.close()