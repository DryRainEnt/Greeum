#!/usr/bin/env python3
"""
시계열 순 메모리 병합 스크립트 (v2.4.0rc3)

블록 인덱스 충돌 방지를 위한 타임스탬프 기반 병합:
1. 두 데이터베이스에서 모든 블록을 timestamp 순으로 조회
2. 새 블록 인덱스를 순차적으로 재할당 
3. 원본 데이터베이스에 시계열 순으로 병합
4. 해시 체인 무결성 유지
"""

import sqlite3
import json
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

def connect_database(db_path: str) -> sqlite3.Connection:
    """데이터베이스 연결"""
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_blocks_chronological(db_path: str) -> List[Dict[str, Any]]:
    """시계열 순으로 모든 블록 조회"""
    conn = connect_database(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT block_index, timestamp, context, importance, hash, prev_hash
        FROM blocks 
        ORDER BY timestamp ASC, block_index ASC
    """)
    
    blocks = []
    for row in cursor.fetchall():
        block = {
            'original_index': row['block_index'],
            'timestamp': row['timestamp'], 
            'context': row['context'],
            'importance': row['importance'],
            'hash': row['hash'],
            'prev_hash': row['prev_hash']
        }
        blocks.append(block)
    
    # 관련 메타데이터도 함께 조회
    for block in blocks:
        block_idx = block['original_index']
        
        # 키워드 조회
        cursor.execute("SELECT keyword FROM block_keywords WHERE block_index = ?", (block_idx,))
        block['keywords'] = [row['keyword'] for row in cursor.fetchall()]
        
        # 태그 조회
        cursor.execute("SELECT tag FROM block_tags WHERE block_index = ?", (block_idx,))
        block['tags'] = [row['tag'] for row in cursor.fetchall()]
        
        # 임베딩 조회 (있는 경우)
        cursor.execute("SELECT embedding, embedding_model, embedding_dim FROM block_embeddings WHERE block_index = ?", (block_idx,))
        embedding_row = cursor.fetchone()
        if embedding_row:
            block['embedding'] = {
                'data': json.loads(embedding_row['embedding']) if embedding_row['embedding'] else None,
                'model': embedding_row['embedding_model'],
                'dimension': embedding_row['embedding_dim']
            }
    
    conn.close()
    print(f"📊 {db_path}에서 {len(blocks)}개 블록 조회 (시계열 순)")
    return blocks

def calculate_hash(block_data: Dict[str, Any], prev_hash: str) -> str:
    """블록 해시 계산 (기존 방식과 동일)"""
    import hashlib
    content = f"{block_data['timestamp']}:{block_data['context']}:{prev_hash}"
    return hashlib.sha256(content.encode()).hexdigest()

def insert_block_with_metadata(conn: sqlite3.Connection, block: Dict[str, Any], new_index: int, new_prev_hash: str) -> str:
    """블록과 메타데이터를 새 인덱스로 삽입"""
    cursor = conn.cursor()
    
    # 새 해시 계산
    new_hash = calculate_hash(block, new_prev_hash)
    
    # 1. 블록 기본 정보 삽입
    cursor.execute("""
        INSERT INTO blocks (block_index, timestamp, context, importance, hash, prev_hash)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (new_index, block['timestamp'], block['context'], block['importance'], new_hash, new_prev_hash))
    
    # 2. 키워드 삽입
    for keyword in block.get('keywords', []):
        cursor.execute("""
            INSERT OR IGNORE INTO block_keywords (block_index, keyword)
            VALUES (?, ?)
        """, (new_index, keyword))
    
    # 3. 태그 삽입
    for tag in block.get('tags', []):
        cursor.execute("""
            INSERT OR IGNORE INTO block_tags (block_index, tag) 
            VALUES (?, ?)
        """, (new_index, tag))
    
    # 4. 임베딩 삽입 (있는 경우)
    if 'embedding' in block and block['embedding']['data']:
        embedding_json = json.dumps(block['embedding']['data'])
        cursor.execute("""
            INSERT INTO block_embeddings (block_index, embedding, embedding_model, embedding_dim)
            VALUES (?, ?, ?, ?)
        """, (
            new_index,
            embedding_json, 
            block['embedding']['model'],
            block['embedding']['dimension']
        ))
    
    return new_hash

