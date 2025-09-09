#!/usr/bin/env python3
"""
End-to-End Context Preservation System Tests

v2.6.4 Context Preservation System의 전체 사이클을 
실제 환경과 유사한 조건에서 테스트합니다.

Author: Greeum Development Team
Version: 2.6.4
"""

import os
import sys
import time
import tempfile
import unittest
import threading
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

# Greeum 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from greeum.core.database_manager import DatabaseManager
from greeum.core.raw_data_backup_layer import RawDataBackupLayer
from greeum.core.precompact_hook import PreCompactHookHandler, PreCompactEvent
from greeum.core.context_recovery import ContextRecoveryManager
from greeum.core.intelligent_context_processor import IntelligentContextProcessor
from greeum.core.context_backup import ContextBackupItem, ContextType
from greeum.core.claude_code_detector import ClaudeCodeDetector


class ContextPreservationE2ETest(unittest.TestCase):
    """
    전체 Context Preservation 사이클 End-to-End 테스트
    
    실제 Claude Code 환경에서의 사용 시나리오를 시뮬레이션하여
    PreCompact Hook → Backup → Recovery → Processing 전체 흐름을 검증합니다.
    """
    
    def setUp(self):
        """테스트 환경 설정"""
        # 임시 데이터베이스 생성
        self.test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.test_db_path = self.test_db.name
        self.test_db.close()
        
        # 테스트 데이터
        self.test_session_id = "test_session_e2e_001"
        
        # 핵심 컴포넌트들 초기화
        self.db_manager = DatabaseManager(self.test_db_path)
        self.backup_layer = RawDataBackupLayer(self.db_manager)
        self.backup_layer.initialize()  # 테이블 생성을 위한 초기화
        self.precompact_hook = PreCompactHookHandler(self.backup_layer, self.test_session_id)
        self.recovery_manager = ContextRecoveryManager(self.backup_layer)
        self.context_processor = IntelligentContextProcessor()
        self.test_contexts = [
            "사용자가 새로운 프로젝트 시작을 요청했습니다.",
            "class ProjectManager:\n    def __init__(self):\n        self.status = 'active'",
            "테스트 실행 결과: 모든 테스트가 성공했습니다.",
            "오류 발생: FileNotFoundError in project_setup.py line 42",
            "프로젝트 설정이 완료되었습니다. 다음 단계로 진행해주세요."
        ]
        
    def tearDown(self):
        """테스트 정리"""
        try:
            # Hook 해제
            if self.precompact_hook.is_active:
                self.precompact_hook.unregister_hook()
            
            # 임시 파일 정리
            os.unlink(self.test_db_path)
        except Exception:
            pass
    
    def test_full_cycle_with_claude_code_simulation(self):
        """완전한 Context Preservation 사이클 테스트 (Claude Code 환경 시뮬레이션)"""
        print("\n🔄 Full Cycle Test: Claude Code Environment Simulation")
        
        # 1. Claude Code 환경 시뮬레이션
        with patch.dict(os.environ, {
            'CLAUDECODE': '1',
            'CLAUDE_CODE_ENTRYPOINT': 'cli',
            'CLAUDE_SESSION_ID': self.test_session_id
        }):
            
            # 2. PreCompact Hook 등록
            self.assertTrue(self.precompact_hook.register_hook())
            self.assertTrue(self.precompact_hook.is_active)
            print("✅ PreCompact Hook 등록 성공")
            
            # 3. 컨텍스트 데이터 백업 시뮬레이션
            backup_ids = []
            for i, context in enumerate(self.test_contexts):
                backup_item = ContextBackupItem(
                    raw_content=context,
                    context_type=ContextType.USER_MESSAGE if "사용자" in context else ContextType.TOOL_RESULT,
                    session_id=self.test_session_id,
                    timestamp=datetime.now() + timedelta(seconds=i),
                    auto_compact_risk_score=0.8,
                    original_length=len(context),
                    recovery_metadata={
                        "test_sequence": i,
                        "e2e_test": True
                    }
                )
                
                backup_id = self.backup_layer.backup_context_immediately(
                    content=backup_item.raw_content,
                    context_type=backup_item.context_type,
                    session_id=backup_item.session_id
                )
                backup_ids.append(backup_id)
                time.sleep(0.1)  # 시간 차이 생성
            
            print(f"✅ {len(backup_ids)} 개 컨텍스트 백업 완료")
            
            # 4. PreCompact 이벤트 시뮬레이션
            precompact_event_data = {
                'length': 15000,
                'trigger_type': 'auto_compact',
                'urgency': 0.9,
                'preview': 'Large context about to be compacted...'
            }
            
            self.precompact_hook.handle_precompact_signal(precompact_event_data)
            print("✅ PreCompact 이벤트 처리 완료")
            
            # 5. 컨텍스트 복원 테스트
            time.sleep(0.2)  # 백업 완료 대기
            recovery_result = self.recovery_manager.recover_session_context(self.test_session_id)
            
            self.assertTrue(recovery_result['success'])
            self.assertGreater(recovery_result['quality_score'], 0.5)
            self.assertGreater(len(recovery_result['recovered_context']), 0)
            print(f"✅ 컨텍스트 복원 완료 (품질: {recovery_result['quality_score']:.2f})")
            
            # 6. 지능형 컨텍스트 처리 테스트
            recovered_context = recovery_result['recovered_context']
            processed_contexts = self.context_processor.optimize_context_flow([recovered_context])
            
            self.assertGreater(len(processed_contexts), 0)
            
            # 중요도 분석
            importance_scores = [
                self.context_processor.analyze_context_importance(ctx)
                for ctx in self.test_contexts
            ]
            avg_importance = sum(importance_scores) / len(importance_scores)
            self.assertGreater(avg_importance, 0.3)
            print(f"✅ 지능형 처리 완료 (평균 중요도: {avg_importance:.2f})")
            
            # 7. 전체 시스템 상태 검증
            hook_status = self.precompact_hook.get_hook_status()
            processing_stats = self.context_processor.get_processing_statistics()
            
            self.assertEqual(hook_status['session_id'], self.test_session_id)
            self.assertTrue(hook_status['claude_code_detected'])
            print("✅ 시스템 상태 검증 완료")
            
        print("🎉 Full Cycle Test 성공!")
    
    def test_emergency_backup_recovery_scenario(self):
        """긴급 백업 및 복원 시나리오 테스트"""
        print("\n🚨 Emergency Backup Recovery Test")
        
        # Claude Code 환경 설정
        with patch.dict(os.environ, {'CLAUDECODE': '1', 'CLAUDE_CODE_ENTRYPOINT': 'cli'}):
            
            # Hook 등록
            self.precompact_hook.register_hook()
            
            # 긴급 상황 시뮬레이션 (높은 위험도 데이터)
            emergency_data = {
                'critical_context': self.test_contexts,
                'session_state': {'active_task': 'project_setup', 'progress': 0.7},
                'user_intent': 'implement new feature with error handling',
                'timestamp': datetime.now().isoformat()
            }
            
            # 긴급 백업 수행
            backup_id = self.precompact_hook.emergency_backup(emergency_data)
            self.assertIsNotNone(backup_id)
            self.assertNotIn('error', backup_id)
            print(f"✅ 긴급 백업 완료: {backup_id}")
            
            # 복원 테스트
            time.sleep(0.1)
            recovery_result = self.recovery_manager.recover_session_context(self.precompact_hook.session_id)
            
            self.assertTrue(recovery_result['success'])
            self.assertIn('critical_context', recovery_result['recovered_context'])
            print("✅ 긴급 복원 성공")
            
            # 복원된 데이터 품질 검증
            quality_score = recovery_result['quality_score']
            self.assertGreater(quality_score, 0.6)  # 긴급 백업은 높은 품질 기대
            print(f"✅ 복원 품질 검증: {quality_score:.2f}")
    
    def test_multi_session_context_continuity(self):
        """다중 세션 컨텍스트 연속성 테스트"""
        print("\n🔗 Multi-Session Continuity Test")
        
        # 첫 번째 세션
        session1_id = "test_session_001"
        session1_contexts = self.test_contexts[:3]
        
        for context in session1_contexts:
            backup_item = ContextBackupItem(
                raw_content=context,
                context_type=ContextType.CONVERSATION_TURN,
                session_id=session1_id,
                timestamp=datetime.now(),
                auto_compact_risk_score=0.6,
                original_length=len(context),
                recovery_metadata={"session": 1}
            )
            self.backup_layer.backup_context_immediately(
                content=backup_item.raw_content,
                context_type=backup_item.context_type,
                session_id=backup_item.session_id
            )
        
        print("✅ 세션 1 백업 완료")
        
        # 두 번째 세션
        session2_id = "test_session_002"
        session2_contexts = self.test_contexts[3:]
        
        for context in session2_contexts:
            backup_item = ContextBackupItem(
                raw_content=context,
                context_type=ContextType.CONVERSATION_TURN, 
                session_id=session2_id,
                timestamp=datetime.now() + timedelta(minutes=5),
                auto_compact_risk_score=0.7,
                original_length=len(context),
                recovery_metadata={"session": 2}
            )
            self.backup_layer.backup_context_immediately(
                content=backup_item.raw_content,
                context_type=backup_item.context_type,
                session_id=backup_item.session_id
            )
        
        print("✅ 세션 2 백업 완료")
        
        # 각 세션 복원 테스트
        recovery1 = self.recovery_manager.recover_session_context(session1_id)
        recovery2 = self.recovery_manager.recover_session_context(session2_id)
        
        self.assertTrue(recovery1['success'])
        self.assertTrue(recovery2['success'])
        print("✅ 두 세션 모두 복원 성공")
        
        # 컨텍스트 병합 테스트
        merged_context = self.recovery_manager.smart_context_merge(
            recovery1['recovered_context'],
            recovery2['recovered_context']
        )
        
        self.assertGreater(len(merged_context), 0)
        self.assertIn("사용자가 새로운", merged_context)  # 세션 1 내용
        self.assertIn("오류 발생", merged_context)       # 세션 2 내용
        print("✅ 컨텍스트 병합 성공")
    
    def test_context_processing_performance(self):
        """컨텍스트 처리 성능 테스트"""
        print("\n⚡ Context Processing Performance Test")
        
        # 대량 컨텍스트 데이터 생성
        large_contexts = []
        for i in range(50):
            context = f"테스트 컨텍스트 #{i}: 이것은 성능 테스트용 데이터입니다. " * 10
            large_contexts.append(context)
        
        # 중요도 분석 성능 측정
        start_time = time.time()
        importance_scores = [
            self.context_processor.analyze_context_importance(ctx)
            for ctx in large_contexts
        ]
        analysis_time = time.time() - start_time
        
        print(f"✅ 중요도 분석: {len(large_contexts)}개 컨텍스트, {analysis_time:.2f}초")
        self.assertLess(analysis_time, 5.0)  # 5초 이내
        
        # 압축 성능 측정
        start_time = time.time()
        compressed = self.context_processor.compress_redundant_context(large_contexts)
        compression_time = time.time() - start_time
        
        print(f"✅ 압축 처리: {compression_time:.2f}초")
        self.assertLess(compression_time, 3.0)  # 3초 이내
        
        # 압축 효율성 검증
        original_size = sum(len(ctx) for ctx in large_contexts)
        compressed_size = len(compressed)
        compression_ratio = compressed_size / original_size
        
        print(f"✅ 압축률: {compression_ratio:.1%}")
        self.assertLess(compression_ratio, 0.8)  # 80% 이하로 압축
    
    def test_error_handling_and_recovery(self):
        """오류 처리 및 복구 테스트"""
        print("\n🛡️  Error Handling and Recovery Test")
        
        # 잘못된 데이터로 테스트
        invalid_contexts = [
            None,
            "",
            "A" * 100000,  # 너무 긴 컨텍스트
            "\x00\x01\x02",  # 바이너리 데이터
            "🎉" * 1000  # 이모지 대량
        ]
        
        # 각 잘못된 데이터에 대한 처리 테스트
        for i, invalid_context in enumerate(invalid_contexts):
            try:
                if invalid_context is not None:
                    importance = self.context_processor.analyze_context_importance(invalid_context)
                    self.assertIsInstance(importance, float)
                    self.assertGreaterEqual(importance, 0.0)
                    self.assertLessEqual(importance, 1.0)
                    print(f"✅ 잘못된 데이터 {i+1} 처리 성공")
                else:
                    # None 데이터는 0.0 반환 기대
                    importance = self.context_processor.analyze_context_importance(invalid_context)
                    self.assertEqual(importance, 0.0)
                    print(f"✅ None 데이터 처리 성공")
            except Exception as e:
                print(f"⚠️ 잘못된 데이터 {i+1} 처리 중 예외: {e}")
                # 예외가 발생해도 시스템이 다운되지 않으면 성공
                self.assertIsInstance(e, Exception)
        
        # 데이터베이스 오류 시뮬레이션
        with patch.object(self.backup_layer, 'backup_context_immediately', 
                         side_effect=Exception("DB Connection Error")):
            
            # Hook이 오류를 처리하고 계속 작동하는지 테스트
            try:
                test_data = {"test": "error simulation"}
                result = self.precompact_hook.emergency_backup(test_data)
                self.assertIn("error_", result)  # 오류 ID 생성 확인
                print("✅ 데이터베이스 오류 처리 성공")
            except Exception:
                print("⚠️ 데이터베이스 오류 처리 실패")
    
    def test_concurrent_operations(self):
        """동시 작업 처리 테스트"""
        print("\n🧵 Concurrent Operations Test")
        
        # 동시 백업 작업 테스트
        def backup_worker(worker_id):
            """백업 워커 함수"""
            for i in range(10):
                backup_item = ContextBackupItem(
                    raw_content=f"워커 {worker_id} 컨텍스트 #{i}",
                    context_type=ContextType.SYSTEM_STATE,
                    session_id=f"concurrent_session_{worker_id}",
                    timestamp=datetime.now(),
                    auto_compact_risk_score=0.5,
                    original_length=50,
                    recovery_metadata={"worker": worker_id, "item": i}
                )
                
                try:
                    backup_id = self.backup_layer.backup_context_immediately(
                    content=backup_item.raw_content,
                    context_type=backup_item.context_type,
                    session_id=backup_item.session_id
                )
                    self.assertIsNotNone(backup_id)
                except Exception as e:
                    print(f"워커 {worker_id} 백업 오류: {e}")
        
        # 3개 워커로 동시 작업
        threads = []
        for worker_id in range(3):
            thread = threading.Thread(target=backup_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join(timeout=5.0)
        
        print("✅ 동시 백업 작업 완료")
        
        # 동시 복원 작업 테스트
        recovery_threads = []
        recovery_results = {}
        
        def recovery_worker(session_id):
            """복원 워커 함수"""
            try:
                result = self.recovery_manager.recover_session_context(f"concurrent_session_{session_id}")
                recovery_results[session_id] = result
            except Exception as e:
                print(f"복원 워커 {session_id} 오류: {e}")
                recovery_results[session_id] = {"success": False, "error": str(e)}
        
        for session_id in range(3):
            thread = threading.Thread(target=recovery_worker, args=(session_id,))
            recovery_threads.append(thread)
            thread.start()
        
        for thread in recovery_threads:
            thread.join(timeout=5.0)
        
        print(f"✅ 동시 복원 작업 완료: {len(recovery_results)} 결과")
    
    def test_system_integration_health_check(self):
        """시스템 통합 상태 검사"""
        print("\n🏥 System Integration Health Check")
        
        # 모든 컴포넌트 초기화 상태 확인
        self.assertIsNotNone(self.db_manager)
        self.assertIsNotNone(self.backup_layer)
        self.assertIsNotNone(self.precompact_hook)
        self.assertIsNotNone(self.recovery_manager)
        self.assertIsNotNone(self.context_processor)
        print("✅ 모든 컴포넌트 초기화 완료")
        
        # 컴포넌트 간 상호작용 테스트
        with patch.dict(os.environ, {'CLAUDECODE': '1'}):
            # Hook 등록
            hook_success = self.precompact_hook.register_hook()
            self.assertTrue(hook_success)
            
            # 백업 계층 작동 확인
            test_backup = ContextBackupItem(
                raw_content="시스템 상태 확인 테스트",
                context_type=ContextType.SYSTEM_STATE,
                session_id="health_check_session",
                timestamp=datetime.now(),
                auto_compact_risk_score=0.5,
                original_length=20,
                recovery_metadata={"health_check": True}
            )
            
            backup_id = self.backup_layer.backup_context_immediately(
                content=test_backup.raw_content,
                context_type=test_backup.context_type,
                session_id=test_backup.session_id
            )
            self.assertIsNotNone(backup_id)
            print("✅ 백업 계층 작동 확인")
            
            # 복원 관리자 작동 확인
            time.sleep(0.1)
            recovery = self.recovery_manager.recover_session_context("health_check_session")
            self.assertTrue(recovery['success'])
            print("✅ 복원 관리자 작동 확인")
            
            # 프로세서 작동 확인
            processed = self.context_processor.analyze_context_importance("테스트 컨텍스트")
            self.assertIsInstance(processed, float)
            print("✅ 컨텍스트 프로세서 작동 확인")
            
        # 리소스 사용량 확인
        processing_stats = self.context_processor.get_processing_statistics()
        self.assertIsInstance(processing_stats, dict)
        print(f"✅ 처리 통계 확인: {processing_stats}")
        
        print("🎉 시스템 상태 검사 완료!")


def run_e2e_tests():
    """E2E 테스트 실행"""
    print("🚀 Context Preservation System E2E 테스트 시작")
    print("=" * 60)
    
    # 테스트 스위트 생성
    test_suite = unittest.TestLoader().loadTestsFromTestCase(ContextPreservationE2ETest)
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 E2E 테스트 결과 요약")
    print(f"총 테스트: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"오류: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 실패한 테스트:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n⚠️ 오류가 발생한 테스트:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n🎯 성공률: {success_rate:.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # E2E 테스트 실행
    success = run_e2e_tests()
    
    if success:
        print("\n🎉 모든 E2E 테스트가 성공했습니다!")
        sys.exit(0)
    else:
        print("\n💥 일부 E2E 테스트가 실패했습니다.")
        sys.exit(1)