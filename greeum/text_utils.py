import re
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from collections import Counter
import json
from datetime import datetime
import logging
try:
    from keybert import KeyBERT  # type: ignore
    _kw_model = KeyBERT(model="all-MiniLM-L6-v2")
except Exception:
    _kw_model = None

logger = logging.getLogger(__name__)

# numpy 타입을 Python 기본 타입으로 변환하는 유틸리티 함수 추가
def convert_numpy_types(obj: Any) -> Any:
    """
    numpy 데이터 타입을 Python 기본 타입으로 변환
    
    Args:
        obj: 변환할 객체
        
    Returns:
        변환된 객체
    """
    if isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(round(obj.item(), 6))
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    return obj

# Multi-language emotion tag dictionary (English primary, Korean support)
EMOTION_KEYWORDS = {
    "positive": ["good", "great", "happy", "excellent", "satisfied", "grateful", "success", "amazing", "wonderful",
                "좋다", "행복", "기쁘", "즐겁", "만족", "감사", "좋은", "성공", "감동"],
    "negative": ["bad", "angry", "sad", "disappointed", "worried", "anxious", "afraid", "failure", "regret",
                "나쁘", "화나", "슬프", "실망", "걱정", "불안", "두렵", "실패", "후회"],
    "neutral": ["think", "consider", "analyze", "observe", "evaluate", "expect", "plan", "study",
               "생각", "고려", "판단", "분석", "관찰", "평가", "예상", "계획"],
    "motivated": ["want", "hope", "goal", "motivation", "passion", "will", "effort", "drive",
                 "원하", "바라", "목표", "동기", "열정", "의지", "추진", "노력"],
    "question": ["what", "how", "why", "where", "when", "who", "which", "question",
                "무엇", "어떻게", "왜", "어디", "언제", "누구", "어느", "질문"],
    "request": ["please", "help", "assist", "explain", "advise", "recommend", "teach", "show",
               "해줘", "부탁", "도와", "알려", "설명", "조언", "추천", "가르쳐"]
}

def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """
    텍스트에서 키워드 추출
    
    Args:
        text: 입력 텍스트
        max_keywords: 최대 키워드 수
        
    Returns:
        추출된 키워드 목록
    """
    # 텍스트 전처리
    text = text.lower()
    
    # Multi-language stopwords (English primary, Korean support)
    stopwords = set([
        # English stopwords
        "and", "but", "or", "so", "then", "also", "however", "therefore", "because", "through", "about", 
        "with", "for", "from", "to", "in", "on", "at", "by", "of", "the", "a", "an", "this", "that", 
        "these", "those", "i", "you", "we", "he", "she", "it", "they", "my", "your", "our", "his", 
        "her", "its", "their", "is", "are", "was", "were", "be", "being", "been", "have", "has", "had",
        "do", "does", "did", "will", "would", "should", "could", "can", "may", "might", "must",
        # Korean stopwords (maintained for compatibility)
        "그리고", "하지만", "그런데", "그래서", "또한", "물론", "또는", "혹은", 
        "그렇게", "이렇게", "저렇게", "이런", "저런", "그런", "이것", "저것", "그것",
        "나는", "너는", "우리", "저는", "제가", "나의", "너의", "우리의", "저의", "제",
        "그러나", "따라서", "때문에", "위해서", "통해", "대해", "관해", "으로", "로", 
        "이다", "있다", "없다", "된다", "한다", "있는", "없는", "되는", "하는"
    ])
    
    # 단어 추출 및 카운트
    words = re.findall(r'\b\w+\b', text)
    word_counts = Counter(w for w in words if w not in stopwords and len(w) > 1)
    
    # 가장 빈도가 높은 단어 추출
    top_keywords = [word for word, _ in word_counts.most_common(max_keywords)]
    
    return top_keywords

def extract_tags(text: str, max_tags: int = 3) -> List[str]:
    """
    텍스트에서 감정/의도 태그 추출
    
    Args:
        text: 입력 텍스트
        max_tags: 최대 태그 수
        
    Returns:
        추출된 태그 목록
    """
    text = text.lower()
    matched_tags = {}
    
    for tag, keywords in EMOTION_KEYWORDS.items():
        count = 0
        for keyword in keywords:
            if keyword in text:
                count += 1
        if count > 0:
            matched_tags[tag] = count
    
    # 가장 매칭이 많은 태그 선택
    sorted_tags = sorted(matched_tags.items(), key=lambda x: x[1], reverse=True)
    return [tag for tag, _ in sorted_tags[:max_tags]]

