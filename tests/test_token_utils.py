from greeum.token_utils import count_tokens, truncate_by_tokens

def test_count_tokens():
    text = "안녕 하세요 여러분"
    assert count_tokens(text) == 3


def test_truncate():
    text = "a b c d e"
    truncated = truncate_by_tokens(text, 3)
    assert count_tokens(truncated) <= 3 