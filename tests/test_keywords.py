from greeum.text_utils import extract_keywords_advanced

def test_advanced_keywords():
    text = "파이썬으로 중요한 머신러닝 프로젝트를 진행하고 있습니다."
    kws = extract_keywords_advanced(text, max_keywords=3)
    assert isinstance(kws, list) and len(kws) <= 3 