def generate_simple_embedding(text: str, dimension: int = 128) -> List[float]:
    """
    간단한 임베딩 생성 (실제 구현에서는 적절한 임베딩 모델 사용 필요)
    
    Args:
        text: 입력 텍스트
        dimension: 임베딩 차원
        
    Returns:
        임베딩 벡터
    """
    # 실제 구현에서는 적절한 임베딩 모델 사용 필요
    # 여기서는 간단한 문자열 기반 임베딩 생성
    
    # 일관된 시드 생성 (텍스트 길이와 첫 글자 기반)
    seed = len(text) 
    if text:
        seed += ord(text[0])
    
    # 랜덤 시드 설정
    np.random.seed(seed % 10000)  # 작은 범위의 안전한 시드 값
    
    # 임베딩 생성
    embedding = np.random.normal(0, 1, dimension)
    
    # 정규화
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
        
    return embedding.tolist()

def calculate_importance(text: str) -> float:
    """
    텍스트의 중요도 계산
    
    Args:
        text: 입력 텍스트
        
    Returns:
        중요도 점수 (0~1)
    """
    # 간단한 중요도 계산 (텍스트 길이, 키워드 수, 감정 강도 등 고려)
    length_score = min(len(text) / 200, 1.0) * 0.3
    
    # 키워드 다양성
    keywords = extract_keywords(text, max_keywords=10)
    keyword_score = min(len(keywords) / 5, 1.0) * 0.3
    
    # 감정 강도
    emotion_tags = extract_tags(text)
    emotion_score = min(len(emotion_tags) / 2, 1.0) * 0.4
    
    # 최종 점수 (0~1 범위)
    importance = length_score + keyword_score + emotion_score
    return min(importance, 1.0)

def process_user_input(text: str, extract_keywords: bool = True,
                      extract_tags: bool = True, 
                      compute_importance: bool = True,
                      compute_embedding: bool = True) -> Dict[str, Any]:
    """
    사용자 입력 텍스트 처리
    
    Args:
        text: 사용자 입력 텍스트
        extract_keywords: 키워드 추출 여부
        extract_tags: 태그 추출 여부
        compute_importance: 중요도 계산 여부
        compute_embedding: 임베딩 계산 여부
        
    Returns:
        처리된 결과 딕셔너리
    """
    result = {
        "context": text,
        "timestamp": datetime.now().isoformat()
    }
    
    # 1. 키워드 추출
    if extract_keywords:
        result["keywords"] = extract_keywords_from_text(text)
    
    # 2. 태그 추출
    if extract_tags:
        result["tags"] = extract_tags_from_text(text)
    
    # 3. 중요도 계산
    if compute_importance:
        result["importance"] = compute_text_importance(text)
    
    # 4. 임베딩 계산
    if compute_embedding:
        try:
            from .embedding_models import get_embedding
            result["embedding"] = get_embedding(text)
        except ImportError:
            # 임베딩 모듈이 없으면 간단한 해시 기반 임베딩 생성
            result["embedding"] = simple_hash_embedding(text)
    
    return result

def extract_keywords_from_text(text: str) -> List[str]:
    """
    텍스트에서 키워드 추출
    
    Args:
        text: 원본
        
    Returns:
        키워드 목록
    """
    # 간단한 키워드 추출 방법: 불용어 제거 및 명사 추출
    # 실제 구현에서는 형태소 분석기나 NLP 라이브러리 사용
    stopwords = ["은", "는", "이", "가", "을", "를", "에", "의", "과", "와", "로", "으로", 
                "이다", "있다", "하다", "되다", "않다", "그", "그리고", "또한", "그러나"]
    
    # 모든 문장 부호 및 특수 문자 제거
    clean_text = re.sub(r'[^\w\s]', ' ', text)
    
    # 단어 분리
    words = clean_text.split()
    
    # 불용어 제거 및 2글자 이상만 유지
    keywords = [word for word in words if word not in stopwords and len(word) >= 2]
    
    # 중복 제거 및 최대 10개 반환
    return list(set(keywords))[:10]