def merge_chronological(source_db: str, target_db: str) -> Dict[str, Any]:
    """시계열 순 병합 실행"""
    print("🔄 시계열 순 메모리 병합 시작...")
    
    # 1. 원본과 새 DB에서 모든 블록을 시계열 순으로 조회
    target_blocks = get_all_blocks_chronological(target_db)
    source_blocks = get_all_blocks_chronological(source_db) 
    
    if not source_blocks:
        print("ℹ️  병합할 새 메모리가 없습니다.")
        return {'merged_count': 0, 'total_blocks': len(target_blocks)}
    
    # 2. 백업 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{target_db}.backup_{timestamp}"
    
    import shutil
    shutil.copy2(target_db, backup_path)
    print(f"✅ 원본 DB 백업: {backup_path}")
    
    # 3. 모든 블록을 타임스탬프 순으로 병합
    all_blocks = target_blocks + source_blocks
    all_blocks.sort(key=lambda x: (x['timestamp'], x.get('original_index', 0)))
    
    print(f"📋 전체 {len(all_blocks)}개 블록을 시계열 순으로 정렬")
    
    # 4. 원본 DB 초기화 및 재구축
    conn = connect_database(target_db)
    cursor = conn.cursor()
    
    # 기존 데이터 삭제 (테이블 구조는 유지)
    cursor.execute("DELETE FROM block_embeddings")
    cursor.execute("DELETE FROM block_tags")  
    cursor.execute("DELETE FROM block_keywords")
    cursor.execute("DELETE FROM blocks")
    
    # 5. 시계열 순으로 블록 재삽입
    prev_hash = "genesis"
    inserted_count = 0
    merged_count = 0
    
    for new_index, block in enumerate(all_blocks, 1):
        prev_hash = insert_block_with_metadata(conn, block, new_index, prev_hash)
        inserted_count += 1
        
        # 새로 병합된 블록인지 확인 (source_db에서 온 블록)
        if any(sb['original_index'] == block['original_index'] and 
               sb['timestamp'] == block['timestamp'] for sb in source_blocks):
            merged_count += 1
        
        if inserted_count % 50 == 0:
            print(f"  📝 {inserted_count}/{len(all_blocks)} 블록 처리중...")
    
    conn.commit()
    conn.close()
    
    result = {
        'merged_count': merged_count,
        'total_blocks': len(all_blocks), 
        'source_blocks': len(source_blocks),
        'target_blocks': len(target_blocks),
        'backup_path': backup_path
    }
    
    print(f"""
📊 병합 완료!
  - 🔄 병합된 새 블록: {merged_count}개
  - 📚 기존 블록: {len(target_blocks)}개  
  - 📖 전체 블록: {len(all_blocks)}개
  - 💾 백업 파일: {backup_path}
  - ⏰ 시계열 순 정렬 적용됨
""")
    
    return result

def main():
    """메인 실행 함수"""
    # 경로 설정
    source_db = "/Users/dryrain/.greeum/universal_memory.db"  # 새 메모리가 누적된 DB
    target_db = "/Users/dryrain/greeum-global/memory.db"     # 원본 181개 블록 DB
    
    print("🎯 시계열 순 메모리 병합 스크립트 v2.4.0rc3")
    print(f"📂 소스 DB: {source_db}")
    print(f"📁 타겟 DB: {target_db}")
    
    try:
        result = merge_chronological(source_db, target_db)
        
        print("\n✅ 병합이 성공적으로 완료되었습니다!")
        print("🔄 이제 rc3 버전을 설치하시면 모든 메모리에 정상 접근 가능합니다.")
        
        return result
        
    except Exception as e:
        print(f"❌ 병합 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()