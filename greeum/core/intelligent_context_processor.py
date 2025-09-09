#!/usr/bin/env python3
"""
Intelligent Context Processor for Greeum

AI 기반 컨텍스트 분석, 압축, 및 최적화를 수행하는 
지능형 컨텍스트 처리 시스템입니다.

Author: Greeum Development Team  
Version: 2.6.4
"""

import re
import json
import logging
import hashlib
from typing import Dict, Any, List, Tuple, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import Counter, defaultdict

from .context_backup import ContextBackupItem


@dataclass
class ContextAnalysisResult:
    """컨텍스트 분석 결과"""
    content: str
    importance_score: float
    content_type: str
    key_concepts: List[str]
    redundancy_level: float
    compression_ratio: float
    semantic_density: float
    

@dataclass
class CompressionResult:
    """압축 결과"""
    original_content: str
    compressed_content: str
    compression_ratio: float
    preserved_concepts: List[str]
    removed_redundancy: List[str]
    quality_score: float


class IntelligentContextProcessor:
    """
    AI 기반 컨텍스트 분석 및 최적화 프로세서
    
    대량의 컨텍스트 데이터를 지능적으로 분석하고,
    중요도에 따라 압축 및 우선순위를 지정합니다.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 분석 설정
        self.min_importance_threshold = 0.3
        self.max_compression_ratio = 0.7
        self.semantic_density_target = 0.8
        
        # 컨텍스트 패턴 정의
        self.importance_patterns = {
            'error_patterns': [r'error|exception|fail|bug|issue', 0.9],
            'decision_patterns': [r'decision|choose|select|determine', 0.8], 
            'code_patterns': [r'def |class |function|import|const|let|var', 0.7],
            'user_intent': [r'사용자|user|요청|request|질문|question', 0.8],
            'result_patterns': [r'결과|result|output|완료|complete', 0.7],
            'context_transition': [r'다음|next|then|이후|after', 0.6]
        }
        
        # 중복성 탐지 패턴
        self.redundancy_patterns = [
            r'반복|repeat|again|다시|same|동일',
            r'이미|already|previously|앞서|before',
            r'마찬가지|similarly|likewise|같은|identical'
        ]
        
        # 핵심 개념 추출 패턴
        self.concept_extractors = [
            r'(?:implement|구현|개발)\s+(\w+)',
            r'(?:class|클래스)\s+(\w+)', 
            r'(?:function|함수|기능)\s+(\w+)',
            r'(?:error|오류|에러)\s+(\w+)',
            r'(?:test|테스트|검증)\s+(\w+)'
        ]
        
        # 캐시된 분석 결과
        self.analysis_cache: Dict[str, ContextAnalysisResult] = {}
        self.compression_cache: Dict[str, CompressionResult] = {}
        
    def analyze_context_importance(self, content: str) -> float:
        """
        컨텍스트 내용의 중요도를 분석합니다.
        
        Args:
            content: 분석할 컨텍스트 내용
            
        Returns:
            중요도 스코어 (0.0-1.0)
        """
        try:
            if not content or not content.strip():
                return 0.0
            
            # 캐시 확인
            content_hash = self._get_content_hash(content)
            if content_hash in self.analysis_cache:
                return self.analysis_cache[content_hash].importance_score
            
            importance_score = 0.5  # 기본값
            content_lower = content.lower()
            
            # 패턴 기반 중요도 분석
            pattern_scores = []
            for pattern_name, (pattern, weight) in self.importance_patterns.items():
                matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
                if matches > 0:
                    pattern_score = min(matches * weight * 0.1, weight)
                    pattern_scores.append(pattern_score)
                    self.logger.debug(f"Pattern {pattern_name}: {matches} matches, score: {pattern_score}")
            
            # 패턴 스코어들의 가중평균
            if pattern_scores:
                importance_score += sum(pattern_scores) / len(pattern_scores)
            
            # 컨텐츠 길이 기반 조정
            length_factor = self._calculate_length_importance(content)
            importance_score *= length_factor
            
            # 구조적 복잡성 평가
            structural_complexity = self._evaluate_structural_complexity(content)
            importance_score += structural_complexity * 0.2
            
            # 시맨틱 밀도 평가
            semantic_density = self._calculate_semantic_density(content)
            importance_score += semantic_density * 0.15
            
            # 최종 스코어 정규화
            final_score = min(max(importance_score, 0.0), 1.0)
            
            # 결과 캐싱
            analysis_result = ContextAnalysisResult(
                content=content,
                importance_score=final_score,
                content_type=self._classify_content_type(content),
                key_concepts=self._extract_key_concepts(content),
                redundancy_level=self._calculate_redundancy_level(content),
                compression_ratio=0.0,  # 아직 압축되지 않음
                semantic_density=semantic_density
            )
            self.analysis_cache[content_hash] = analysis_result
            
            return final_score
            
        except Exception as e:
            self.logger.error(f"Failed to analyze context importance: {e}")
            return 0.5  # 기본값 반환
    
    def compress_redundant_context(self, contexts: List[str]) -> str:
        """
        중복된 컨텍스트를 압축합니다.
        
        Args:
            contexts: 압축할 컨텍스트 목록
            
        Returns:
            압축된 컨텍스트 텍스트
        """
        try:
            if not contexts:
                return ""
            
            if len(contexts) == 1:
                return contexts[0]
            
            # 전체 컨텍스트 합치기
            combined_content = "\n\n".join(contexts)
            content_hash = self._get_content_hash(combined_content)
            
            # 캐시 확인
            if content_hash in self.compression_cache:
                return self.compression_cache[content_hash].compressed_content
            
            # 중복 제거 및 압축 수행
            compressed = self._perform_intelligent_compression(contexts)
            
            # 압축 결과 캐싱
            compression_result = CompressionResult(
                original_content=combined_content,
                compressed_content=compressed,
                compression_ratio=len(compressed) / max(len(combined_content), 1),
                preserved_concepts=self._extract_key_concepts(compressed),
                removed_redundancy=self._identify_removed_content(combined_content, compressed),
                quality_score=self._evaluate_compression_quality(combined_content, compressed)
            )
            self.compression_cache[content_hash] = compression_result
            
            return compressed
            
        except Exception as e:
            self.logger.error(f"Failed to compress redundant context: {e}")
            return "\n\n".join(contexts)  # 압축 실패 시 원본 반환
    
    def prioritize_context_segments(self, segments: List[str]) -> List[Tuple[str, float]]:
        """
        컨텍스트 세그먼트들을 우선순위로 정렬합니다.
        
        Args:
            segments: 우선순위를 지정할 세그먼트 목록
            
        Returns:
            (세그먼트, 우선순위_스코어) 튜플의 정렬된 목록
        """
        try:
            prioritized_segments = []
            
            for segment in segments:
                # 각 세그먼트의 중요도 분석
                importance = self.analyze_context_importance(segment)
                
                # 세그먼트별 추가 분석
                segment_priority = self._calculate_segment_priority(segment, importance)
                
                prioritized_segments.append((segment, segment_priority))
            
            # 우선순위 순으로 정렬 (높은 순)
            sorted_segments = sorted(prioritized_segments, key=lambda x: x[1], reverse=True)
            
            self.logger.info(f"Prioritized {len(segments)} segments, top priority: {sorted_segments[0][1]:.3f}")
            return sorted_segments
            
        except Exception as e:
            self.logger.error(f"Failed to prioritize context segments: {e}")
            return [(segment, 0.5) for segment in segments]
    
    def optimize_context_flow(self, contexts: List[str]) -> List[str]:
        """
        컨텍스트 플로우를 최적화합니다.
        
        Args:
            contexts: 최적화할 컨텍스트 목록
            
        Returns:
            최적화된 컨텍스트 목록
        """
        try:
            if not contexts:
                return []
            
            # 1. 각 컨텍스트 분석
            analyzed_contexts = []
            for i, context in enumerate(contexts):
                importance = self.analyze_context_importance(context)
                concepts = self._extract_key_concepts(context)
                
                analyzed_contexts.append({
                    'index': i,
                    'content': context,
                    'importance': importance,
                    'concepts': concepts,
                    'length': len(context)
                })
            
            # 2. 중요도 기반 필터링
            important_contexts = [
                ctx for ctx in analyzed_contexts 
                if ctx['importance'] >= self.min_importance_threshold
            ]
            
            # 3. 개념 기반 중복 제거
            deduplicated = self._remove_conceptual_duplicates(important_contexts)
            
            # 4. 플로우 최적화 (논리적 순서 재배치)
            optimized_flow = self._optimize_logical_flow(deduplicated)
            
            # 5. 최적화된 컨텍스트 반환
            result = [ctx['content'] for ctx in optimized_flow]
            
            self.logger.info(f"Optimized context flow: {len(contexts)} -> {len(result)} contexts")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to optimize context flow: {e}")
            return contexts
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """처리 통계를 반환합니다."""
        return {
            'analysis_cache_size': len(self.analysis_cache),
            'compression_cache_size': len(self.compression_cache),
            'average_importance_score': self._calculate_average_importance(),
            'average_compression_ratio': self._calculate_average_compression(),
            'most_common_content_types': self._get_common_content_types(),
            'processing_efficiency': self._calculate_processing_efficiency()
        }
    
    # 내부 메서드들
    
    def _get_content_hash(self, content: str) -> str:
        """컨텐츠의 해시를 계산합니다."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _calculate_length_importance(self, content: str) -> float:
        """컨텐츠 길이 기반 중요도 팩터를 계산합니다."""
        length = len(content)
        
        if length < 50:
            return 0.7  # 너무 짧음
        elif length < 200:
            return 1.0  # 적당함
        elif length < 1000:
            return 0.95  # 약간 김
        elif length < 5000:
            return 0.8   # 김
        else:
            return 0.6   # 너무 김
    
    def _evaluate_structural_complexity(self, content: str) -> float:
        """구조적 복잡성을 평가합니다."""
        complexity_indicators = [
            len(re.findall(r'\n', content)) * 0.01,  # 줄바꿈 수
            len(re.findall(r'```', content)) * 0.1,   # 코드 블록 수
            len(re.findall(r'[{}()\[\]]', content)) * 0.005,  # 괄호 수
            len(re.findall(r'[.!?]', content)) * 0.02,  # 문장 수
        ]
        
        return min(sum(complexity_indicators), 0.3)  # 최대 0.3
    
    def _calculate_semantic_density(self, content: str) -> float:
        """시맨틱 밀도를 계산합니다."""
        if not content:
            return 0.0
        
        words = content.split()
        if not words:
            return 0.0
        
        # 의미있는 단어들 (명사, 동사, 형용사 등)
        meaningful_words = [
            word for word in words 
            if len(word) > 2 and not word.lower() in ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for']
        ]
        
        # 고유 단어 비율
        unique_ratio = len(set(meaningful_words)) / max(len(meaningful_words), 1)
        
        # 평균 단어 길이
        avg_word_length = sum(len(word) for word in meaningful_words) / max(len(meaningful_words), 1)
        
        # 시맨틱 밀도 = 고유성 * 단어길이팩터
        density = unique_ratio * min(avg_word_length / 8.0, 1.0)
        
        return min(density, 1.0)
    
    def _classify_content_type(self, content: str) -> str:
        """컨텐츠 타입을 분류합니다."""
        content_lower = content.lower()
        
        type_patterns = {
            'code': [r'def |class |function|import|const|let|var|\{|\}|;$'],
            'error': [r'error|exception|fail|traceback|stack'],
            'dialogue': [r'사용자:|user:|assistant:|질문:|답변:'],
            'analysis': [r'분석|analysis|result|결과|평가|evaluation'],
            'instruction': [r'지시|instruction|command|요청|request']
        }
        
        for content_type, patterns in type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    return content_type
        
        return 'general'
    
    def _extract_key_concepts(self, content: str) -> List[str]:
        """핵심 개념을 추출합니다."""
        concepts = []
        
        for pattern in self.concept_extractors:
            matches = re.findall(pattern, content, re.IGNORECASE)
            concepts.extend(matches)
        
        # 단어 빈도 기반 핵심 단어 추출
        words = re.findall(r'\b\w{3,}\b', content.lower())
        word_freq = Counter(words)
        frequent_words = [word for word, count in word_freq.most_common(10) if count > 1]
        
        concepts.extend(frequent_words)
        
        return list(set(concepts))[:20]  # 최대 20개
    
    def _calculate_redundancy_level(self, content: str) -> float:
        """중복성 수준을 계산합니다."""
        redundancy_score = 0.0
        
        for pattern in self.redundancy_patterns:
            matches = len(re.findall(pattern, content.lower(), re.IGNORECASE))
            redundancy_score += matches * 0.1
        
        # 반복되는 문장 패턴 감지
        sentences = re.split(r'[.!?]', content)
        if len(sentences) > 1:
            sentence_similarity = self._calculate_sentence_similarity(sentences)
            redundancy_score += sentence_similarity * 0.3
        
        return min(redundancy_score, 1.0)
    
    def _calculate_sentence_similarity(self, sentences: List[str]) -> float:
        """문장 간 유사도를 계산합니다."""
        if len(sentences) < 2:
            return 0.0
        
        similarities = []
        for i in range(len(sentences)):
            for j in range(i + 1, len(sentences)):
                sim = self._simple_similarity(sentences[i], sentences[j])
                similarities.append(sim)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        """간단한 텍스트 유사도를 계산합니다."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _perform_intelligent_compression(self, contexts: List[str]) -> str:
        """지능형 압축을 수행합니다."""
        if not contexts:
            return ""
        
        # 1. 각 컨텍스트의 핵심 정보 추출
        key_info_parts = []
        seen_concepts = set()
        
        for context in contexts:
            # 중요도 분석
            importance = self.analyze_context_importance(context)
            
            if importance < self.min_importance_threshold:
                continue  # 중요도가 낮으면 제외
            
            # 핵심 개념 추출
            concepts = self._extract_key_concepts(context)
            new_concepts = [c for c in concepts if c not in seen_concepts]
            
            if new_concepts or importance > 0.7:  # 새로운 개념이 있거나 중요도가 높으면 포함
                compressed_context = self._compress_single_context(context, importance)
                key_info_parts.append(compressed_context)
                seen_concepts.update(concepts)
        
        # 2. 압축된 부분들을 연결
        compressed_result = "\n\n".join(key_info_parts)
        
        # 3. 최종 정리
        final_compressed = self._final_polish(compressed_result)
        
        return final_compressed
    
    def _compress_single_context(self, context: str, importance: float) -> str:
        """단일 컨텍스트를 압축합니다."""
        # 중요도에 따른 압축 비율 결정
        if importance > 0.8:
            return context  # 거의 압축 안함
        elif importance > 0.6:
            return self._moderate_compression(context)
        else:
            return self._aggressive_compression(context)
    
    def _moderate_compression(self, context: str) -> str:
        """중간 정도 압축"""
        lines = context.split('\n')
        important_lines = []
        
        for line in lines:
            if any(re.search(pattern[0], line, re.IGNORECASE) 
                   for pattern in self.importance_patterns.values()):
                important_lines.append(line)
            elif len(line.strip()) > 20:  # 의미있는 길이의 줄만 유지
                important_lines.append(line[:100] + "..." if len(line) > 100 else line)
        
        return '\n'.join(important_lines)
    
    def _aggressive_compression(self, context: str) -> str:
        """적극적 압축"""
        concepts = self._extract_key_concepts(context)
        content_type = self._classify_content_type(context)
        
        summary = f"[{content_type}] {', '.join(concepts[:5])}"
        return summary
    
    def _final_polish(self, compressed: str) -> str:
        """최종 정리 작업"""
        # 빈 줄 정리
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', compressed)
        
        # 너무 긴 줄 정리
        lines = cleaned.split('\n')
        polished_lines = []
        
        for line in lines:
            if len(line) > 200:
                polished_lines.append(line[:197] + "...")
            else:
                polished_lines.append(line)
        
        return '\n'.join(polished_lines)
    
    def _identify_removed_content(self, original: str, compressed: str) -> List[str]:
        """제거된 컨텐츠를 식별합니다."""
        original_lines = set(original.split('\n'))
        compressed_lines = set(compressed.split('\n'))
        removed_lines = original_lines - compressed_lines
        return list(removed_lines)[:10]  # 최대 10개
    
    def _evaluate_compression_quality(self, original: str, compressed: str) -> float:
        """압축 품질을 평가합니다."""
        if not original or not compressed:
            return 0.0
        
        # 압축 비율
        compression_ratio = len(compressed) / len(original)
        
        # 핵심 개념 보존율
        original_concepts = set(self._extract_key_concepts(original))
        compressed_concepts = set(self._extract_key_concepts(compressed))
        
        concept_preservation = len(compressed_concepts & original_concepts) / max(len(original_concepts), 1)
        
        # 품질 스코어 = 개념보존율 * (1 - 과압축패널티)
        quality = concept_preservation * (2 - compression_ratio)
        
        return min(max(quality, 0.0), 1.0)
    
    def _calculate_segment_priority(self, segment: str, base_importance: float) -> float:
        """세그먼트별 우선순위를 계산합니다."""
        priority = base_importance
        
        # 길이 기반 조정
        length_factor = self._calculate_length_importance(segment)
        priority *= length_factor
        
        # 컨텐츠 타입별 가중치
        content_type = self._classify_content_type(segment)
        type_weights = {
            'error': 0.9,
            'code': 0.8, 
            'analysis': 0.7,
            'dialogue': 0.8,
            'instruction': 0.75,
            'general': 0.6
        }
        priority += type_weights.get(content_type, 0.6) * 0.2
        
        return min(priority, 1.0)
    
    def _remove_conceptual_duplicates(self, analyzed_contexts: List[Dict]) -> List[Dict]:
        """개념적 중복을 제거합니다."""
        unique_contexts = []
        seen_concept_sets = []
        
        for ctx in analyzed_contexts:
            ctx_concepts = set(ctx['concepts'])
            
            # 기존 컨텍스트들과 개념 유사도 검사
            is_duplicate = False
            for seen_concepts in seen_concept_sets:
                similarity = len(ctx_concepts & seen_concepts) / len(ctx_concepts | seen_concepts) if (ctx_concepts | seen_concepts) else 0
                if similarity > 0.7:  # 70% 이상 유사하면 중복으로 간주
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_contexts.append(ctx)
                seen_concept_sets.append(ctx_concepts)
        
        return unique_contexts
    
    def _optimize_logical_flow(self, contexts: List[Dict]) -> List[Dict]:
        """논리적 플로우를 최적화합니다."""
        # 컨텐츠 타입별 그룹화
        type_groups = defaultdict(list)
        for ctx in contexts:
            content_type = self._classify_content_type(ctx['content'])
            type_groups[content_type].append(ctx)
        
        # 최적 순서: instruction -> dialogue -> code -> analysis -> error -> general
        optimal_order = ['instruction', 'dialogue', 'code', 'analysis', 'error', 'general']
        
        optimized_flow = []
        for content_type in optimal_order:
            if content_type in type_groups:
                # 각 그룹 내에서는 중요도 순으로 정렬
                sorted_group = sorted(type_groups[content_type], key=lambda x: x['importance'], reverse=True)
                optimized_flow.extend(sorted_group)
        
        return optimized_flow
    
    def _calculate_average_importance(self) -> float:
        """평균 중요도 스코어를 계산합니다."""
        if not self.analysis_cache:
            return 0.0
        
        scores = [result.importance_score for result in self.analysis_cache.values()]
        return sum(scores) / len(scores)
    
    def _calculate_average_compression(self) -> float:
        """평균 압축 비율을 계산합니다."""
        if not self.compression_cache:
            return 1.0
        
        ratios = [result.compression_ratio for result in self.compression_cache.values()]
        return sum(ratios) / len(ratios)
    
    def _get_common_content_types(self) -> Dict[str, int]:
        """일반적인 컨텐츠 타입들을 반환합니다."""
        type_counts = Counter(result.content_type for result in self.analysis_cache.values())
        return dict(type_counts.most_common(5))
    
    def _calculate_processing_efficiency(self) -> float:
        """처리 효율성을 계산합니다."""
        if not self.analysis_cache:
            return 0.0
        
        # 캐시 히트율과 평균 품질 스코어로 효율성 측정
        cache_efficiency = min(len(self.analysis_cache) / 100, 1.0)  # 캐시 활용도
        avg_quality = self._calculate_average_importance()
        
        return (cache_efficiency + avg_quality) / 2


# 편의 함수들
def create_context_processor() -> IntelligentContextProcessor:
    """Intelligent Context Processor 인스턴스를 생성합니다."""
    return IntelligentContextProcessor()


def quick_context_analysis(content: str) -> Dict[str, Any]:
    """빠른 컨텍스트 분석을 수행합니다."""
    processor = create_context_processor()
    
    importance = processor.analyze_context_importance(content)
    concepts = processor._extract_key_concepts(content)
    content_type = processor._classify_content_type(content)
    
    return {
        'importance_score': importance,
        'key_concepts': concepts,
        'content_type': content_type,
        'length': len(content),
        'semantic_density': processor._calculate_semantic_density(content)
    }


if __name__ == "__main__":
    # 테스트용 실행
    logging.basicConfig(level=logging.INFO)
    
    print("🧠 Intelligent Context Processor 테스트")
    
    # 테스트 컨텍스트들
    test_contexts = [
        "사용자가 새로운 기능 구현을 요청했습니다. 중요한 결정이 필요합니다.",
        "def process_data(data): return data.transform()",
        "오류가 발생했습니다: TypeError in line 42",
        "분석 결과: 성능이 20% 향상되었습니다.",
        "같은 내용을 다시 반복해서 설명드리겠습니다."
    ]
    
    processor = create_context_processor()
    
    # 중요도 분석 테스트
    print("\n📊 중요도 분석:")
    for i, context in enumerate(test_contexts):
        importance = processor.analyze_context_importance(context)
        print(f"  {i+1}. {context[:50]}... → {importance:.3f}")
    
    # 압축 테스트
    print("\n🗜️  압축 테스트:")
    compressed = processor.compress_redundant_context(test_contexts)
    print(f"  원본: {sum(len(c) for c in test_contexts)} 문자")
    print(f"  압축: {len(compressed)} 문자")
    print(f"  압축률: {len(compressed) / sum(len(c) for c in test_contexts) * 100:.1f}%")
    
    # 우선순위 테스트
    print("\n🎯 우선순위 테스트:")
    prioritized = processor.prioritize_context_segments(test_contexts)
    for i, (segment, priority) in enumerate(prioritized[:3]):
        print(f"  {i+1}. {segment[:50]}... → {priority:.3f}")
    
    print("\n✅ Intelligent Context Processor 준비 완료")