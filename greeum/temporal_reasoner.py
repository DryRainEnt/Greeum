import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
import json
import os

class TemporalReasoner:
    """시간적 추론 및 질의 처리 클래스"""
    
    def __init__(self, db_manager=None, default_language="auto"):
        """
        시간적 추론 처리기 초기화
        
        Args:
            db_manager: 데이터베이스 관리자 (없으면 검색만 가능)
            default_language: 기본 언어 설정 ("ko", "en", "ja", "zh", "es" 또는 "auto")
        """
        self.db_manager = db_manager
        self.default_language = default_language
        self._setup_temporal_patterns()
        self._setup_date_formats()
    
    def _detect_language(self, text: str) -> str:
        """
        텍스트의 언어 감지
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            언어 코드 ("ko", "en", "ja", "zh", "es")
        """
        # 간단한 휴리스틱 기반 언어 감지
        # 실제 구현에서는 langdetect 등의 라이브러리 사용 권장
        
        # 한글 문자 비율
        ko_chars = len(re.findall(r'[가-힣]', text))
        
        # 일본어 문자 비율
        ja_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF]', text))
        
        # 중국어 문자 비율
        zh_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        
        # 영어 문자 비율
        en_chars = len(re.findall(r'[a-zA-Z]', text))
        
        # 스페인어 특수 문자 (ñ, á, é, í, ó, ú, ü 등)
        es_chars = len(re.findall(r'[áéíóúüñ¿¡]', text.lower()))
        
        # 각 언어별 점수 계산
        lang_scores = {
            "ko": ko_chars * 2,  # 한글은 가중치를 높게 설정
            "ja": ja_chars * 2,  # 일본어도 가중치를 높게 설정
            "zh": zh_chars * 2,  # 중국어도 가중치를 높게 설정
            "en": en_chars,
            "es": en_chars * 0.5 + es_chars * 5  # 스페인어 특수 문자에 높은 가중치
        }
        
        # 최고 점수 언어 반환
        if max(lang_scores.values()) > 0:
            return max(lang_scores.items(), key=lambda x: x[1])[0]
        else:
            return "en"  # 기본값은 영어
    
    def _setup_temporal_patterns(self):
        """시간 표현 패턴 설정"""
        # 한국어 시간 표현
        self.ko_time_patterns = {
            # 상대적 기간 (정확한 매칭)
            "어제": lambda: timedelta(days=1),
            "그저께": lambda: timedelta(days=2),
            "그제": lambda: timedelta(days=2),
            "오늘": lambda: timedelta(days=0),
            "지금": lambda: timedelta(days=0),
            "방금": lambda: timedelta(minutes=5),
            "조금 전": lambda: timedelta(hours=1),
            "지난주": lambda: timedelta(days=7),
            "저번 주": lambda: timedelta(days=7),
            "지난달": lambda: timedelta(days=30),
            "저번 달": lambda: timedelta(days=30),
            "지난해": lambda: timedelta(days=365),
            "작년": lambda: timedelta(days=365),
            "재작년": lambda: timedelta(days=730),
            
            # 정규식 패턴
            "(\d+)초 전": lambda m: timedelta(seconds=int(m.group(1))),
            "(\d+)분 전": lambda m: timedelta(minutes=int(m.group(1))),
            "(\d+)시간 전": lambda m: timedelta(hours=int(m.group(1))),
            "(\d+)일 전": lambda m: timedelta(days=int(m.group(1))),
            "(\d+)주 전": lambda m: timedelta(weeks=int(m.group(1))),
            "(\d+)개월 전": lambda m: timedelta(days=int(m.group(1)) * 30),
            "(\d+)달 전": lambda m: timedelta(days=int(m.group(1)) * 30),
            "(\d+)년 전": lambda m: timedelta(days=int(m.group(1)) * 365),
            "약 (\d+)시간 전": lambda m: timedelta(hours=int(m.group(1))),
            "약 (\d+)일 전": lambda m: timedelta(days=int(m.group(1))),
            
            # 모호한 기간
            "얼마 전": lambda: timedelta(hours=6),
            "최근": lambda: timedelta(days=3),
            "며칠 전": lambda: timedelta(days=3),
            "몇 주 전": lambda: timedelta(weeks=2),
            "몇 달 전": lambda: timedelta(days=60),
            "한참 전": lambda: timedelta(days=100),
            "옛날": lambda: timedelta(days=365),
        }
        
        # 한국어 미래 시간 패턴
        self.ko_future_patterns = {
            "내일": lambda: timedelta(days=1),
            "모레": lambda: timedelta(days=2),
            "다음 주": lambda: timedelta(days=7),
            "다음 달": lambda: timedelta(days=30),
            "다음 해": lambda: timedelta(days=365),
            "내년": lambda: timedelta(days=365),
            
            "(\d+)일 후": lambda m: timedelta(days=int(m.group(1))),
            "(\d+)주 후": lambda m: timedelta(weeks=int(m.group(1))),
            "(\d+)개월 후": lambda m: timedelta(days=int(m.group(1)) * 30),
            "(\d+)년 후": lambda m: timedelta(days=int(m.group(1)) * 365),
        }
        
        # 영어 시간 표현
        self.en_time_patterns = {
            # 상대적 기간 (정확한 매칭)
            "yesterday": lambda: timedelta(days=1),
            "the day before yesterday": lambda: timedelta(days=2),
            "today": lambda: timedelta(days=0),
            "now": lambda: timedelta(days=0),
            "just now": lambda: timedelta(minutes=5),
            "a moment ago": lambda: timedelta(minutes=10),
            "recently": lambda: timedelta(days=3),
            "last week": lambda: timedelta(days=7),
            "last month": lambda: timedelta(days=30),
            "last year": lambda: timedelta(days=365),
            "a year ago": lambda: timedelta(days=365),
            "two years ago": lambda: timedelta(days=730),
            
            # 정규식 패턴
            "(\d+) seconds ago": lambda m: timedelta(seconds=int(m.group(1))),
            "(\d+) minutes ago": lambda m: timedelta(minutes=int(m.group(1))),
            "(\d+) hours ago": lambda m: timedelta(hours=int(m.group(1))),
            "(\d+) days ago": lambda m: timedelta(days=int(m.group(1))),
            "(\d+) weeks ago": lambda m: timedelta(weeks=int(m.group(1))),
            "(\d+) months ago": lambda m: timedelta(days=int(m.group(1)) * 30),
            "(\d+) years ago": lambda m: timedelta(days=int(m.group(1)) * 365),
            "about (\d+) hours ago": lambda m: timedelta(hours=int(m.group(1))),
            "about (\d+) days ago": lambda m: timedelta(days=int(m.group(1))),
            
            # 모호한 기간
            "a while ago": lambda: timedelta(hours=6),
            "some time ago": lambda: timedelta(days=3),
            "a few days ago": lambda: timedelta(days=3),
            "a few weeks ago": lambda: timedelta(weeks=2),
            "a few months ago": lambda: timedelta(days=60),
            "long ago": lambda: timedelta(days=100),
            "ages ago": lambda: timedelta(days=365),
        }
        
        # 영어 미래 시간 패턴
        self.en_future_patterns = {
            "tomorrow": lambda: timedelta(days=1),
            "the day after tomorrow": lambda: timedelta(days=2),
            "next week": lambda: timedelta(days=7),
            "next month": lambda: timedelta(days=30),
            "next year": lambda: timedelta(days=365),
            
            "in (\d+) days": lambda m: timedelta(days=int(m.group(1))),
            "in (\d+) weeks": lambda m: timedelta(weeks=int(m.group(1))),
            "in (\d+) months": lambda m: timedelta(days=int(m.group(1)) * 30),
            "in (\d+) years": lambda m: timedelta(days=int(m.group(1)) * 365),
        }
        
        # 언어별 패턴 사전
        self.time_patterns = {
            "ko": self.ko_time_patterns,
            "en": self.en_time_patterns,
        }
        
        self.future_patterns = {
            "ko": self.ko_future_patterns,
            "en": self.en_future_patterns,
        }
    
    def _setup_date_formats(self):
        """날짜 형식 패턴 설정"""
        # 언어별 날짜 형식 패턴
        self.date_patterns_by_lang = {
            "ko": [
                # ISO 형식 (2023-05-01)
                r"(\d{4}-\d{2}-\d{2})",
                # 년월일 형식 (2023년 5월 1일)
                r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",
                # 월일 형식 (5월 1일)
                r"(\d{1,2})월\s*(\d{1,2})일",
                # 슬래시 형식 (2023/05/01)
                r"(\d{4})/(\d{1,2})/(\d{1,2})",
            ],
            "en": [
                # ISO 형식 (2023-05-01)
                r"(\d{4}-\d{2}-\d{2})",
                # 미국식 형식 (May 1, 2023)
                r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})",
                # 영국식 형식 (1 May 2023)
                r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
                # 슬래시 형식 (05/01/2023) - 미국식
                r"(\d{1,2})/(\d{1,2})/(\d{4})",
            ]
        }
        
        # 기본 날짜 패턴 설정 (이전 버전과의 호환성 유지)
        self.date_patterns = self.date_patterns_by_lang["ko"]
    
    def extract_time_references(self, query: str) -> List[Dict[str, Any]]:
        """
        쿼리에서 시간 참조 추출
        
        Args:
            query: 검색 쿼리
            
        Returns:
            시간 참조 목록 (용어, 델타, 시작일 포함)
        """
        time_refs = []
        
        # 현재 시간
        now = datetime.now()
        
        # 언어 감지
        if self.default_language == "auto":
            lang = self._detect_language(query)
        else:
            lang = self.default_language
            
        # 지원하지 않는 언어는 영어로 대체
        if lang not in self.time_patterns:
            lang = "en"
        
        # 선택된 언어의 패턴 사전 가져오기
        time_patterns = self.time_patterns.get(lang, self.time_patterns["en"])
        future_patterns = self.future_patterns.get(lang, self.future_patterns["en"])
        
        # 1. 일반 문자열 패턴 (과거)
        for term, delta_func in time_patterns.items():
            if "(" not in term and term in query:
                delta = delta_func()
                time_refs.append({
                    "term": term,
                    "delta": delta,
                    "is_future": False,
                    "from_date": now - delta,
                    "to_date": now
                })
        
        # 2. 정규식 패턴 (과거)
        for pattern, delta_func in time_patterns.items():
            if "(" in pattern:  # 정규식 패턴 (캡쳐 그룹 포함)
                try:
                    regex = re.compile(pattern)
                    matches = regex.finditer(query)
                    for match in matches:
                        try:
                            delta = delta_func(match)
                            time_refs.append({
                                "term": match.group(0),
                                "delta": delta,
                                "is_future": False,
                                "from_date": now - delta,
                                "to_date": now
                            })
                        except Exception as e:
                            print(f"시간 표현 처리 에러 - {match.group(0)}: {e}")
                            continue
                except Exception as e:
                    print(f"정규식 컴파일 에러 - {pattern}: {e}")
                    continue
        
        # 3. 일반 문자열 패턴 (미래)
        for term, delta_func in future_patterns.items():
            if "(" not in term and term in query:
                delta = delta_func()
                time_refs.append({
                    "term": term,
                    "delta": delta,
                    "is_future": True,
                    "from_date": now,
                    "to_date": now + delta
                })
        
        # 4. 정규식 패턴 (미래)
        for pattern, delta_func in future_patterns.items():
            if "(" in pattern:  # 정규식 패턴 (캡쳐 그룹 포함)
                try:
                    regex = re.compile(pattern)
                    matches = regex.finditer(query)
                    for match in matches:
                        try:
                            delta = delta_func(match)
                            time_refs.append({
                                "term": match.group(0),
                                "delta": delta,
                                "is_future": True,
                                "from_date": now,
                                "to_date": now + delta
                            })
                        except Exception as e:
                            print(f"시간 표현 처리 에러 - {match.group(0)}: {e}")
                            continue
                except Exception as e:
                    print(f"정규식 컴파일 에러 - {pattern}: {e}")
                    continue
        
        # 5. 특정 날짜 패턴 검색
        date_patterns_to_use = self.date_patterns_by_lang.get(lang, self.date_patterns)
        for pattern in date_patterns_to_use:
            matches = re.finditer(pattern, query)
            for match in matches:
                try:
                    if pattern == r"(\d{4}-\d{2}-\d{2})":
                        # ISO 형식
                        date_str = match.group(1)
                        target_date = datetime.fromisoformat(date_str)
                    elif pattern == r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일":
                        # 년월일 형식 (한국어)
                        year = int(match.group(1))
                        month = int(match.group(2))
                        day = int(match.group(3))
                        target_date = datetime(year, month, day)
                    elif pattern == r"(\d{1,2})월\s*(\d{1,2})일":
                        # 월일 형식 (한국어, 현재 년도 가정)
                        month = int(match.group(1))
                        day = int(match.group(2))
                        target_date = datetime(now.year, month, day)
                        # 미래 날짜인 경우 작년으로 조정
                        if target_date > now:
                            target_date = datetime(now.year - 1, month, day)
                    elif pattern == r"(\d{4})/(\d{1,2})/(\d{1,2})":
                        # 슬래시 형식
                        year = int(match.group(1))
                        month = int(match.group(2))
                        day = int(match.group(3))
                        target_date = datetime(year, month, day)
                    elif pattern == r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})":
                        # 미국식 형식 (영어)
                        month_name = match.group(1)
                        month_names = ["January", "February", "March", "April", "May", "June", 
                                       "July", "August", "September", "October", "November", "December"]
                        month = month_names.index(month_name) + 1
                        day = int(match.group(2))
                        year = int(match.group(3))
                        target_date = datetime(year, month, day)
                    elif pattern == r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})":
                        # 영국식 형식 (영어)
                        day = int(match.group(1))
                        month_name = match.group(2)
                        month_names = ["January", "February", "March", "April", "May", "June", 
                                       "July", "August", "September", "October", "November", "December"]
                        month = month_names.index(month_name) + 1
                        year = int(match.group(3))
                        target_date = datetime(year, month, day)
                    elif pattern == r"(\d{1,2})/(\d{1,2})/(\d{4})":
                        # 슬래시 형식 (미국식, MM/DD/YYYY)
                        month = int(match.group(1))
                        day = int(match.group(2))
                        year = int(match.group(3))
                        target_date = datetime(year, month, day)
                    else:
                        continue
                    
                    # 날짜 범위 설정 (해당 날짜의 시작부터 끝)
                    from_date = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
                    to_date = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)
                    
                    time_refs.append({
                        "term": match.group(0),
                        "is_specific_date": True,
                        "from_date": from_date,
                        "to_date": to_date
                    })
                except (ValueError, IndexError) as e:
                    print(f"Error processing date match '{match.group(0)}': {e}")
                    continue
        
        return time_refs
    
    def get_most_specific_time_reference(self, time_refs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        가장 구체적인 시간 참조 선택
        
        Args:
            time_refs: 시간 참조 목록
            
        Returns:
            가장 구체적인 시간 참조
        """
        if not time_refs:
            return None
            
        # 특정 날짜가 있으면 가장 우선순위 높음
        specific_dates = [ref for ref in time_refs if ref.get("is_specific_date", False)]
        if specific_dates:
            return specific_dates[0]
        
        # 델타 기준으로 정렬 (작은 델타 = 더 구체적)
        delta_refs = [ref for ref in time_refs if "delta" in ref]
        if not delta_refs:
            return time_refs[0]
            
        # 정규식 패턴 (숫자 포함)이 더 구체적이라고 가정
        regex_refs = [ref for ref in delta_refs if any(c.isdigit() for c in ref["term"])]
        if regex_refs:
            # 가장 작은 범위 (가장 구체적)
            return min(regex_refs, key=lambda x: x["delta"])
        
        # 일반 패턴 중 가장 작은 범위
        return min(delta_refs, key=lambda x: x["delta"])
    
    def search_by_time_reference(self, query: str, margin_hours: int = 12) -> Dict[str, Any]:
        """
        시간 참조 기반 메모리 검색
        
        Args:
            query: 검색 쿼리
            margin_hours: 시간 여유 (경계 확장, 시간 단위)
            
        Returns:
            검색 결과 및 메타데이터
        """
        if not self.db_manager:
            return {
                "error": "데이터베이스 관리자가 설정되지 않았습니다.",
                "query": query,
                "time_refs": []
            }
            
        # 1. 시간 참조 추출
        time_refs = self.extract_time_references(query)
        if not time_refs:
            return {
                "query": query,
                "time_refs": [],
                "blocks": []
            }
            
        # 2. 가장 구체적인 시간 참조 선택
        time_ref = self.get_most_specific_time_reference(time_refs)
        
        # 3. 시간 범위 계산 (여유 추가)
        margin = timedelta(hours=margin_hours)
        from_date = time_ref["from_date"] - margin
        to_date = time_ref["to_date"] + margin
        
        # 4. 데이터베이스 검색
        blocks = self.db_manager.search_blocks_by_date_range(
            from_date.isoformat(),
            to_date.isoformat()
        )
        
        return {
            "query": query,
            "time_ref": time_ref,
            "time_refs": time_refs,
            "search_range": {
                "from_date": from_date.isoformat(),
                "to_date": to_date.isoformat()
            },
            "blocks": blocks
        }
    
    def hybrid_search(self, query: str, embedding: List[float], keywords: List[str], 
                     time_weight: float = 0.3, embedding_weight: float = 0.5, 
                     keyword_weight: float = 0.2, top_k: int = 5) -> Dict[str, Any]:
        """
        시간, 임베딩, 키워드 기반 하이브리드 검색
        
        Args:
            query: 검색 쿼리
            embedding: 쿼리 임베딩
            keywords: 추출된 키워드
            time_weight: 시간 가중치
            embedding_weight: 임베딩 가중치
            keyword_weight: 키워드 가중치
            top_k: 상위 k개 결과 반환
            
        Returns:
            하이브리드 검색 결과
        """
        if not self.db_manager:
            return {
                "error": "데이터베이스 관리자가 설정되지 않았습니다.",
                "query": query
            }
            
        # 1. 시간 참조 기반 검색
        time_result = self.search_by_time_reference(query)
        time_blocks = time_result.get("blocks", [])
        
        # 시간 참조가 없으면 다른 검색 방법 가중치 조정
        has_time_ref = bool(time_result.get("time_refs"))
        if not has_time_ref:
            embedding_weight += time_weight / 2
            keyword_weight += time_weight / 2
            time_weight = 0
        
        # 2. 임베딩 기반 검색
        embedding_blocks = self.db_manager.search_blocks_by_embedding(embedding, top_k=top_k*2)
        
        # 3. 키워드 기반 검색
        keyword_blocks = self.db_manager.search_blocks_by_keyword(keywords, limit=top_k*2)
        
        # 4. 결과 합치기 (가중치 부여)
        block_scores = {}
        
        # 시간 기반 점수
        for block in time_blocks:
            block_index = block.get("block_index")
            if block_index is not None:
                if block_index not in block_scores:
                    block_scores[block_index] = {"block": block, "score": 0}
                block_scores[block_index]["score"] += time_weight
        
        # 임베딩 기반 점수
        for idx, block in enumerate(embedding_blocks):
            block_index = block.get("block_index")
            if block_index is not None:
                if block_index not in block_scores:
                    block_scores[block_index] = {"block": block, "score": 0}
                # 유사도 점수 반영
                similarity = block.get("similarity", 0)
                # 순위에 따른 감쇠 적용
                rank_decay = max(0, 1 - (idx / (top_k * 2)))
                block_scores[block_index]["score"] += embedding_weight * similarity * rank_decay
        
        # 키워드 기반 점수
        for idx, block in enumerate(keyword_blocks):
            block_index = block.get("block_index")
            if block_index is not None:
                if block_index not in block_scores:
                    block_scores[block_index] = {"block": block, "score": 0}
                # 순위에 따른 감쇠 적용
                rank_decay = max(0, 1 - (idx / (top_k * 2)))
                block_scores[block_index]["score"] += keyword_weight * rank_decay
        
        # 5. 점수 기준 정렬
        sorted_blocks = sorted(
            block_scores.values(), 
            key=lambda x: x["score"], 
            reverse=True
        )
        
        # 6. 상위 k개 결과 반환
        top_blocks = sorted_blocks[:top_k]
        for item in top_blocks:
            item["block"]["relevance_score"] = item["score"]
        
        return {
            "query": query,
            "time_info": time_result.get("time_ref"),
            "weights": {
                "time": time_weight,
                "embedding": embedding_weight,
                "keyword": keyword_weight
            },
            "blocks": [item["block"] for item in top_blocks]
        }


# 시간 표현 평가 함수 (테스트용)
def evaluate_temporal_query(query: str, language: str = "auto") -> Dict[str, Any]:
    """
    시간 표현 평가 (테스트용)
    
    Args:
        query: 평가할 쿼리
        language: 언어 설정 ("ko", "en" 또는 "auto")
        
    Returns:
        평가 결과
    """
    reasoner = TemporalReasoner(default_language=language)
    
    # 자동 언어 감지가 활성화된 경우, 감지된 언어 표시
    detected_lang = reasoner._detect_language(query) if language == "auto" else language
    
    time_refs = reasoner.extract_time_references(query)
    
    if not time_refs:
        return {
            "query": query,
            "language": detected_lang,
            "detected": False,
            "message": "시간 표현이 감지되지 않았습니다."
        }
    
    # 가장 구체적인 시간 참조 선택
    best_ref = reasoner.get_most_specific_time_reference(time_refs)
    
    return {
        "query": query,
        "language": detected_lang,
        "detected": True,
        "time_refs": time_refs,
        "best_ref": best_ref,
        "message": f"감지된 시간 표현: {best_ref['term']}"
    } 