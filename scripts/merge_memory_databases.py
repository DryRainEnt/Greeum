#!/usr/bin/env python3
"""
Greeum 메모리 데이터베이스 병합 스크립트
새 경로(~/.greeum) 메모리를 원본(/greeum-global)으로 병합
"""

import sqlite3
import os
import shutil
from datetime import datetime

def merge_memory_databases():
    """메모리 데이터베이스 병합"""
    
    # 경로 설정
    new_db = os.path.expanduser('~/.greeum/universal_memory.db')
    original_db = '/Users/dryrain/greeum-global/memory.db'
    
    print(f"🔍 새 메모리 DB: {new_db}")
    print(f"🔍 원본 메모리 DB: {original_db}")
    
    # 파일 존재 확인
    if not os.path.exists(new_db):
        print(f"❌ 새 DB 파일이 없습니다: {new_db}")
        return False
        
    if not os.path.exists(original_db):
        print(f"❌ 원본 DB 파일이 없습니다: {original_db}")
        return False
    
    # 백업 생성
    backup_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{original_db}.backup_{backup_time}"
    shutil.copy2(original_db, backup_path)
    print(f"✅ 원본 DB 백업: {backup_path}")
    
    try:
        # 새 DB에서 메모리 읽기
        new_conn = sqlite3.connect(new_db)
        new_cursor = new_conn.cursor()
        
        # 새 메모리들 조회 (memories 테이블)
        new_cursor.execute("SELECT * FROM memories ORDER BY id")
        new_memories = new_cursor.fetchall()
        
        print(f"📊 새 경로에서 {len(new_memories)}개 메모리 발견")
        
        if len(new_memories) == 0:
            print("ℹ️  병합할 새 메모리가 없습니다.")
            new_conn.close()
            return True
            
        # 원본 DB 연결
        orig_conn = sqlite3.connect(original_db)
        orig_cursor = orig_conn.cursor()
        
        # 원본 DB의 스키마 확인
        orig_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in orig_cursor.fetchall()]
        print(f"📋 원본 DB 테이블: {tables}")
        
        # long_term_memory 테이블에 삽입
        if 'long_term_memory' in tables:
            # 새 메모리를 원본 형식으로 변환하여 삽입
            for memory in new_memories:
                id_, timestamp, content, keywords, tags, importance, created_at = memory
                
                # long_term_memory 형식으로 변환
                orig_cursor.execute("""
                    INSERT INTO long_term_memory 
                    (timestamp, content, keywords, tags, importance, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (timestamp, content, keywords or '', tags or '', importance, created_at))
                
            orig_conn.commit()
            print(f"✅ {len(new_memories)}개 메모리를 원본 DB에 병합 완료")
            
        else:
            print("❌ 원본 DB에 long_term_memory 테이블이 없습니다")
            return False
            
        # 연결 정리
        new_conn.close()
        orig_conn.close()
        
        # 새 DB 정리 (선택적)
        print(f"🗑️  새 DB 임시 이동: {new_db} -> {new_db}.merged_{backup_time}")
        shutil.move(new_db, f"{new_db}.merged_{backup_time}")
        
        print("🎉 메모리 병합 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 병합 중 오류: {e}")
        return False

if __name__ == "__main__":
    success = merge_memory_databases()
    exit(0 if success else 1)