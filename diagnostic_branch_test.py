"""
Diagnostic test to understand why local DFS search is failing
로컬 DFS 검색 실패 원인 진단 테스트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from greeum.core.branch_manager import BranchManager
import json

def diagnose_dfs_failure():
    """DFS 검색 실패 원인 진단"""
    
    print("🔍 Diagnosing DFS Local Search Failure...")
    
    # 브랜치 시스템 생성
    branch_system = BranchManager()
    
    # 간단한 테스트 데이터 생성
    test_data = [
        {"content": "user authentication service implementation", "project": "auth-service"},
        {"content": "login endpoint with JWT token generation", "project": "auth-service"},
        {"content": "password validation and encryption", "project": "auth-service"},
        {"content": "user session management", "project": "auth-service"},
        {"content": "auth middleware for protected routes", "project": "auth-service"}
    ]
    
    # 데이터 추가
    print(f"\n📝 Adding {len(test_data)} test blocks...")
    for i, item in enumerate(test_data):
        block = branch_system.add_block(
            content=item['content'],
            root=item['project'],
            slot='A',
            tags={'labels': ['test']},
            importance=0.6
        )
        print(f"   Block {i+1}: {block.id[:8]}... - '{item['content'][:30]}...'")
    
    # 브랜치 상태 확인
    print(f"\n🌳 Branch System State:")
    print(f"   Total blocks: {len(branch_system.blocks)}")
    print(f"   Branches: {list(branch_system.branches.keys())}")
    print(f"   STM slots: {branch_system.stm_slots}")
    
    # 브랜치 구조 상세 확인
    if 'auth-service' in branch_system.branches:
        branch_meta = branch_system.branches['auth-service']
        print(f"   Auth-service branch: size={branch_meta.size}, heads={branch_meta.heads}")
        
        # 브랜치 블록들 확인
        auth_blocks = [block for block in branch_system.blocks.values() if block.root == 'auth-service']
        print(f"   Auth-service blocks: {len(auth_blocks)}")
        
        for i, block in enumerate(auth_blocks):
            print(f"     Block {i}: {block.id[:8]} -> before={block.before[:8] if block.before else None}, after={[a[:8] for a in block.after]}")
    
    # 테스트 쿼리
    test_queries = [
        "authentication",
        "login JWT",
        "password encryption",
        "session management",
        "middleware"
    ]
    
    print(f"\n🔍 Testing DFS Search with queries...")
    
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        
        # 검색 실행
        result = branch_system.search(
            query=query,
            slot='A',
            k=10,
            fallback=True,
            depth=6
        )
        
        print(f"     Results: {len(result.items)} items")
        print(f"     Search type: {result.meta.get('search_type', 'unknown')}")
        print(f"     Hops: {result.meta.get('hops', 0)}")
        print(f"     From cache: {result.meta.get('from_cache', False)}")
        
        # 결과 상세
        for i, item in enumerate(result.items[:3]):  # 상위 3개만
            score = branch_system._calculate_score(query, item, local=True)
            print(f"       {i+1}. {item.content['text'][:40]}... (score: {score:.3f})")
    
    # 직접 DFS 호출 테스트
    print(f"\n🔧 Direct DFS Test...")
    
    head_id = branch_system.stm_slots['A']
    if head_id:
        print(f"   Starting from head: {head_id[:8]}...")
        
        results, hops = branch_system._dfs_search(
            start_id=head_id,
            query="authentication",
            max_depth=6,
            k=20
        )
        
        print(f"   DFS Results: {len(results)} blocks, {hops} hops")
        
        for i, block in enumerate(results[:5]):
            score = branch_system._calculate_score("authentication", block, local=True)
            print(f"     {i+1}. {block.content['text'][:40]}... (score: {score:.3f})")
    else:
        print("   No head found in slot A!")
    
    # 스코어 계산 상세 테스트
    print(f"\n🧮 Score Calculation Test...")
    
    if auth_blocks:
        test_block = auth_blocks[0]
        test_query = "authentication"
        
        score = branch_system._calculate_score(test_query, test_block, local=True)
        print(f"   Query: '{test_query}'")
        print(f"   Block: '{test_block.content['text']}'")
        print(f"   Final Score: {score:.6f}")
        print(f"   Min Threshold: {branch_system.MIN_SIMILARITY_SCORE}")
        print(f"   Similarity Threshold: {branch_system.SIMILARITY_THRESHOLD}")
        
        # 스코어 구성 요소 분해
        query_words = set(test_query.lower().split())
        block_text = test_block.content.get('text', '').lower()
        block_words = set(block_text.split())
        
        intersection = len(query_words & block_words)
        union = len(query_words | block_words)
        cos_sim = intersection / union if union > 0 else 0.0
        
        print(f"   Query words: {query_words}")
        print(f"   Block words: {block_words}")
        print(f"   Intersection: {intersection}")
        print(f"   Union: {union}")
        print(f"   Jaccard similarity: {cos_sim:.6f}")
        
        exact_matches = sum(1 for word in query_words if word in block_text)
        print(f"   Exact matches: {exact_matches}")
    
    print(f"\n✅ Diagnosis Complete!")

if __name__ == "__main__":
    diagnose_dfs_failure()