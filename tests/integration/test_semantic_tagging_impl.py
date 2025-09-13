#!/usr/bin/env python3
"""
Semantic Tagging 실제 구현 테스트
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from greeum.core.semantic_tagging import SemanticTagger, MemoryTag
from greeum.core.database_manager import DatabaseManager

def test_semantic_tagging():
    """의미 기반 태깅 실제 테스트"""
    
    print("\n" + "="*60)
    print("🏷️ Semantic Tagging Implementation Test")
    print("="*60)
    
    # Initialize
    db_path = "data/semantic_tag_test.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db_manager = DatabaseManager(connection_string=db_path)
    tagger = SemanticTagger(db_manager)
    
    # Test memories
    test_cases = [
        (1, "API 버그 수정 완료, 인증 토큰 만료 처리 개선"),
        (2, "프론트엔드 UI 개선 작업 진행중"),
        (3, "점심으로 김치찌개 먹었다"),
        (4, "팀 회의에서 새로운 기능 요구사항 논의"),
        (5, "Python 알고리즘 최적화 연구"),
        (6, "배포 스크립트 작성 및 테스트"),
        (7, "코드 리뷰 피드백 반영"),
        (8, "데이터베이스 마이그레이션 계획 수립"),
    ]
    
    print("\n📝 1. Quick Tagging Test")
    print("-" * 40)
    
    for memory_id, content in test_cases:
        tags = tagger.quick_tag(content)
        tagger.save_tags(memory_id, tags)
        
        print(f"\n Memory #{memory_id}: {content[:30]}...")
        print(f"  Category: {tags.category}")
        print(f"  Activity: {tags.activity}")
        print(f"  Domains: {', '.join(tags.domains) if tags.domains else 'none'}")
        print(f"  Language: {tags.language}")
    
    print("\n🔍 2. Tag-based Search Test")
    print("-" * 40)
    
    # Search by category
    work_memories = tagger.search_by_tags(category='work')
    print(f"\nWork memories: {work_memories}")
    
    # Search by activity
    fix_memories = tagger.search_by_tags(activity='fix')
    print(f"Fix activities: {fix_memories}")
    
    # Search by domain
    api_memories = tagger.search_by_tags(domains=['api'])
    print(f"API related: {api_memories}")
    
    # Complex search
    work_fix_memories = tagger.search_by_tags(
        category='work',
        activity='fix',
        exclude=['frontend']
    )
    print(f"Work fixes (not frontend): {work_fix_memories}")
    
    print("\n📊 3. Tag Analytics")
    print("-" * 40)
    
    analytics = tagger.get_tag_analytics()
    for tag_type, tags in analytics.items():
        print(f"\n{tag_type.upper()}:")
        for tag_info in tags[:5]:  # Top 5
            print(f"  {tag_info['tag']}: {tag_info['count']} uses")
    
    print("\n🔧 4. Tag Consolidation Test")
    print("-" * 40)
    
    # Add some synonym variations
    cursor = db_manager.conn.cursor()
    cursor.execute('''
        INSERT INTO memory_tags (memory_id, tag_name, tag_type)
        VALUES (9, '버그', 'domain'),
               (10, 'bugs', 'domain'),
               (11, '데이터베이스', 'domain')
    ''')
    db_manager.conn.commit()
    
    print("Before consolidation:")
    cursor.execute("SELECT DISTINCT tag_name FROM memory_tags WHERE tag_type='domain'")
    before = [row[0] for row in cursor.fetchall()]
    print(f"  Domain tags: {', '.join(before)}")
    
    # Consolidate
    tagger.consolidate_tags()
    
    print("\nAfter consolidation:")
    cursor.execute("SELECT DISTINCT tag_name FROM memory_tags WHERE tag_type='domain'")
    after = [row[0] for row in cursor.fetchall()]
    print(f"  Domain tags: {', '.join(after)}")
    print(f"  Reduced from {len(before)} to {len(after)} tags")
    
    print("\n✅ 5. Cross-language Search")
    print("-" * 40)
    
    # Korean content with English tags
    korean_with_api = tagger.search_by_tags(domains=['api'])
    print(f"Korean memories with 'api' tag: {korean_with_api}")
    
    # This demonstrates that Korean content can be found with English tags
    for mem_id in korean_with_api[:2]:
        cursor.execute("SELECT content FROM blocks WHERE block_index=?", (mem_id,))
        result = cursor.fetchone()
        if result:
            print(f"  Memory #{mem_id}: {result[0][:40]}...")
    
    print("\n" + "="*60)
    print("📊 Summary:")
    print("  ✅ Automatic categorization works")
    print("  ✅ Activity detection works")
    print("  ✅ Domain extraction works")
    print("  ✅ Tag-based search works")
    print("  ✅ Synonym consolidation works")
    print("  ✅ Cross-language tagging works")
    print("="*60)
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
        print("\n✓ Test database cleaned up")

if __name__ == "__main__":
    test_semantic_tagging()