import sys
import os
import unittest
from datetime import datetime, timedelta

# 상위 디렉토리 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from greeum.temporal_reasoner import TemporalReasoner, evaluate_temporal_query

class TestTemporalReasoner(unittest.TestCase):
    """TemporalReasoner 클래스 테스트"""
    
    def setUp(self):
        """테스트 설정"""
        # 한국어를 기본 언어로 설정
        self.reasoner = TemporalReasoner(default_language="ko")
        # 영어를 위한 별도의 인스턴스
        self.en_reasoner = TemporalReasoner(default_language="en")
        # 자동 감지를 위한 인스턴스
        self.auto_reasoner = TemporalReasoner(default_language="auto")
    
    def test_korean_time_references(self):
        """한국어 시간 표현 테스트"""
        # 기본 시간 표현
        query = "어제 만난 사람이 누구였지?"
        refs = self.reasoner.extract_time_references(query)
        self.assertTrue(len(refs) > 0, "한국어 '어제' 인식 실패")
        self.assertEqual(refs[0]["term"], "어제")
        
        # 숫자가 포함된 정규식 패턴
        query = "3일 전에 보낸 이메일을 찾아줘"
        refs = self.reasoner.extract_time_references(query)
        self.assertTrue(len(refs) > 0, "한국어 '3일 전' 인식 실패")
        self.assertEqual(refs[0]["term"], "3일 전")
        
        # 특정 날짜
        query = "2023년 5월 15일에 있었던 미팅 내용 알려줘"
        refs = self.reasoner.extract_time_references(query)
        self.assertTrue(len(refs) > 0, "한국어 날짜 형식 인식 실패")
        self.assertEqual(refs[0]["term"], "2023년 5월 15일")
        self.assertTrue(refs[0].get("is_specific_date", False))
    
    def test_english_time_references(self):
        """영어 시간 표현 테스트"""
        # 기본 시간 표현
        query = "Who did I meet yesterday?"
        refs = self.en_reasoner.extract_time_references(query)
        self.assertTrue(len(refs) > 0, "영어 'yesterday' 인식 실패")
        self.assertEqual(refs[0]["term"], "yesterday")
        
        # 숫자가 포함된 정규식 패턴
        query = "Find the email I sent 3 days ago"
        refs = self.en_reasoner.extract_time_references(query)
        self.assertTrue(len(refs) > 0, "영어 '3 days ago' 인식 실패")
        self.assertEqual(refs[0]["term"], "3 days ago")
        
        # 특정 날짜 (미국식)
        query = "Tell me about the meeting on May 15, 2023"
        refs = self.en_reasoner.extract_time_references(query)
        self.assertTrue(len(refs) > 0, "영어 미국식 날짜 형식 인식 실패")
        self.assertEqual(refs[0]["term"], "May 15, 2023")
        self.assertTrue(refs[0].get("is_specific_date", False))
        
        # 특정 날짜 (영국식)
        query = "What happened on 15 May 2023?"
        refs = self.en_reasoner.extract_time_references(query)
        self.assertTrue(len(refs) > 0, "영어 영국식 날짜 형식 인식 실패")
        self.assertEqual(refs[0]["term"], "15 May 2023")
        self.assertTrue(refs[0].get("is_specific_date", False))
    
    def test_language_detection(self):
        """언어 감지 기능 테스트"""
        # 한국어 텍스트
        ko_query = "어제 서울에서 무슨 일이 있었는지 알려줘"
        lang = self.auto_reasoner._detect_language(ko_query)
        self.assertEqual(lang, "ko")
        
        # 영어 텍스트
        en_query = "Tell me what happened in Seoul yesterday"
        lang = self.auto_reasoner._detect_language(en_query)
        self.assertEqual(lang, "en")
        
        # 혼합 텍스트 (한국어 우세)
        mixed_query = "서울 날씨가 어제 how was it?"
        lang = self.auto_reasoner._detect_language(mixed_query)
        self.assertEqual(lang, "ko")
    
    def test_auto_language_detection(self):
        """자동 언어 감지 기반 시간 표현 추출 테스트"""
        # 한국어 쿼리
        ko_query = "어제 보낸 이메일을 찾아줘"
        ko_refs = self.auto_reasoner.extract_time_references(ko_query)
        self.assertTrue(len(ko_refs) > 0, "자동 감지 기반 한국어 인식 실패")
        self.assertEqual(ko_refs[0]["term"], "어제")
        
        # 영어 쿼리
        en_query = "Find the email I sent yesterday"
        en_refs = self.auto_reasoner.extract_time_references(en_query)
        self.assertTrue(len(en_refs) > 0, "자동 감지 기반 영어 인식 실패")
        self.assertEqual(en_refs[0]["term"], "yesterday")
    
    def test_evaluate_temporal_query(self):
        """evaluate_temporal_query 함수 테스트"""
        # 한국어 쿼리
        ko_result = evaluate_temporal_query("3일 전에 뭐 했어?", language="ko")
        self.assertTrue(ko_result["detected"], "한국어 쿼리 '3일 전' 평가 실패")
        self.assertEqual(ko_result["language"], "ko")
        self.assertEqual(ko_result["best_ref"]["term"], "3일 전")
        
        # 영어 쿼리
        en_result = evaluate_temporal_query("What did I do 3 days ago?", language="en")
        self.assertTrue(en_result["detected"], "영어 쿼리 '3 days ago' 평가 실패")
        self.assertEqual(en_result["language"], "en")
        self.assertEqual(en_result["best_ref"]["term"], "3 days ago")
        
        # 자동 언어 감지
        auto_result = evaluate_temporal_query("What happened yesterday?")
        self.assertTrue(auto_result["detected"], "자동 감지 기반 평가 실패")
        self.assertEqual(auto_result["language"], "en")
        self.assertEqual(auto_result["best_ref"]["term"], "yesterday")
        
        # 시간 표현이 없는 쿼리
        no_time_result = evaluate_temporal_query("Tell me about the weather")
        self.assertFalse(no_time_result["detected"])

if __name__ == "__main__":
    unittest.main() 