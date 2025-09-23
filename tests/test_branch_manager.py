"""
Branch Manager Test Suite
브랜치 기반 메모리 시스템 테스트
"""

import unittest
import time
import uuid
from typing import List, Dict, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from greeum.core.branch_manager import BranchManager, BranchBlock, BranchMeta, SearchResult
from greeum.core.branch_global_index import GlobalIndex


class TestBranchManager(unittest.TestCase):
    """BranchManager 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.manager = BranchManager()
        
    def test_add_block_creates_new_branch(self):
        """새 브랜치 생성 테스트"""
        # 첫 블록 추가
        block = self.manager.add_block(
            content="프로젝트 시작",
            root="project-1",
            tags={"actants": {"subject": "user", "action": "start", "object": "project"}}
        )
        
        self.assertIsNotNone(block)
        self.assertEqual(block.root, "project-1")
        self.assertIsNone(block.before)  # 첫 블록이므로 부모 없음
        self.assertEqual(len(block.after), 0)  # 아직 자식 없음
        
        # 브랜치 메타 확인
        self.assertIn("project-1", self.manager.branches)
        branch_meta = self.manager.branches["project-1"]
        self.assertEqual(branch_meta.size, 1)
        self.assertEqual(branch_meta.heads["A"], block.id)  # 기본 슬롯 A
        
    def test_add_block_continues_branch(self):
        """브랜치 연속 추가 테스트"""
        # 첫 블록
        block1 = self.manager.add_block(
            content="작업 시작",
            root="project-1"
        )
        
        # 두번째 블록 (이어서 추가)
        block2 = self.manager.add_block(
            content="작업 진행중",
            slot="A"  # 같은 슬롯
        )
        
        self.assertEqual(block2.root, block1.root)  # 같은 루트
        self.assertEqual(block2.before, block1.id)  # block1이 부모
        self.assertIn(block2.id, self.manager.blocks[block1.id].after)  # block1의 자식
        
        # 브랜치 메타 업데이트 확인
        branch_meta = self.manager.branches["project-1"]
        self.assertEqual(branch_meta.size, 2)
        self.assertEqual(branch_meta.heads["A"], block2.id)  # 헤드 이동
        
    def test_dfs_local_search_hits(self):
        """DFS 로컬 검색 히트 테스트 - 브랜치 구조에서"""
        # 실제 사용 시나리오: 메인 작업과 버그 수정 브랜치
        # 메인 작업 진행
        blocks = []
        for i in range(3):
            block = self.manager.add_block(
                content=f"기능 {i} 구현",
                root="project-1",
                slot="A"
            )
            blocks.append(block)
            
        # 버그 발견 후 브랜치 생성 (블록1에서)
        self.manager.stm_slots['A'] = blocks[1].id  # 블록1로 이동
        
        # 버그 수정 브랜치
        bug_fixes = []
        for i in range(3):
            block = self.manager.add_block(
                content=f"에러 수정 {i}",
                root="project-1",
                slot="A"
            )
            bug_fixes.append(block)
            
        # 현재 STM은 버그 수정 브랜치의 마지막을 가리킴
        # "에러" 검색 (depth=3으로 버그 브랜치 내에서만 검색)
        result = self.manager.search(
            query="에러",
            slot="A",
            depth=3,
            k=5
        )
        
        self.assertIsInstance(result, SearchResult)
        self.assertGreater(len(result.items), 0)
        
        # 검색된 블록들이 버그 수정 브랜치의 블록들인지 확인
        for block in result.items:
            # 모든 결과가 "에러 수정"을 포함해야 함
            self.assertIn("에러 수정", block.content['text'])
            
        # 메인 라인 블록들은 검색되지 않아야 함
        has_main = any("기능" in b.content['text'] and "에러" not in b.content['text'] 
                      for b in result.items)
        self.assertFalse(has_main, "메인 라인 블록이 검색되지 않아야 함")
            
    def test_dfs_depth_limit(self):
        """DFS 깊이 제한 테스트 - 브랜치 구조에서"""
        # 실제 사용 시나리오: 브랜치가 있는 구조 생성
        # 메인 라인 생성
        main_blocks = []
        for i in range(5):
            block = self.manager.add_block(
                content=f"메인 {i}",
                root="deep-branch",
                slot="A"
            )
            main_blocks.append(block)
            
        # 중간 지점(블록2)에서 브랜치 생성
        # STM을 블록2로 이동 (과거 노드 선택)
        self.manager.stm_slots['A'] = main_blocks[2].id
        
        # 브랜치 생성 (5개 깊이)
        branch_blocks = []
        for i in range(5):
            block = self.manager.add_block(
                content=f"브랜치 {i}",
                root="deep-branch",
                slot="A"
            )
            branch_blocks.append(block)
            
        # 현재 STM은 브랜치4를 가리킴
        # depth=2로 검색하면 브랜치4, 브랜치3, 브랜치2까지만 접근 가능
        result = self.manager.search(
            query="메인",  # 메인 라인 검색
            slot="A",
            depth=2,  # 깊이 제한
            k=10
        )
        
        # 메인 라인 블록들이 검색되지 않아야 함 (브랜치에서 depth=2로는 도달 불가)
        found_main = any("메인" in b.content['text'] for b in result.items)
        self.assertFalse(found_main, "depth=2로는 브랜치에서 메인 라인에 도달할 수 없어야 함")
        
        # 브랜치 블록만 검색되어야 함
        all_branch = all("브랜치" in b.content['text'] for b in result.items)
        self.assertTrue(all_branch, "브랜치 블록만 검색되어야 함")
        
        # 메타데이터 확인
        self.assertLessEqual(result.meta['depth_used'], 2)
        
    def test_stm_slot_management(self):
        """STM 슬롯 관리 테스트"""
        # 슬롯 A에 블록 추가
        block_a = self.manager.add_block(content="슬롯 A 작업", slot="A", root="root-a")
        
        # 슬롯 B에 블록 추가
        block_b = self.manager.add_block(content="슬롯 B 작업", slot="B", root="root-b")
        
        # 슬롯 C에 블록 추가
        block_c = self.manager.add_block(content="슬롯 C 작업", slot="C", root="root-c")
        
        # 각 슬롯 헤드 확인
        self.assertEqual(self.manager.stm_slots["A"], block_a.id)
        self.assertEqual(self.manager.stm_slots["B"], block_b.id)
        self.assertEqual(self.manager.stm_slots["C"], block_c.id)
        
        # 서로 다른 브랜치 확인
        self.assertNotEqual(block_a.root, block_b.root)
        self.assertNotEqual(block_b.root, block_c.root)
        
    def test_score_calculation(self):
        """스코어 계산 테스트"""
        # 테스트용 블록 생성
        recent_block = BranchBlock(
            id="recent",
            root="test",
            before=None,
            content={'text': "최근 에러 수정 작업"},
            stats={'visit': 0}
        )
        
        old_block = BranchBlock(
            id="old",
            root="test",
            before=None,
            content={'text': "오래된 에러 수정 작업"},
            stats={'visit': 10},
            created_at=time.time() - 30 * 24 * 3600  # 30일 전
        )
        
        # 스코어 계산
        recent_score = self.manager._calculate_score("에러 수정", recent_block, local=True)
        old_score = self.manager._calculate_score("에러 수정", old_block, local=True)
        
        # 최근 블록이 더 높은 스코어를 가져야 함
        self.assertGreater(recent_score, old_score)
        
    def test_metrics_tracking(self):
        """메트릭 추적 테스트"""
        # 여러 검색 수행
        for i in range(5):
            self.manager.add_block(content=f"테스트 {i}", root="test-root")
            
        for _ in range(3):
            self.manager.search("테스트", k=2)
            
        metrics = self.manager.get_metrics()

        self.assertEqual(metrics['total_searches'], 3)
        self.assertGreaterEqual(metrics['avg_hops'], 0)
        self.assertIn('local_hit_rate', metrics)
        

class TestGlobalIndex(unittest.TestCase):
    """GlobalIndex 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.index = GlobalIndex()
        
    def test_keyword_indexing(self):
        """키워드 인덱싱 테스트"""
        # 노드 추가
        self.index.add_node(
            node_id="node1",
            content="Python 프로그래밍 에러 수정",
            root="root1",
            created_at=time.time()
        )
        
        self.index.add_node(
            node_id="node2",
            content="JavaScript 코드 리뷰",
            root="root1",
            created_at=time.time()
        )
        
        # 키워드 검색
        results = self.index.search_keywords("프로그래밍", limit=5)
        
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0][0], "node1")  # node1이 매칭
        
    def test_vector_search(self):
        """벡터 검색 테스트"""
        # 노드 추가
        self.index.add_node(
            node_id="node1",
            content="머신러닝 모델 학습",
            root="root1",
            created_at=time.time()
        )
        
        self.index.add_node(
            node_id="node2",
            content="딥러닝 네트워크 구성",
            root="root1",
            created_at=time.time()
        )
        
        # 벡터 검색
        query_embedding = self.index._create_simple_embedding("머신러닝 학습")
        results = self.index.search_vectors(query_embedding, limit=5)
        
        self.assertGreater(len(results), 0)
        self.assertGreater(results[0][1], 0)  # 유사도 > 0
        
    def test_hybrid_search(self):
        """하이브리드 검색 테스트"""
        # 다양한 노드 추가
        nodes = [
            ("node1", "Python 에러 디버깅 작업", "project1"),
            ("node2", "JavaScript 버그 수정", "project1"),
            ("node3", "Python 성능 최적화", "project2"),
            ("node4", "데이터베이스 쿼리 최적화", "project2"),
        ]
        
        for node_id, content, root in nodes:
            self.index.add_node(
                node_id=node_id,
                content=content,
                root=root,
                created_at=time.time()
            )
            
        # 하이브리드 검색
        results = self.index.hybrid_search("Python 최적화", limit=3)
        
        self.assertGreater(len(results), 0)
        # Python과 최적화를 모두 포함하는 node3가 상위에 있어야 함
        top_nodes = [r[0] for r in results[:2]]
        self.assertIn("node3", top_nodes)
        
    def test_entry_points_diversity(self):
        """엔트리 포인트 다양성 테스트"""
        # 여러 루트의 노드 추가
        for root_idx in range(3):
            for node_idx in range(3):
                self.index.add_node(
                    node_id=f"node_{root_idx}_{node_idx}",
                    content=f"작업 {root_idx} 내용 {node_idx}",
                    root=f"root{root_idx}",
                    created_at=time.time()
                )
                
        # 엔트리 포인트 가져오기
        entries = self.index.get_entry_points("작업", limit=3)
        
        # 서로 다른 루트에서 선택되었는지 확인
        roots = set()
        for entry in entries:
            if entry in self.index.node_meta:
                roots.add(self.index.node_meta[entry]['root'])
                
        self.assertGreaterEqual(len(roots), 2)  # 최소 2개 이상의 다른 루트
        
    def test_node_removal(self):
        """노드 제거 테스트"""
        # 노드 추가
        self.index.add_node(
            node_id="node1",
            content="테스트 노드",
            root="root1",
            created_at=time.time()
        )
        
        # 통계 확인
        stats_before = self.index.get_stats()
        self.assertEqual(stats_before['total_nodes'], 1)
        
        # 노드 제거
        self.index.remove_node("node1")
        
        # 제거 후 확인
        stats_after = self.index.get_stats()
        self.assertEqual(stats_after['total_nodes'], 0)
        
        # 검색에서도 나타나지 않아야 함
        results = self.index.search_keywords("테스트", limit=5)
        self.assertEqual(len(results), 0)


if __name__ == '__main__':
    unittest.main()
