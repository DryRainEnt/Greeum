#!/usr/bin/env python3
"""
Greeum v2.5.1 AI Context Slots 단위 테스트
Smart Context Slots 시스템의 핵심 기능을 검증
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

from greeum.core.working_memory import (
    AIContextualSlots, MemorySlot, SlotType, SlotIntent
)


class TestMemorySlot(unittest.TestCase):
    """MemorySlot 클래스 테스트"""
    
    def test_memory_slot_creation(self):
        """기본 메모리 슬롯 생성 테스트"""
        slot = MemorySlot(content="테스트 메모리")
        
        self.assertEqual(slot.content, "테스트 메모리")
        self.assertEqual(slot.speaker, "user")
        self.assertEqual(slot.slot_type, SlotType.CONTEXT)
        self.assertIsNone(slot.ltm_anchor_block)
        self.assertEqual(slot.search_radius, 5)
        self.assertEqual(slot.importance_score, 0.5)
        
    def test_memory_slot_ltm_anchor(self):
        """LTM 앵커 슬롯 생성 테스트"""
        slot = MemorySlot(
            content="LTM 앵커 테스트",
            slot_type=SlotType.ANCHOR,
            ltm_anchor_block=123,
            search_radius=10,
            importance_score=0.9
        )
        
        self.assertTrue(slot.is_ltm_anchor())
        self.assertEqual(slot.ltm_anchor_block, 123)
        self.assertEqual(slot.search_radius, 10)
        self.assertEqual(slot.importance_score, 0.9)
        
    def test_memory_slot_expiration(self):
        """메모리 슬롯 만료 테스트"""
        # 과거 타임스탬프로 슬롯 생성
        past_time = datetime.utcnow() - timedelta(seconds=100)
        slot = MemorySlot(content="만료 테스트", timestamp=past_time)
        
        # 50초 TTL로 만료 검사 (만료되어야 함)
        self.assertTrue(slot.is_expired(50))
        
        # 200초 TTL로 만료 검사 (만료되지 않아야 함)
        self.assertFalse(slot.is_expired(200))
        
    def test_memory_slot_query_matching(self):
        """쿼리 매칭 기능 테스트"""
        slot = MemorySlot(content="인공지능 메모리 시스템 개발")
        
        self.assertTrue(slot.matches_query("메모리"))
        self.assertTrue(slot.matches_query("시스템"))
        self.assertTrue(slot.matches_query("메모리"))  # 한글 매칭
        self.assertFalse(slot.matches_query("데이터베이스"))


class TestAIContextualSlots(unittest.TestCase):
    """AIContextualSlots 시스템 테스트"""
    
    def setUp(self):
        """테스트 전 설정"""
        self.ai_slots = AIContextualSlots(ttl_seconds=60)  # 1분 TTL
        
    def test_slot_initialization(self):
        """슬롯 초기화 테스트"""
        self.assertEqual(len(self.ai_slots.slots), 3)
        self.assertIn('active', self.ai_slots.slots)
        self.assertIn('anchor', self.ai_slots.slots)
        self.assertIn('buffer', self.ai_slots.slots)
        
        # 모든 슬롯이 비어있어야 함
        for slot_name in self.ai_slots.slots:
            self.assertIsNone(self.ai_slots.slots[slot_name])
            
    def test_ai_decide_usage_context(self):
        """AI 컨텍스트 저장 의도 분석 테스트"""
        content = "현재 프로젝트 진행상황을 논의중입니다"
        context = {'metadata': {'session_id': 'test'}}
        
        used_slot = self.ai_slots.ai_decide_usage(content, context)
        self.assertEqual(used_slot, 'active')
        
        slot = self.ai_slots.get_slot('active')
        self.assertIsNotNone(slot)
        self.assertEqual(slot.slot_type, SlotType.CONTEXT)
        self.assertEqual(slot.importance_score, 0.7)
        
    def test_ai_decide_usage_anchor(self):
        """AI LTM 앵커 의도 분석 테스트"""
        content = "이 기억을 저장해두고 자주 참조해야 합니다"
        context = {
            'ltm_block_id': 456,
            'search_radius': 8,
            'metadata': {'priority': 'high'}
        }
        
        used_slot = self.ai_slots.ai_decide_usage(content, context)
        self.assertEqual(used_slot, 'anchor')
        
        slot = self.ai_slots.get_slot('anchor')
        self.assertIsNotNone(slot)
        self.assertEqual(slot.slot_type, SlotType.ANCHOR)
        self.assertEqual(slot.ltm_anchor_block, 456)
        self.assertEqual(slot.search_radius, 8)
        self.assertEqual(slot.importance_score, 0.9)
        self.assertTrue(slot.is_ltm_anchor())
        
    def test_ai_decide_usage_buffer(self):
        """AI 버퍼 임시보관 의도 분석 테스트"""
        content = "나중에 처리할 임시 메모입니다"
        context = {'metadata': {'temporary': True}}
        
        used_slot = self.ai_slots.ai_decide_usage(content, context)
        self.assertEqual(used_slot, 'buffer')
        
        slot = self.ai_slots.get_slot('buffer')
        self.assertIsNotNone(slot)
        self.assertEqual(slot.slot_type, SlotType.BUFFER)
        self.assertEqual(slot.importance_score, 0.3)
        
    def test_slot_expiration_handling(self):
        """슬롯 만료 처리 테스트"""
        # 매우 짧은 TTL로 설정
        short_ttl_slots = AIContextualSlots(ttl_seconds=1)
        
        content = "만료 테스트 메모리"
        context = {'metadata': {}}
        
        short_ttl_slots.ai_decide_usage(content, context)
        
        # 즉시 조회하면 존재해야 함
        slot = short_ttl_slots.get_slot('active')
        self.assertIsNotNone(slot)
        
        # 2초 후에는 만료되어야 함 (모킹을 사용하여 시간 조작)
        with patch('greeum.core.working_memory.datetime') as mock_datetime:
            future_time = datetime.utcnow() + timedelta(seconds=2)
            mock_datetime.utcnow.return_value = future_time
            
            expired_slot = short_ttl_slots.get_slot('active')
            self.assertIsNone(expired_slot)
            
    def test_get_all_active_slots(self):
        """모든 활성 슬롯 조회 테스트"""
        # 각 슬롯에 명시적으로 데이터 저장
        # active 슬롯
        self.ai_slots._use_as_context_cache("활성 메모리", {'metadata': {}})
        
        # anchor 슬롯  
        self.ai_slots._use_as_ltm_anchor("앵커 메모리", {'ltm_block_id': 789, 'metadata': {}})
        
        # buffer 슬롯
        self.ai_slots._use_as_buffer("버퍼 메모리", {'metadata': {'temp': True}})
            
        active_slots = self.ai_slots.get_all_active_slots()
        
        self.assertEqual(len(active_slots), 3)
        self.assertIn('active', active_slots)
        self.assertIn('anchor', active_slots)
        self.assertIn('buffer', active_slots)
        
    def test_slot_clearing(self):
        """슬롯 비우기 테스트"""
        # 슬롯에 데이터 저장
        self.ai_slots.ai_decide_usage("테스트 데이터", {'metadata': {}})
        self.assertIsNotNone(self.ai_slots.get_slot('active'))
        
        # 슬롯 비우기
        success = self.ai_slots.clear_slot('active')
        self.assertTrue(success)
        self.assertIsNone(self.ai_slots.get_slot('active'))
        
        # 존재하지 않는 슬롯 비우기 시도
        success = self.ai_slots.clear_slot('nonexistent')
        self.assertFalse(success)
        
    def test_slot_status_report(self):
        """슬롯 상태 리포트 테스트"""
        # 앵커 슬롯에 LTM 연결 데이터 저장
        anchor_content = "중요한 앵커 데이터입니다. " + "A" * 150  # 긴 내용
        anchor_context = {'ltm_block_id': 999, 'metadata': {'priority': 'critical'}}
        
        # 명시적으로 앵커 슬롯에 저장
        self.ai_slots._use_as_ltm_anchor(anchor_content, anchor_context)
        
        status = self.ai_slots.get_status()
        
        # 상태 구조 검증
        self.assertIn('active', status)
        self.assertIn('anchor', status)
        self.assertIn('buffer', status)
        
        # 앵커 슬롯 상태 상세 검증
        anchor_status = status['anchor']
        self.assertIsNotNone(anchor_status)
        self.assertEqual(anchor_status['type'], 'anchor')
        self.assertTrue(len(anchor_status['content_preview']) <= 103)  # 100 + "..."
        self.assertTrue(anchor_status['is_anchor'])
        self.assertEqual(anchor_status['anchor_block'], 999)
        self.assertEqual(anchor_status['importance'], 0.9)
        
        # 비어있는 슬롯 상태 검증
        self.assertIsNone(status['active'])
        self.assertIsNone(status['buffer'])
        

class TestIntentAnalysis(unittest.TestCase):
    """AI 의도 분석 로직 테스트"""
    
    def setUp(self):
        self.ai_slots = AIContextualSlots()
        
    def test_intent_frequent_reference_keywords(self):
        """자주참조 키워드 의도 분석"""
        test_cases = [
            "이 기억을 저장해두고 자주 참조하겠습니다",  # "나중에" 제거
            "중요한 정보를 보관해주세요",
            "이것을 기억해두세요"
        ]
        
        for content in test_cases:
            intent = self.ai_slots._analyze_intent(content, {})
            self.assertEqual(intent, SlotIntent.FREQUENT_REFERENCE)
            
    def test_intent_temporary_hold_keywords(self):
        """임시보관 키워드 의도 분석"""
        test_cases = [
            "임시로 저장해두세요",
            "잠깐 보관해주세요", 
            "나중에 다시 검토하겠습니다"
        ]
        
        for content in test_cases:
            intent = self.ai_slots._analyze_intent(content, {})
            self.assertEqual(intent, SlotIntent.TEMPORARY_HOLD)
            
    def test_intent_default_conversation(self):
        """기본 대화 의도 분석"""
        test_cases = [
            "현재 진행 상황을 알려드리겠습니다",
            "프로젝트 개발이 순조롭게 진행되고 있습니다",
            "이번 회의에서 논의된 내용입니다"
        ]
        
        for content in test_cases:
            intent = self.ai_slots._analyze_intent(content, {})
            self.assertEqual(intent, SlotIntent.CONTINUE_CONVERSATION)


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2)