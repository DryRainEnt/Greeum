#!/usr/bin/env python3
"""
Migrate local database to global database
로컬 프로젝트 DB를 글로벌 DB로 마이그레이션하는 스크립트
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

def migrate_database():
    """로컬 DB를 글로벌 DB로 마이그레이션"""

    # 경로 설정
    local_db = Path("./data/memory.db")
    global_db = Path.home() / ".greeum" / "memory.db"

    print(f"=== Greeum Database Migration ===")
    print(f"Source: {local_db}")
    print(f"Target: {global_db}")
    print()

    # 로컬 DB 존재 확인
    if not local_db.exists():
        print(f"❌ Local database not found: {local_db}")
        return False

    # 글로벌 디렉토리 생성
    global_db.parent.mkdir(parents=True, exist_ok=True)

    # 백업 생성
    if global_db.exists():
        backup_path = global_db.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        print(f"📦 Creating backup: {backup_path}")
        shutil.copy2(global_db, backup_path)

    # 데이터베이스 연결
    local_conn = sqlite3.connect(local_db)
    global_conn = sqlite3.connect(global_db)

    try:
        local_cursor = local_conn.cursor()
        global_cursor = global_conn.cursor()

        # 로컬 DB 통계
        local_cursor.execute("SELECT COUNT(*) FROM blocks")
        local_count = local_cursor.fetchone()[0]
        print(f"📊 Local database: {local_count} blocks")

        # 글로벌 DB 통계
        global_cursor.execute("SELECT COUNT(*) FROM blocks")
        global_count = global_cursor.fetchone()[0]
        print(f"📊 Global database: {global_count} blocks")

        if local_count == 0:
            print("⚠️  No blocks to migrate")
            return True

        # 스키마 확인 및 생성
        local_cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='blocks'")
        schema = local_cursor.fetchone()[0]

        # 테이블이 없으면 생성
        global_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blocks'")
        if not global_cursor.fetchone():
            print("📝 Creating blocks table in global database...")
            global_cursor.execute(schema)

        # 모든 관련 테이블 마이그레이션
        tables = ['blocks', 'block_embeddings', 'stm_slots', 'anchors', 'usage_metrics',
                 'temporal_memories', 'duplicate_hashes', 'memory_evolution']

        for table in tables:
            # 테이블 존재 확인
            local_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not local_cursor.fetchone():
                continue

            print(f"\n🔄 Migrating table: {table}")

            # 스키마 복사
            local_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
            schema_row = local_cursor.fetchone()
            if schema_row:
                schema = schema_row[0]
                global_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not global_cursor.fetchone():
                    global_cursor.execute(schema)

            # 데이터 카운트
            local_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = local_cursor.fetchone()[0]

            if count == 0:
                print(f"  ⚠️  No data in {table}")
                continue

            # 데이터 복사
            local_cursor.execute(f"SELECT * FROM {table}")
            rows = local_cursor.fetchall()

            # 컬럼 정보 가져오기
            local_cursor.execute(f"PRAGMA table_info({table})")
            columns = [col[1] for col in local_cursor.fetchall()]
            placeholders = ','.join(['?' for _ in columns])

            # 글로벌 DB에 삽입 (REPLACE 사용하여 중복 처리)
            insert_query = f"INSERT OR REPLACE INTO {table} ({','.join(columns)}) VALUES ({placeholders})"

            migrated = 0
            for row in rows:
                try:
                    global_cursor.execute(insert_query, row)
                    migrated += 1
                except sqlite3.IntegrityError as e:
                    print(f"  ⚠️  Skipping duplicate: {e}")

            print(f"  ✅ Migrated {migrated}/{count} rows")

        # 인덱스 복사
        print("\n🔧 Creating indexes...")
        local_cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        indexes = local_cursor.fetchall()
        for index in indexes:
            try:
                global_cursor.execute(index[0])
            except sqlite3.OperationalError:
                pass  # 이미 존재하는 인덱스

        # 커밋
        global_conn.commit()

        # 최종 확인
        global_cursor.execute("SELECT COUNT(*) FROM blocks")
        final_count = global_cursor.fetchone()[0]
        print(f"\n✅ Migration complete! Global database now has {final_count} blocks")

        # 로컬 DB 이름 변경 (삭제 대신 보관)
        migrated_path = local_db.with_suffix(".migrated.db")
        print(f"\n📦 Renaming local database to: {migrated_path}")
        local_conn.close()
        global_conn.close()
        shutil.move(local_db, migrated_path)

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        local_conn.close()
        global_conn.close()

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)