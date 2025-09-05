"""Utility functions for rough token estimation.
현재는 whitespace split 기반으로 단순 토큰 수를 계산한다.
후에 tiktoken / transformers 토크나이저로 대체 가능.
"""
from __future__ import annotations

def count_tokens(text: str) -> int:
    """매우 단순한 토큰 카운트 (whitespace 기준)."""
    return len(text.strip().split())


def truncate_by_tokens(text: str, max_tokens: int) -> str:
    tokens = text.strip().split()
    if len(tokens) <= max_tokens:
        return text
    return " ".join(tokens[:max_tokens]) + "…" 