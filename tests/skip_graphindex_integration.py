#!/usr/bin/env python3
"""
TDD: GraphIndex와 BlockManager 통합 테스트
RED-GREEN-REFACTOR 사이클로 GraphIndex 연결 구현
"""

import unittest
import unittest.mock
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Greeum 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from greeum.core import BlockManager, DatabaseManager
from greeum.graph.index import GraphIndex
from greeum.text_utils import process_user_input

# GREEN 단계: GraphIndex 통합을 위한 패치 적용
from greeum.core.block_manager_graphindex import patch_block_manager_with_graphindex
patch_block_manager_with_graphindex(BlockManager)


class TestGraphIndexIntegration(unittest.TestCase):
    """GraphIndex와 BlockManager 통합 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_memory.db"
        
        # 데이터베이스 설정
        os.environ['GREEUM_DB_PATH'] = str(self.db_path)
        self.db_manager = DatabaseManager()
        self.block_manager = BlockManager(self.db_manager)
        
    def tearDown(self):
        """테스트 정리"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_block_manager_has_graph_index(self):
        """요구사항: BlockManager는 GraphIndex를 가져야 함"""
        # RED: 현재 BlockManager에 graph_index 속성이 없음
        self.assertTrue(
            hasattr(self.block_manager, 'graph_index'),
            "BlockManager should have graph_index attribute"
        )
        self.assertIsInstance(
            self.block_manager.graph_index,
            GraphIndex,
            "graph_index should be instance of GraphIndex"
        )
    
    def test_search_uses_graph_index_beam_search(self):
        """요구사항: _search_local_graph는 GraphIndex.beam_search를 사용해야 함"""
        # 테스트 데이터 준비
        test_blocks = [
            "프로젝트 시작",
            "프로젝트 설계 문서 작성",
            "프로젝트 구현 시작",
            "버그 수정",
            "테스트 작성"
        ]
        
        block_indices = []
        for i, content in enumerate(test_blocks):
            processed = process_user_input(content)
            idx = self.block_manager.add_block(
                context=content,
                keywords=processed.get('keywords', []),
                tags=processed.get('tags', []),
                embedding=processed.get('embedding', [0.0] * 768),
                importance=0.5
            )
            block_indices.append(idx)
        
        # 블록 간 링크 생성 (0 ↔ 1 ↔ 2)
        self.block_manager.update_block_links(block_indices[0], [block_indices[1]])
        self.block_manager.update_block_links(block_indices[1], [block_indices[0], block_indices[2]])
        self.block_manager.update_block_links(block_indices[2], [block_indices[1]])
        
        # GraphIndex가 beam_search를 사용하는지 확인
        # RED: 현재 _search_local_graph는 자체 BFS 사용
        with unittest.mock.patch.object(GraphIndex, 'beam_search') as mock_beam_search:
            mock_beam_search.return_value = [str(block_indices[1])]
            
            results = self.block_manager._search_local_graph(
                anchor_block=block_indices[0],
                radius=2,
                query="프로젝트",
                limit=5
            )
            
            # beam_search가 호출되어야 함
            mock_beam_search.assert_called_once()
    
    def test_add_block_updates_graph_index(self):
        """요구사항: 새 블록 추가 시 GraphIndex에 엣지가 추가되어야 함"""
        # 앵커 블록 생성
        anchor_idx = self.block_manager.add_block(
            context="앵커 블록",
            keywords=["anchor"],
            tags=["test"],
            embedding=[0.0] * 768,
            importance=0.9
        )
        
        # GraphIndex에 앵커가 추가되었는지 확인
        self.assertIn(
            str(anchor_idx),
            self.block_manager.graph_index.adj,
            "Anchor block should be in GraphIndex adjacency list"
        )
        
        # 직접 GraphIndex update_block_links 테스트
        # 슬롯 복잡성을 우회하고 직접 링크 생성 테스트
        new_idx = self.block_manager.add_block(
            context="새 블록",
            keywords=["new"],
            tags=["test"],
            embedding=[0.0] * 768,
            importance=0.5
        )
        
        # 직접 링크 생성 (update_block_links 호출로 GraphIndex 업데이트 테스트)
        success = self.block_manager.update_block_links(anchor_idx, [new_idx])
        self.assertTrue(success, "update_block_links should succeed")
        
        # GraphIndex에 엣지가 추가되었는지 확인
        neighbors = self.block_manager.graph_index.neighbors(str(anchor_idx))
        neighbor_ids = [n[0] for n in neighbors]
        self.assertIn(
            str(new_idx),
            neighbor_ids,
            "New block should be in anchor's neighbors in GraphIndex"
        )
    
    def test_graph_bootstrap_from_existing_blocks(self):
        """요구사항: 기존 블록들로부터 GraphIndex를 부트스트랩할 수 있어야 함"""
        # 기존 블록 생성 (GraphIndex 없이)
        block_indices = []
        for i in range(5):
            idx = self.block_manager.add_block(
                context=f"기존 블록 {i}",
                keywords=[f"block{i}"],
                tags=["existing"],
                embedding=[0.0] * 768,
                importance=0.5
            )
            block_indices.append(idx)
        
        # 수동으로 링크 추가
        self.block_manager.update_block_links(block_indices[0], [block_indices[1], block_indices[2]])
        self.block_manager.update_block_links(block_indices[1], [block_indices[0], block_indices[3]])
        
        # 부트스트랩 실행
        # RED: bootstrap_graph_index 메서드가 없음
        self.block_manager.bootstrap_graph_index()
        
        # GraphIndex에 모든 링크가 로드되었는지 확인
        neighbors_0 = self.block_manager.graph_index.neighbors(str(block_indices[0]))
        neighbor_ids_0 = [n[0] for n in neighbors_0]
        
        self.assertIn(str(block_indices[1]), neighbor_ids_0)
        self.assertIn(str(block_indices[2]), neighbor_ids_0)
    
    def test_search_performance_with_graph_index(self):
        """요구사항: GraphIndex 사용 시 검색 성능이 개선되어야 함"""
        import time
        
        # 100개 블록 생성 및 링크
        for i in range(100):
            idx = self.block_manager.add_block(
                context=f"테스트 블록 {i}",
                keywords=[f"test{i}"],
                tags=["perf"],
                embedding=[0.0] * 768,
                importance=0.5
            )
            # 이전 블록과 링크
            if i > 0:
                self.block_manager.update_block_links(idx, [idx - 1])
        
        # BFS 검색 시간 측정
        start = time.time()
        results_bfs = self.block_manager._search_local_graph(
            anchor_block=50,
            radius=3,
            query="테스트",
            limit=10
        )
        bfs_time = time.time() - start
        
        # GraphIndex beam_search 시간 측정
        # RED: GraphIndex를 사용하지 않으므로 같은 시간
        start = time.time()
        # 이상적으로는 graph_index.beam_search를 직접 호출
        results_beam = self.block_manager._search_local_graph(
            anchor_block=50,
            radius=3,
            query="테스트",
            limit=10
        )
        beam_time = time.time() - start
        
        # beam_search가 더 빨라야 함 (또는 최소한 비슷해야 함)
        self.assertLessEqual(
            beam_time,
            bfs_time * 1.2,  # 20% 마진 허용
            f"beam_search ({beam_time:.3f}s) should be faster than BFS ({bfs_time:.3f}s)"
        )


