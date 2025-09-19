import pytest
from greeum.token_utils import count_tokens, truncate_by_tokens

@pytest.mark.fast
def test_count_tokens():
    text = "안녕 하세요 여러분"
    # 한국어 문자 6개 * 0.5 + 단어 3개 = 6개 토큰 (실제로는 7개)
    result = count_tokens(text)
    assert result >= 6  # 최소 6개 이상의 토큰


@pytest.mark.fast
def test_truncate():
    text = "a b c d e"
    truncated = truncate_by_tokens(text, 3)
    assert count_tokens(truncated) <= 3 