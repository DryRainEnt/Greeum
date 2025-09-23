"""
Branch System Integration Test
브랜치 기반 메모리 시스템 통합 테스트
"""

import unittest
import time
import uuid
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from greeum.core.branch_manager import BranchManager
from greeum.core.branch_global_index import GlobalIndex
from greeum.core.branch_auto_merge import AutoMergeEngine


class TestBranchIntegration(unittest.TestCase):
    """브랜치 시스템 통합 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        self.manager = BranchManager()
        
    def test_complete_workflow(self):
        """완전한 워크플로우 테스트"""
        # 1. 프로젝트 시작 - 여러 작업 병렬 진행
        self.manager.add_block(
            content="프로젝트 초기 설정 및 환경 구성",
            root="project-alpha",
            slot="A",
            tags={"actants": {"subject": "team", "action": "setup", "object": "project"}}
        )
        
        self.manager.add_block(
            content="API 설계 문서 작성 시작",
            root="project-alpha", 
            slot="B",
            tags={"actants": {"subject": "architect", "action": "design", "object": "api"}}
        )
        
        self.manager.add_block(
            content="데이터베이스 스키마 초안",
            root="project-alpha",
            slot="C",
            tags={"actants": {"subject": "dba", "action": "schema", "object": "database"}}
        )
        
        # 2. 각 브랜치에서 연속 작업
        for i in range(3):
            self.manager.add_block(
                content=f"환경 설정 단계 {i+1}",
                slot="A"
            )
            
        for i in range(2):
            self.manager.add_block(
                content=f"API 엔드포인트 {i+1} 설계",
                slot="B"
            )
            
        # 3. DFS 로컬 검색 테스트
        result = self.manager.search("환경 설정", slot="A", k=3)
        
        self.assertGreater(len(result.items), 0)
        self.assertEqual(result.meta['search_type'], 'dfs_local')
        self.assertIn('hops', result.meta)
        
        # 환경 설정 관련 블록들이 상위에 있는지 확인
        for item in result.items[:2]:
            self.assertIn("환경", item.content['text'])
            
    def test_cross_branch_search_with_global_index(self):
        """브랜치 간 검색 with 전역 인덱스"""
        # 서로 다른 브랜치에 관련 내용 추가
        self.manager.add_block(
            content="사용자 인증 시스템 개발",
            root="auth-service",
            slot="A"
        )
        
        self.manager.add_block(
            content="JWT 토큰 기반 인증 구현",
            root="auth-service",
            slot="A"
        )
        
        self.manager.add_block(
            content="프론트엔드 인증 연동",
            root="frontend-app",
            slot="B"
        )
        
        # 다른 브랜치에서 "인증" 검색
        self.manager.activate_slot("B", self.manager.stm_slots["B"])  # 프론트엔드 브랜치 활성화
        result = self.manager.search("JWT 인증", slot="B", fallback=True, k=5)
        
        # 결과에 JWT 관련 내용이 포함되어야 함 (전역 점프 통해)
        found_jwt = any("JWT" in item.content['text'] for item in result.items)
        self.assertTrue(found_jwt, "JWT content should be found through global jump")
        
    def test_auto_merge_proposal(self):
        """자동 머지 제안 테스트"""
        # 유사한 작업을 다른 슬롯에서 진행
        root = "merge-test"
        
        # 슬롯 A: 에러 수정 작업
        self.manager.add_block(
            content="로그인 에러 수정",
            root=root,
            slot="A",
            tags={"labels": ["bugfix", "login", "error"]}
        )
        
        self.manager.add_block(
            content="에러 핸들링 개선",
            root=root,
            slot="A",
            tags={"labels": ["bugfix", "error", "handling"]}
        )
        
        # 슬롯 B: 유사한 에러 수정 작업
        self.manager.add_block(
            content="로그인 버그 수정 완료",
            root=root,
            slot="B", 
            tags={"labels": ["bugfix", "login", "completed"]}
        )
        
        self.manager.add_block(
            content="에러 처리 로직 개선",
            root=root,
            slot="B",
            tags={"labels": ["bugfix", "error", "logic"]}
        )
        
        # 여러 번 유사한 작업 추가하여 EMA 점수 높이기
        for i in range(3):
            self.manager.add_block(
                content=f"에러 수정 후속 작업 {i}",
                root=root,
                slot="A",
                tags={"labels": ["bugfix", "followup"]}
            )
            
        # 머지 제안 확인
        proposals = self.manager.auto_merge.evaluate_auto_merge(["A", "B", "C"])
        
        # 유사한 작업이므로 머지 제안이 있을 수 있음
        if proposals:
            proposal = proposals[0]
            self.assertIn(proposal.slot_i, ["A", "B"])
            self.assertIn(proposal.slot_j, ["A", "B"])
            self.assertGreater(proposal.score, 0)
            self.assertTrue(proposal.reversible)
            
    def test_performance_metrics_tracking(self):
        """성능 메트릭 추적 테스트"""
        # 다양한 패턴의 검색 수행
        self.manager.add_block("성능 테스트 블록 1", root="perf-test")
        self.manager.add_block("성능 테스트 블록 2", root="perf-test")
        self.manager.add_block("성능 테스트 블록 3", root="perf-test")
        
        # 로컬 히트
        result1 = self.manager.search("성능 테스트", k=2)
        
        # 다른 루트에 추가하여 fallback 유도
        self.manager.add_block("다른 프로젝트", root="other-project", slot="B")
        
        # 다른 슬롯에서 검색 (fallback 가능성)
        result2 = self.manager.search("성능", slot="B", fallback=True, k=2)
        
        # 메트릭 확인
        metrics = self.manager.get_metrics()
        
        self.assertGreater(metrics['total_searches'], 0)
        self.assertGreaterEqual(metrics['avg_hops'], 0)
        self.assertGreaterEqual(metrics['local_hit_rate'], 0)
        self.assertIn('fallback_rate', metrics)
        
    def test_branch_depth_and_complexity(self):
        """브랜치 깊이 및 복잡도 테스트"""
        # 깊은 브랜치 생성
        root = "deep-branch"
        for i in range(10):
            self.manager.add_block(
                content=f"깊이 레벨 {i}",
                root=root,
                slot="A"
            )
            
        # 분기 생성
        current_head = self.manager.stm_slots["A"]
        
        # 슬롯 B에서 분기 시작
        self.manager.add_block(
            content="분기점에서 새로운 방향",
            root=root,
            slot="B"
        )
        
        for i in range(3):
            self.manager.add_block(
                content=f"분기 작업 {i}",
                root=root,
                slot="B"
            )
            
        # 브랜치 메타 확인
        branch_meta = self.manager.branches[root]
        self.assertGreater(branch_meta.size, 10)
        self.assertGreater(branch_meta.depth, 5)
        
        # 양쪽 브랜치에서 검색
        result_main = self.manager.search("깊이", slot="A", k=5)
        result_branch = self.manager.search("분기", slot="B", k=5)
        
        # 각각 적절한 결과를 반환해야 함
        self.assertGreater(len(result_main.items), 0)
        self.assertGreater(len(result_branch.items), 0)
        
    def test_global_index_integration(self):
        """전역 인덱스 통합 테스트"""
        # 다양한 키워드로 블록 추가
        keywords_content = [
            ("머신러닝", "머신러닝 모델 개발"),
            ("딥러닝", "딥러닝 네트워크 구성"),
            ("AI", "AI 시스템 통합"),
            ("알고리즘", "정렬 알고리즘 최적화"),
            ("데이터", "데이터 전처리 파이프라인")
        ]
        
        for keyword, content in keywords_content:
            self.manager.add_block(content, root="ai-project")
            
        # 전역 인덱스 통계 확인
        if self.manager.global_index:
            stats = self.manager.global_index.get_stats()
            self.assertGreater(stats['total_nodes'], 0)
            self.assertGreater(stats['total_terms'], 0)
            
            # 키워드 검색 테스트
            keyword_results = self.manager.global_index.search_keywords("머신러닝", limit=3)
            self.assertGreater(len(keyword_results), 0)
            
            # 하이브리드 검색 테스트
            hybrid_results = self.manager.global_index.hybrid_search("AI 머신러닝", limit=3)
            self.assertGreater(len(hybrid_results), 0)


if __name__ == '__main__':
    unittest.main()