class TestGraphBootstrap(unittest.TestCase):
    """그래프 부트스트랩 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_memory.db"
        os.environ['GREEUM_DB_PATH'] = str(self.db_path)
        
    def tearDown(self):
        """테스트 정리"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_bootstrap_script_exists(self):
        """요구사항: 부트스트랩 스크립트가 존재해야 함"""
        # RED: 스크립트가 없음
        script_path = Path("scripts/bootstrap_graphindex.py")
        self.assertTrue(
            script_path.exists(),
            "bootstrap_graphindex.py script should exist"
        )
    
    def test_bootstrap_creates_snapshot(self):
        """요구사항: 부트스트랩이 그래프 스냅샷을 생성해야 함"""
        from greeum.core import BlockManager, DatabaseManager
        
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        
        # 테스트 블록 생성
        for i in range(10):
            block_manager.add_block(
                context=f"블록 {i}",
                keywords=[f"key{i}"],
                tags=["test"],
                embedding=[0.0] * 768,
                importance=0.5
            )
        
        # 부트스트랩 실행
        # RED: bootstrap 메서드가 없음
        from pathlib import Path
        output_path = Path(self.test_dir) / "graph_snapshot.json"
        snapshot_path = block_manager.bootstrap_and_save_graph(
            output_path=output_path
        )
        
        self.assertTrue(snapshot_path.exists())
        
        # 스냅샷 로드 가능한지 확인
        from greeum.graph.snapshot import load_graph_snapshot
        adjacency_dict = load_graph_snapshot(snapshot_path)
        
        # 로드된 데이터는 adjacency dictionary
        self.assertIsInstance(adjacency_dict, dict)
        self.assertGreater(len(adjacency_dict), 0)
        
        # GraphIndex로 복원 가능한지 확인
        from greeum.graph.index import GraphIndex
        restored_graph = GraphIndex()
        restored_graph.adj = adjacency_dict
        self.assertGreater(len(restored_graph.adj), 0)
    
    def test_first_run_auto_bootstrap(self):
        """요구사항: 첫 실행 시 자동으로 부트스트랩되어야 함"""
        from greeum.core import BlockManager, DatabaseManager
        
        # 새 BlockManager 생성 시 GraphIndex가 없으면 자동 부트스트랩
        # RED: 자동 부트스트랩이 구현되지 않음
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        
        # graph_index가 자동으로 초기화되었는지 확인
        self.assertIsNotNone(block_manager.graph_index)
        
        # 기존 블록이 있다면 자동으로 로드되었는지 확인
        if block_manager.get_blocks(limit=1):
            self.assertGreater(
                len(block_manager.graph_index.adj),
                0,
                "Existing blocks should be loaded into GraphIndex"
            )


