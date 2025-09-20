#!/usr/bin/env python3
"""
Test script for Actant Parser
Tests parsing Korean and English memory text into actant structures
"""

import sys
import pytest
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


pytest.importorskip(
    'greeum.core.actant_parser',
    reason='ActantParser implementation removed in current build',
)

from greeum.core.database_manager import DatabaseManager
from greeum.core.actant_parser import ActantParser

def test_actant_parser():
    """Test actant parser with various inputs"""
    
    print("Testing Actant Parser")
    print("=" * 50)
    
    # Initialize
    db_manager = DatabaseManager(connection_string="data/test_actant.db")
    parser = ActantParser(db_manager)
    
    # Test cases
    test_cases = [
        "사용자가 버그 수정을 요청했다",
        "Claude가 문제를 해결했고 사용자가 만족했다",
        "팀이 새로운 기능을 개발했다",
        "프로젝트가 완료되어 팀이 축하했다",
        "시스템이 오류를 발견했고 개발자가 수정했다",
        "User requested new feature implementation",
        "The team completed the project successfully",
        "버그를 수정한 후 배포를 완료했다"
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{text}'")
        print("-" * 40)
        
        actants = parser.parse(text, memory_id=i)
        
        for j, actant in enumerate(actants, 1):
            print(f"   Actant {j}:")
            print(f"   - Subject: {actant.subject_raw} (hash: {actant.subject_hash})")
            print(f"   - Action: {actant.action_raw} (hash: {actant.action_hash})")
            print(f"   - Object: {actant.object_raw} (hash: {actant.object_hash})")
            if actant.sender_raw:
                print(f"   - Sender: {actant.sender_raw}")
            if actant.receiver_raw:
                print(f"   - Receiver: {actant.receiver_raw}")
            print(f"   - Confidence: {actant.confidence:.2f}")
            
            # Save to database
            parser.save_actant(actant)
    
    # Show statistics
    print("\n" + "=" * 50)
    print("Parser Statistics:")
    stats = parser.get_entity_stats()
    print(f"- Total entities: {stats['total_entities']}")
    print(f"- Total actions: {stats['total_actions']}")
    print(f"- Total actants: {stats['total_actants']}")
    print(f"- Entity types: {stats['entity_types']}")
    print(f"- Action types: {stats['action_types']}")
    
    # Show entity mappings
    print("\nDiscovered Entity Mappings:")
    cursor = db_manager.conn.cursor()
    cursor.execute("SELECT entity_hash, canonical_form, variations FROM actant_entities LIMIT 5")
    for row in cursor.fetchall():
        print(f"- {row['entity_hash']}: {row['canonical_form']} -> {row['variations']}")
    
    print("\nDiscovered Action Mappings:")
    cursor.execute("SELECT action_hash, canonical_form, variations FROM actant_actions LIMIT 5")
    for row in cursor.fetchall():
        print(f"- {row['action_hash']}: {row['canonical_form']} -> {row['variations']}")
    
    # Test entity similarity
    print("\n" + "=" * 50)
    print("Entity Hash Consistency Test:")
    
    # These should produce the same hash
    test_entities = [
        ("사용자", "user", "유저"),
        ("Claude", "claude", "AI"),
        ("팀", "team", "개발팀")
    ]
    
    for entities in test_entities:
        hashes = [parser._get_entity_hash(e, 'subject') for e in entities]
        if len(set(hashes)) == 1:
            print(f"✓ {entities} -> Same hash: {hashes[0]}")
        else:
            print(f"✗ {entities} -> Different hashes: {hashes}")
    
    print("\n" + "=" * 50)
    print("All tests completed!")
    
    # Cleanup
    db_manager.close()
    
    # Remove test database
    if os.path.exists("data/test_actant.db"):
        os.remove("data/test_actant.db")
        print("\nTest database cleaned up")

if __name__ == "__main__":
    test_actant_parser()