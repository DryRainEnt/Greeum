#!/usr/bin/env python3
"""
Quality Validation System for Greeum v2.0.5
- Automatically assesses memory quality before storage
- Provides quality scores and improvement suggestions
- Integrates with MCP server for enhanced user experience
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class QualityLevel(Enum):
    """Memory quality classification levels"""
    EXCELLENT = "excellent"    # 0.9-1.0
    GOOD = "good"             # 0.7-0.9
    ACCEPTABLE = "acceptable" # 0.5-0.7
    POOR = "poor"            # 0.3-0.5
    VERY_POOR = "very_poor"  # 0.0-0.3

class QualityValidator:
    """지능적 메모리 품질 검증 시스템"""
    
    def __init__(self):
        """품질 검증기 초기화"""
        self.min_length = 10
        self.max_length = 10000
        self.stop_words = {
            'english': {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'},
            'korean': {'이', '그', '저', '것', '들', '은', '는', '이', '가', '을', '를', '에', '에서', '로', '으로', '와', '과', '도'},
            'common': {'hello', 'hi', 'bye', 'thanks', 'thank', 'you', 'ok', 'okay', 'yes', 'no', 'sure'}
        }
        
    def validate_memory_quality(self, content: str, importance: float = 0.5, 
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        메모리 품질 종합 검증
        
        Args:
            content: 검증할 메모리 내용
            importance: 사용자 지정 중요도
            context: 추가 컨텍스트 정보
            
        Returns:
            {
                "quality_score": float,        # 0.0-1.0 품질 점수
                "quality_level": str,          # excellent/good/acceptable/poor/very_poor
                "quality_factors": Dict,       # 세부 품질 요소들
                "suggestions": List[str],      # 개선 제안사항
                "should_store": bool,          # 저장 권장 여부
                "adjusted_importance": float,  # 품질 기반 조정된 중요도
                "warnings": List[str]          # 경고 사항들
            }
        """
        try:
            # 1. 기본 품질 검사
            quality_factors = self._assess_quality_factors(content)
            
            # 2. 품질 점수 계산
            quality_score = self._calculate_quality_score(quality_factors, importance)
            
            # 3. 품질 등급 분류
            quality_level = self._classify_quality_level(quality_score)
            
            # 4. 개선 제안사항 생성
            suggestions = self._generate_suggestions(quality_factors, content)
            
            # 5. 저장 권장 여부 결정
            should_store = self._should_store_memory(quality_score, quality_level)
            
            # 6. 중요도 조정
            adjusted_importance = self._adjust_importance(importance, quality_score)
            
            # 7. 경고사항 생성
            warnings = self._generate_warnings(quality_factors, content)
            
            return {
                "quality_score": round(quality_score, 3),
                "quality_level": quality_level.value,
                "quality_factors": quality_factors,
                "suggestions": suggestions,
                "should_store": should_store,
                "adjusted_importance": adjusted_importance,
                "warnings": warnings,
                "timestamp": datetime.now().isoformat(),
                "validation_version": "2.1.0"
            }
            
        except Exception as e:
            logger.error(f"Quality validation failed: {e}")
            return self._create_fallback_result(content, importance, str(e))
    
    def _assess_quality_factors(self, content: str) -> Dict[str, Any]:
        """품질 요소들 세부 평가"""
        factors = {}
        
        # 1. 길이 평가
        factors['length'] = self._assess_length_quality(content)
        
        # 2. 내용 풍부도 평가
        factors['richness'] = self._assess_content_richness(content)
        
        # 3. 구조적 품질 평가
        factors['structure'] = self._assess_structural_quality(content)
        
        # 4. 언어 품질 평가
        factors['language'] = self._assess_language_quality(content)
        
        # 5. 정보 밀도 평가
        factors['information_density'] = self._assess_information_density(content)
        
        # 6. 검색 가능성 평가
        factors['searchability'] = self._assess_searchability(content)
        
        # 7. 시간 관련성 평가
        factors['temporal_relevance'] = self._assess_temporal_relevance(content)
        
        return factors
    
    def _assess_length_quality(self, content: str) -> Dict[str, Any]:
        """길이 기반 품질 평가"""
        length = len(content.strip())
        
        if length < self.min_length:
            return {"score": 0.1, "issue": "too_short", "actual_length": length}
        elif length > self.max_length:
            return {"score": 0.3, "issue": "too_long", "actual_length": length}
        elif self.min_length <= length <= 50:
            return {"score": 0.5, "issue": "minimal", "actual_length": length}
        elif 50 < length <= 200:
            return {"score": 0.8, "issue": None, "actual_length": length}
        elif 200 < length <= 1000:
            return {"score": 1.0, "issue": None, "actual_length": length}
        else:
            return {"score": 0.7, "issue": "verbose", "actual_length": length}
    
    def _is_meaningful_word(self, word: str) -> bool:
        """Check if word is meaningful (not stop word)"""
        return (word not in self.stop_words['english'] and 
                word not in self.stop_words['korean'] and 
                word not in self.stop_words['common'] and 
                len(word) > 2 and word.isalpha())
    
    def _assess_content_richness(self, content: str) -> Dict[str, Any]:
        """Memory-efficient content richness evaluation"""
        # Process words incrementally to save memory
        word_count = 0
        unique_words = set()
        meaningful_words = set()
        
        # Early limit to prevent DoS attacks
        max_words = 10000
        words_processed = 0
        
        for word in content.lower().split():
            if words_processed >= max_words:
                break
            
            word_count += 1
            words_processed += 1
            unique_words.add(word)
            
            if self._is_meaningful_word(word):
                meaningful_words.add(word)
        
        # Calculate ratios safely
        richness_ratio = len(meaningful_words) / word_count if word_count > 0 else 0.0
        lexical_diversity = len(unique_words) / word_count if word_count > 0 else 0.0
        
        # Comprehensive score
        richness_score = (richness_ratio * 0.6 + lexical_diversity * 0.4)
        
        return {
            "score": min(richness_score * 1.2, 1.0),  # 약간의 보너스
            "meaningful_word_ratio": richness_ratio,
            "lexical_diversity": lexical_diversity,
            "total_words": word_count,
            "unique_words": len(unique_words),
            "meaningful_words": len(meaningful_words),
            "truncated": words_processed >= max_words
        }
    
    def _assess_structural_quality(self, content: str) -> Dict[str, Any]:
        """구조적 품질 평가"""
        score = 0.5  # 기본 점수
        issues = []
        
        # 문장 구조 확인
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) > 1:
            score += 0.2  # 여러 문장 보너스
        
        # 구두점 사용 확인
        punctuation_count = len(re.findall(r'[.!?,:;]', content))
        if punctuation_count > 0:
            score += 0.1
        
        # 대소문자 혼용 확인 (영어의 경우)
        if re.search(r'[A-Z]', content) and re.search(r'[a-z]', content):
            score += 0.1
        
        # 단락 구분 확인
        paragraphs = content.split('\n\n')
        if len(paragraphs) > 1:
            score += 0.1
        
        # 너무 반복적인 패턴 검사
        words = content.lower().split()
        if len(words) > 5:
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            
            max_repeat = max(word_counts.values())
            if max_repeat > len(words) * 0.3:  # 30% 이상 반복
                score -= 0.3
                issues.append("excessive_repetition")
        
        return {
            "score": min(score, 1.0),
            "sentence_count": len(sentences),
            "punctuation_count": punctuation_count,
            "paragraph_count": len(paragraphs),
            "issues": issues
        }
    
    def _assess_language_quality(self, content: str) -> Dict[str, Any]:
        """언어 품질 평가"""
        score = 0.7  # 기본 점수
        
        # 기본적인 언어 품질 지표들
        
        # 1. 연속 공백 확인
        if '  ' in content:
            score -= 0.1
        
        # 2. 특수문자 남용 확인
        special_char_ratio = len(re.findall(r'[!@#$%^&*()_+=\[\]{}|;:,.<>?]', content)) / len(content)
        if special_char_ratio > 0.1:
            score -= 0.2
        
        # 3. 숫자와 텍스트의 균형
        digit_ratio = len(re.findall(r'\d', content)) / len(content)
        if digit_ratio > 0.5:  # 숫자가 50% 이상
            score -= 0.1
        
        # 4. 전체 대문자 또는 소문자 확인
        if content.isupper() and len(content) > 20:
            score -= 0.2
        elif content.islower() and len(content) > 50:
            score -= 0.1
        
        return {
            "score": max(score, 0.0),
            "special_char_ratio": special_char_ratio,
            "digit_ratio": digit_ratio,
            "has_mixed_case": not (content.isupper() or content.islower())
        }
    
    def _assess_information_density(self, content: str) -> Dict[str, Any]:
        """정보 밀도 평가"""
        words = content.split()
        
        # 정보가 담긴 패턴들 검사
        info_patterns = [
            r'\d+',                    # 숫자
            r'[A-Z][a-z]+',           # 고유명사
            r'[a-zA-Z]+\.[a-zA-Z]+',  # 도메인/확장자
            r'@[a-zA-Z0-9]+',         # 멘션
            r'#[a-zA-Z0-9]+',         # 해시태그
            r'\b[A-Z]{2,}\b',         # 약어
            r'\d{4}-\d{2}-\d{2}',     # 날짜
        ]
        
        info_matches = 0
        for pattern in info_patterns:
            info_matches += len(re.findall(pattern, content))
        
        if len(words) == 0:
            density = 0.0
        else:
            density = info_matches / len(words)
        
        # 밀도 점수 계산
        if density == 0:
            score = 0.3
        elif density < 0.1:
            score = 0.5
        elif density < 0.3:
            score = 0.8
        else:
            score = 1.0
            
        return {
            "score": score,
            "density": density,
            "info_matches": info_matches,
            "word_count": len(words)
        }
    
    def _assess_searchability(self, content: str) -> Dict[str, Any]:
        """검색 가능성 평가"""
        score = 0.5
        
        # 키워드 추출 가능성
        words = content.lower().split()
        potential_keywords = [w for w in words if len(w) > 3 and w.isalpha()]
        
        if len(potential_keywords) >= 3:
            score += 0.3
        elif len(potential_keywords) >= 1:
            score += 0.1
            
        # 고유한 식별자 포함
        unique_identifiers = len(re.findall(r'\b[A-Z][a-z]+\b|\b\d+\b|[a-zA-Z]+\.[a-zA-Z]+', content))
        if unique_identifiers > 0:
            score += 0.2
            
        return {
            "score": min(score, 1.0),
            "potential_keywords": len(potential_keywords),
            "unique_identifiers": unique_identifiers
        }
    
    def _assess_temporal_relevance(self, content: str) -> Dict[str, Any]:
        """시간 관련성 평가"""
        score = 0.6  # 기본 점수
        
        # 시간 관련 표현 검사
        temporal_patterns = [
            r'\b\d{4}년?\b',                    # 년도
            r'\b\d{1,2}월\b',                   # 월
            r'\b\d{1,2}일\b',                   # 일
            r'\b\d{4}-\d{2}-\d{2}\b',          # ISO 날짜
            r'\b(오늘|어제|내일|이번주|다음주)\b',      # 한국어 시간 표현
            r'\b(today|yesterday|tomorrow|this week|next week)\b',  # 영어 시간 표현
            r'\b(최근|예전|과거|미래)\b',             # 시간 관련 형용사
            r'\b(recently|previously|future|past)\b'
        ]
        
        temporal_matches = 0
        for pattern in temporal_patterns:
            temporal_matches += len(re.findall(pattern, content, re.IGNORECASE))
        
        if temporal_matches > 0:
            score += 0.2
        
        # 현재 시점과의 관련성
        current_time_words = ['지금', '현재', '이제', 'now', 'current', 'currently']
        for word in current_time_words:
            if word in content.lower():
                score += 0.1
                break
                
        return {
            "score": min(score, 1.0),
            "temporal_matches": temporal_matches,
            "has_current_context": any(word in content.lower() for word in current_time_words)
        }
    
    def _calculate_quality_score(self, quality_factors: Dict[str, Any], importance: float) -> float:
        """종합 품질 점수 계산"""
        # 가중치 설정
        weights = {
            'length': 0.15,
            'richness': 0.25,
            'structure': 0.15,
            'language': 0.15,
            'information_density': 0.15,
            'searchability': 0.10,
            'temporal_relevance': 0.05
        }
        
        weighted_score = 0.0
        for factor, weight in weights.items():
            if factor in quality_factors:
                weighted_score += quality_factors[factor]['score'] * weight
        
        # 사용자 중요도를 약간 반영
        final_score = weighted_score * 0.85 + importance * 0.15
        
        return min(final_score, 1.0)
    
    def _classify_quality_level(self, quality_score: float) -> QualityLevel:
        """품질 점수를 등급으로 분류"""
        if quality_score >= 0.9:
            return QualityLevel.EXCELLENT
        elif quality_score >= 0.7:
            return QualityLevel.GOOD
        elif quality_score >= 0.5:
            return QualityLevel.ACCEPTABLE
        elif quality_score >= 0.3:
            return QualityLevel.POOR
        else:
            return QualityLevel.VERY_POOR
    
    def _generate_suggestions(self, quality_factors: Dict[str, Any], content: str) -> List[str]:
        """품질 개선 제안사항 생성"""
        suggestions = []
        
        # 길이 관련 제안
        length_factor = quality_factors.get('length', {})
        if length_factor.get('issue') == 'too_short':
            suggestions.append("💡 Content is too short. Add more context or details to make it more meaningful.")
        elif length_factor.get('issue') == 'too_long':
            suggestions.append("✂️ Content is very long. Consider breaking it into smaller, focused memories.")
        elif length_factor.get('issue') == 'minimal':
            suggestions.append("[NOTE] Content is quite brief. Adding more context would improve searchability.")
        
        # 풍부도 관련 제안
        richness = quality_factors.get('richness', {})
        if richness.get('meaningful_word_ratio', 0) < 0.3:
            suggestions.append("🎯 Add more specific and meaningful details to increase content value.")
        
        # 구조 관련 제안
        structure = quality_factors.get('structure', {})
        if 'excessive_repetition' in structure.get('issues', []):
            suggestions.append("[PROCESS] Reduce repetitive content to improve clarity and conciseness.")
        if structure.get('sentence_count', 0) <= 1 and len(content) > 50:
            suggestions.append("📖 Break long content into multiple sentences for better readability.")
        
        # 검색 가능성 관련 제안
        searchability = quality_factors.get('searchability', {})
        if searchability.get('potential_keywords', 0) < 2:
            suggestions.append("🔍 Include more specific keywords to improve future searchability.")
        
        # 정보 밀도 관련 제안
        info_density = quality_factors.get('information_density', {})
        if info_density.get('density', 0) < 0.1:
            suggestions.append("📊 Add specific details like names, dates, or numbers to increase information value.")
        
        # 일반적인 품질 제안
        if not suggestions:
            suggestions.append("✅ Content quality looks good! Consider adding more context if relevant.")
        
        return suggestions[:3]  # 최대 3개 제안
    
    def _should_store_memory(self, quality_score: float, quality_level: QualityLevel) -> bool:
        """저장 권장 여부 결정"""
        if quality_level in [QualityLevel.EXCELLENT, QualityLevel.GOOD]:
            return True
        elif quality_level == QualityLevel.ACCEPTABLE:
            return True  # 수용 가능한 품질
        elif quality_level == QualityLevel.POOR:
            return False  # 품질이 낮아 저장 비권장
        else:  # VERY_POOR
            return False
    
    def _adjust_importance(self, original_importance: float, quality_score: float) -> float:
        """품질에 기반한 중요도 조정"""
        # 품질이 좋으면 중요도 상향, 나쁘면 하향 조정
        adjustment_factor = (quality_score - 0.5) * 0.2  # -0.1 ~ +0.1 범위
        adjusted = original_importance + adjustment_factor
        return max(0.0, min(1.0, adjusted))
    
    def _generate_warnings(self, quality_factors: Dict[str, Any], content: str) -> List[str]:
        """경고사항 생성"""
        warnings = []
        
        # 길이 경고
        length_factor = quality_factors.get('length', {})
        if length_factor.get('issue') == 'too_short':
            warnings.append("⚠️ Content may be too brief to be useful for future reference.")
        
        # 언어 품질 경고
        language_factor = quality_factors.get('language', {})
        if language_factor.get('score', 1.0) < 0.4:
            warnings.append("⚠️ Content may have formatting or language quality issues.")
        
        # 정보 밀도 경고
        info_density = quality_factors.get('information_density', {})
        if info_density.get('density', 0) < 0.05:
            warnings.append("⚠️ Content appears to have low information density.")
        
        # 검색 가능성 경고
        searchability = quality_factors.get('searchability', {})
        if searchability.get('potential_keywords', 0) == 0:
            warnings.append("⚠️ Content may be difficult to search for in the future.")
        
        return warnings
    
    def _create_fallback_result(self, content: str, importance: float, error: str) -> Dict[str, Any]:
        """오류 발생시 기본 결과 반환"""
        return {
            "quality_score": 0.5,
            "quality_level": QualityLevel.ACCEPTABLE.value,
            "quality_factors": {"error": error},
            "suggestions": ["⚠️ Quality validation encountered an error. Manual review recommended."],
            "should_store": True,  # 안전하게 저장 허용
            "adjusted_importance": importance,
            "warnings": [f"Quality validation error: {error}"],
            "timestamp": datetime.now().isoformat(),
            "validation_version": "2.1.0"
        }
    
    def validate_batch_memories(self, memories: List[Tuple[str, float]]) -> List[Dict[str, Any]]:
        """배치 메모리 품질 검증"""
        results = []
        for content, importance in memories:
            result = self.validate_memory_quality(content, importance)
            results.append(result)
        return results
    
    def get_quality_statistics(self, validations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """품질 검증 결과 통계 생성"""
        if not validations:
            return {"error": "No validation results provided"}
        
        total_count = len(validations)
        quality_levels = {}
        total_score = 0.0
        should_store_count = 0
        
        for validation in validations:
            level = validation.get('quality_level', 'unknown')
            quality_levels[level] = quality_levels.get(level, 0) + 1
            total_score += validation.get('quality_score', 0.0)
            if validation.get('should_store', False):
                should_store_count += 1
        
        return {
            "total_validations": total_count,
            "average_quality_score": round(total_score / total_count, 3),
            "quality_level_distribution": quality_levels,
            "storage_recommendation_rate": round(should_store_count / total_count, 3),
            "generated_at": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # 테스트 코드
    validator = QualityValidator()
    
    test_cases = [
        "안녕하세요",
        "오늘 프로젝트 회의에서 중요한 결정을 내렸습니다. 새로운 기능 개발을 위해 React를 사용하기로 했고, 데이터베이스는 PostgreSQL로 선정했습니다.",
        "!!!!!!!!!!!!",
        "Machine learning model training completed successfully with 95% accuracy on validation set. Model deployed to production environment at 2025-07-31 10:30 AM."
    ]
    
    print("✅ QualityValidator module loaded successfully")
    print("🧪 Running test cases...")
    
    for i, content in enumerate(test_cases, 1):
        result = validator.validate_memory_quality(content)
        print(f"\nTest {i}: {content[:50]}...")
        print(f"Quality Score: {result['quality_score']}")
        print(f"Quality Level: {result['quality_level']}")
        print(f"Should Store: {result['should_store']}")
        print(f"Suggestions: {result['suggestions'][0] if result['suggestions'] else 'None'}")