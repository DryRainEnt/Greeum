#!/usr/bin/env python3
"""
토큰 유틸리티 함수들

이 모듈은 텍스트의 토큰 수를 계산하고 토큰 기반으로 텍스트를 자르는 기능을 제공합니다.
"""

import re
from typing import List, Optional


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    텍스트의 토큰 수를 계산합니다.
    
    Args:
        text: 토큰 수를 계산할 텍스트
        model: 사용할 모델 (현재는 간단한 추정치 사용)
        
    Returns:
        토큰 수
    """
    if not text:
        return 0
    
    # 간단한 토큰 추정 (실제 토큰화보다는 근사치)
    # 공백으로 분리된 단어 수 + 특수문자 수
    words = text.split()
    special_chars = len(re.findall(r'[^\w\s]', text))
    
    # 한국어의 경우 더 정확한 추정을 위해 문자 수도 고려
    korean_chars = len(re.findall(r'[가-힣]', text))
    
    # 기본 토큰 수 = 단어 수 + 특수문자 수
    base_tokens = len(words) + special_chars
    
    # 한국어 문자는 추가 토큰으로 계산
    korean_tokens = korean_chars * 0.5  # 한국어는 보통 더 많은 토큰 사용
    
    return int(base_tokens + korean_tokens)


def truncate_by_tokens(text: str, max_tokens: int, model: str = "gpt-3.5-turbo") -> str:
    """
    텍스트를 지정된 토큰 수로 자릅니다.
    
    Args:
        text: 자를 텍스트
        max_tokens: 최대 토큰 수
        model: 사용할 모델
        
    Returns:
        잘린 텍스트
    """
    if not text:
        return text
    
    current_tokens = count_tokens(text, model)
    
    if current_tokens <= max_tokens:
        return text
    
    # 이진 탐색으로 적절한 길이 찾기
    left, right = 0, len(text)
    best_length = 0
    
    while left <= right:
        mid = (left + right) // 2
        truncated = text[:mid]
        tokens = count_tokens(truncated, model)
        
        if tokens <= max_tokens:
            best_length = mid
            left = mid + 1
        else:
            right = mid - 1
    
    return text[:best_length]


def estimate_tokens_for_embedding(text: str) -> int:
    """
    임베딩을 위한 토큰 수를 추정합니다.
    
    Args:
        text: 토큰 수를 추정할 텍스트
        
    Returns:
        추정된 토큰 수
    """
    if not text:
        return 0
    
    # 임베딩 모델은 보통 더 긴 토큰을 처리할 수 있음
    return count_tokens(text) * 2


def split_text_by_tokens(text: str, max_tokens: int, overlap: int = 50) -> List[str]:
    """
    텍스트를 토큰 수에 따라 여러 조각으로 나눕니다.
    
    Args:
        text: 나눌 텍스트
        max_tokens: 각 조각의 최대 토큰 수
        overlap: 조각 간 겹치는 토큰 수
        
    Returns:
        텍스트 조각들의 리스트
    """
    if not text:
        return []
    
    if count_tokens(text) <= max_tokens:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # 현재 위치에서 시작하는 조각의 끝 찾기
        end = start + max_tokens * 4  # 대략적인 문자 수 추정
        if end > len(text):
            end = len(text)
        
        # 단어 경계에서 자르기
        while end > start and end < len(text) and text[end] not in ' \n\t':
            end -= 1
        
        if end <= start:
            end = start + max_tokens * 4
            if end > len(text):
                end = len(text)
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # 다음 조각의 시작 위치 (겹치는 부분 제외)
        start = end - overlap
        if start < 0:
            start = end
    
    return chunks