def extract_tags_from_text(text: str) -> List[str]:
    """
    텍스트에서 태그 추출
    
    Args:
        text: 원본
        
    Returns:
        태그 목록
    """
    # 간단한 규칙 기반 태그 추출
    tags = []
    
    # 감정 분석 (간단한 규칙 기반)
    positive_words = ["좋다", "기쁘다", "행복", "즐겁다", "만족", "성공"]
    negative_words = ["나쁘다", "슬프다", "실패", "불만", "문제", "걱정"]
    
    for word in positive_words:
        if word in text:
            tags.append("긍정")
            break
    
    for word in negative_words:
        if word in text:
            tags.append("부정")
            break
    
    # 주제 분석 (간단한 규칙 기반)
    if any(word in text for word in ["일", "업무", "회의", "프로젝트", "계획"]):
        tags.append("업무")
    
    if any(word in text for word in ["가족", "친구", "만남", "모임", "여행"]):
        tags.append("개인")
    
    if any(word in text for word in ["배우다", "공부", "학습", "교육", "책"]):
        tags.append("학습")
    
    # 중요도 태그
    if any(word in text for word in ["중요", "핵심", "필수", "반드시", "꼭"]):
        tags.append("중요")
    
    if any(word in text for word in ["긴급", "빨리", "즉시", "급하게", "서둘러"]):
        tags.append("긴급")
    
    return tags

def compute_text_importance(text: str) -> float:
    """
    텍스트 중요도 계산
    
    Args:
        text: 원본
        
    Returns:
        중요도 점수 (0.0 ~ 1.0)
    """
    # 간단한 규칙 기반 중요도 계산
    importance = 0.5  # 기본값
    
    # 1. 텍스트 길이 기반 (짧은 메모보다 긴 메모가 더 중요할 수 있음)
    text_length = len(text)
    if text_length > 200:
        importance += 0.1
    
    # 2. 중요 키워드 기반
    important_keywords = ["중요", "핵심", "필수", "반드시", "꼭", "긴급", "즉시"]
    for keyword in important_keywords:
        if keyword in text:
            importance += 0.1
            break
    
    # 3. 질문 포함 여부 (질문은 중요도 상승)
    if "?" in text or "질문" in text:
        importance += 0.1
    
    # 4. 날짜/시간 표현 포함 여부 (구체적인 일정은 중요도 상승)
    date_patterns = [r'\d{4}년', r'\d{1,2}월', r'\d{1,2}일', r'\d{1,2}시', r'\d{2}:\d{2}']
    for pattern in date_patterns:
        if re.search(pattern, text):
            importance += 0.1
            break
    
    # 최대값 제한
    return min(importance, 1.0)

def simple_hash_embedding(text: str, dimension: int = 768) -> List[float]:
    """
    간단한 해시 기반 임베딩 생성 (임시 대체용)
    
    Args:
        text: 원본 텍스트
        dimension: 임베딩 차원
        
    Returns:
        임베딩 벡터
    """
    import hashlib
    import numpy as np
    
    # 해시 기반 시드 생성
    hash_obj = hashlib.md5(text.encode())
    seed = int(hash_obj.hexdigest(), 16) % 100000
    
    # 시드 설정
    np.random.seed(seed)
    
    # 임베딩 생성
    embedding = np.random.normal(0, 1, dimension)
    
    # 정규화
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
        
    return embedding.tolist()

def extract_keywords_advanced(text: str, max_keywords: int = 5) -> List[str]:
    """KeyBERT 기반 고급 키워드 추출 (모델이 없으면 기본 extract_keywords fallback)"""
    if _kw_model is None:
        logger.debug("KeyBERT 모델을 찾을 수 없어 기본 키워드 추출로 대체")
        return extract_keywords(text, max_keywords=max_keywords)
    try:
        keywords = _kw_model.extract_keywords(text, top_n=max_keywords, stop_words="korean")
        return [kw for kw, _ in keywords]
    except Exception as e:
        logger.warning("KeyBERT 추출 실패: %s", e)
        return extract_keywords(text, max_keywords=max_keywords) 