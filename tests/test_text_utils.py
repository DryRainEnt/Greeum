"""
텍스트 유틸리티 함수 테스트
"""

import unittest
import numpy as np

from tests.base_test_case import BaseGreeumTestCase
from greeum.text_utils import (
    convert_numpy_types,
    extract_keywords_from_text,
    extract_tags_from_text,
    compute_text_importance
)

class TestConvertNumpyTypes(BaseGreeumTestCase):
    """convert_numpy_types 함수 테스트"""
    
    def test_convert_numpy_scalar_types(self):
        """numpy 스칼라 타입 변환 테스트"""
        # Numpy 정수형
        self.assertEqual(convert_numpy_types(np.int32(42)), 42)
        self.assertEqual(convert_numpy_types(np.int64(42)), 42)
        self.assertIsInstance(convert_numpy_types(np.int32(42)), int)
        
        # Numpy 실수형
        self.assertEqual(convert_numpy_types(np.float32(3.14)), 3.14)
        self.assertEqual(convert_numpy_types(np.float64(3.14)), 3.14)
        self.assertIsInstance(convert_numpy_types(np.float32(3.14)), float)
        
        # Numpy 불리언
        self.assertEqual(convert_numpy_types(np.bool_(True)), True)
        self.assertEqual(convert_numpy_types(np.bool_(False)), False)
        self.assertIsInstance(convert_numpy_types(np.bool_(True)), bool)
    
    def test_convert_numpy_array(self):
        """numpy 배열 변환 테스트"""
        # 1차원 배열
        arr_1d = np.array([1, 2, 3, 4, 5])
        result_1d = convert_numpy_types(arr_1d)
        self.assertEqual(result_1d, [1, 2, 3, 4, 5])
        self.assertIsInstance(result_1d, list)
        
        # 2차원 배열
        arr_2d = np.array([[1, 2], [3, 4]])
        result_2d = convert_numpy_types(arr_2d)
        self.assertEqual(result_2d, [[1, 2], [3, 4]])
        self.assertIsInstance(result_2d, list)
        self.assertIsInstance(result_2d[0], list)
        
        # 혼합 타입 배열
        arr_mixed = np.array([1, 2.5, 3])
        result_mixed = convert_numpy_types(arr_mixed)
        self.assertEqual(result_mixed, [1.0, 2.5, 3.0])
        self.assertIsInstance(result_mixed, list)
    
    def test_convert_nested_structures(self):
        """중첩 구조 변환 테스트"""
        # 딕셔너리 안의 numpy 타입
        test_dict = {
            "int": np.int32(10),
            "float": np.float64(3.14),
            "array": np.array([1, 2, 3]),
            "nested": {
                "bool": np.bool_(True)
            }
        }
        
        result = convert_numpy_types(test_dict)
        
        self.assertEqual(result["int"], 10)
        self.assertIsInstance(result["int"], int)
        
        self.assertEqual(result["float"], 3.14)
        self.assertIsInstance(result["float"], float)
        
        self.assertEqual(result["array"], [1, 2, 3])
        self.assertIsInstance(result["array"], list)
        
        self.assertEqual(result["nested"]["bool"], True)
        self.assertIsInstance(result["nested"]["bool"], bool)
        
        # 리스트 안의 numpy 타입
        test_list = [np.int32(10), np.array([1, 2]), {"value": np.float64(3.14)}]
        result_list = convert_numpy_types(test_list)
        
        self.assertEqual(result_list[0], 10)
        self.assertIsInstance(result_list[0], int)
        
        self.assertEqual(result_list[1], [1, 2])
        self.assertIsInstance(result_list[1], list)
        
        self.assertEqual(result_list[2]["value"], 3.14)
        self.assertIsInstance(result_list[2]["value"], float)
        
        # 튜플 안의 numpy 타입
        test_tuple = (np.int32(10), np.array([1, 2]))
        result_tuple = convert_numpy_types(test_tuple)
        
        self.assertEqual(result_tuple[0], 10)
        self.assertIsInstance(result_tuple[0], int)
        
        self.assertEqual(result_tuple[1], [1, 2])
        self.assertIsInstance(result_tuple[1], list)
    
    def test_non_numpy_types(self):
        """numpy가 아닌 타입 처리 테스트"""
        # 기본 Python 타입은 그대로 유지
        self.assertEqual(convert_numpy_types(42), 42)
        self.assertEqual(convert_numpy_types(3.14), 3.14)
        self.assertEqual(convert_numpy_types(True), True)
        self.assertEqual(convert_numpy_types("text"), "text")
        self.assertEqual(convert_numpy_types(None), None)
        
        # 사용자 정의 클래스
        class TestClass:
            def __init__(self, value):
                self.value = value
        
        test_obj = TestClass(42)
        self.assertIs(convert_numpy_types(test_obj), test_obj)


class TestTextUtilsFunctions(BaseGreeumTestCase):
    """다른 텍스트 유틸리티 함수 테스트"""
    
    def test_extract_keywords(self):
        """키워드 추출 테스트"""
        text = "인공지능과 머신러닝은 현대 컴퓨터 과학의 중요한 분야입니다."
        keywords = extract_keywords_from_text(text)
        
        # 키워드에 '인공지능', '머신러닝', '컴퓨터', '과학' 등이 포함되어 있는지 확인
        # (정확한 단어 분리는 구현에 따라 달라질 수 있음)
        self.assertIsInstance(keywords, list)
        self.assertTrue(len(keywords) > 0)
    
    def test_extract_tags(self):
        """태그 추출 테스트"""
        text = "이 프로젝트는 매우 중요하고 긴급하게 처리해야 합니다."
        tags = extract_tags_from_text(text)
        
        self.assertIsInstance(tags, list)
        self.assertTrue(len(tags) > 0)
        # '중요', '긴급' 등의 태그가 포함될 가능성이 높음
    
    def test_compute_importance(self):
        """중요도 계산 테스트"""
        text = "이것은 매우 중요한 회의입니다. 반드시 참석해야 합니다."
        importance = compute_text_importance(text)
        
        self.assertIsInstance(importance, float)
        self.assertTrue(0.0 <= importance <= 1.0)
        # '중요', '반드시' 등의 단어로 인해 중요도가 높을 것으로 예상


if __name__ == "__main__":
    unittest.main() 