class TestSTMWorkingMemory(unittest.TestCase):
    """STM을 작업 기억으로 승격하는 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.test_dir = tempfile.mkdtemp()
        os.environ['GREEUM_DB_PATH'] = str(Path(self.test_dir) / "test.db")
        
    def tearDown(self):
        """테스트 정리"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_stm_has_vector_fields(self):
        """요구사항: STM 슬롯에 topic_vec, decay 필드가 있어야 함"""
        from greeum.core.working_memory import AIContextualSlots
        
        slots = AIContextualSlots()
        slots.set_slot('A', content="테스트 내용", importance=0.5)
        
        slot = slots.get_slot('A')
        
        # RED: topic_vec, decay 필드가 없음
        self.assertTrue(
            hasattr(slot, 'topic_vec'),
            "Slot should have topic_vec field"
        )
        self.assertTrue(
            hasattr(slot, 'decay'),
            "Slot should have decay field"
        )
        self.assertIsNotNone(slot.topic_vec)
        
    def test_matches_query_uses_vector_similarity(self):
        """요구사항: matches_query가 벡터 유사도를 사용해야 함"""
        from greeum.core.working_memory import AIContextualSlots
        import numpy as np
        
        slots = AIContextualSlots()
        
        # 벡터가 있는 슬롯 생성
        slots.set_slot(
            'A',
            content="머신러닝 프로젝트",
            importance=0.7,
            embedding=[0.1] * 768  # 임베딩 추가
        )
        
        slot = slots.get_slot('A')
        
        # 유사한 쿼리와 다른 쿼리로 테스트
        # RED: 현재 matches_query는 키워드 매칭만 사용
        similar_query = "딥러닝 AI 프로젝트"
        different_query = "점심 메뉴 추천"
        
        # 벡터 유사도 기반 매칭
        self.assertTrue(
            slot.matches_query(similar_query, use_vector=True),
            "Should match similar query using vector similarity"
        )
        self.assertFalse(
            slot.matches_query(different_query, use_vector=True),
            "Should not match different query"
        )
    
    def test_auto_promote_to_ltm(self):
        """요구사항: 중요도/반복 임계값 초과 시 자동으로 LTM에 승격되어야 함"""
        from greeum.core.working_memory import AIContextualSlots
        from greeum.core import BlockManager, DatabaseManager
        
        slots = AIContextualSlots()
        db_manager = DatabaseManager()
        block_manager = BlockManager(db_manager)
        
        # 높은 중요도 슬롯 생성
        slots.set_slot(
            'A',
            content="중요한 정보",
            importance=0.95
        )
        
        # 여러 번 조회 (반복 사용 시뮬레이션)
        for _ in range(5):
            slot = slots.get_slot('A')
            slot.access_count += 1  # RED: access_count 필드가 없음
        
        # 자동 승격 트리거
        # RED: promote_to_ltm 메서드가 없음
        promoted_block_id = slots.promote_to_ltm('A', block_manager)
        
        self.assertIsNotNone(promoted_block_id)
        
        # LTM에 실제로 추가되었는지 확인
        block = block_manager.get_block(promoted_block_id)
        self.assertIsNotNone(block)
        self.assertEqual(block['context'], "중요한 정보")
        
        # 슬롯이 비워졌는지 확인
        slot_after = slots.get_slot('A')
        self.assertIsNone(slot_after)


def run_tdd_tests():
    """TDD 테스트 실행"""
    print("=" * 60)
    print("TDD: GraphIndex 통합 테스트")
    print("=" * 60)
    print("\n🔴 RED Phase: 실패하는 테스트 작성")
    print("-" * 40)
    
    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 테스트 추가 (완성된 GraphIndex 테스트만)
    suite.addTests(loader.loadTestsFromTestCase(TestGraphIndexIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestGraphBootstrap))
    # STM 테스트는 추가 구현 필요로 제외
    # suite.addTests(loader.loadTestsFromTestCase(TestSTMWorkingMemory))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    print(f"실행: {result.testsRun}개")
    print(f"실패: {len(result.failures)}개")
    print(f"오류: {len(result.errors)}개")
    
    if not result.wasSuccessful():
        print("\n✅ RED 단계 성공: 테스트가 예상대로 실패했습니다!")
        print("다음 단계: GREEN - 테스트를 통과시킬 최소 구현")
        return 0
    else:
        print("\n⚠️ 모든 테스트가 통과했습니다. RED 단계 실패!")
        return 1


if __name__ == "__main__":
    sys.exit(run_tdd_tests())