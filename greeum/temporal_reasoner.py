import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
import json
import os

class TemporalReasoner:
    """시간적 추론 및 질의 처리 클래스"""
    
    def __init__(self, db_manager=None):
        """
        시간적 추론 처리기 초기화
        
        Args:
            db_manager: 데이터베이스 관리자 (없으면 검색만 가능)
        """
        self.db_manager = db_manager
        self._setup_temporal_patterns()
        self._setup_date_formats()
    
    def _setup_temporal_patterns(self):
        """시간 표현 패턴 설정"""
        self.time_patterns = {
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
            r"(\d+)초 전": lambda m: timedelta(seconds=int(m.group(1))),
            r"(\d+)분 전": lambda m: timedelta(minutes=int(m.group(1))),
            r"(\d+)시간 전": lambda m: timedelta(hours=int(m.group(1))),
            r"(\d+)일 전": lambda m: timedelta(days=int(m.group(1))),
            r"(\d+)주 전": lambda m: timedelta(weeks=int(m.group(1))),
            r"(\d+)개월 전": lambda m: timedelta(days=int(m.group(1)) * 30),
            r"(\d+)달 전": lambda m: timedelta(days=int(m.group(1)) * 30),
            r"(\d+)년 전": lambda m: timedelta(days=int(m.group(1)) * 365),
            r"약 (\d+)시간 전": lambda m: timedelta(hours=int(m.group(1))),
            r"약 (\d+)일 전": lambda m: timedelta(days=int(m.group(1))),
            
            # 모호한 기간
            "얼마 전": lambda: timedelta(hours=6),
            "최근": lambda: timedelta(days=3),
            "며칠 전": lambda: timedelta(days=3),
            "몇 주 전": lambda: timedelta(weeks=2),
            "몇 달 전": lambda: timedelta(days=60),
            "한참 전": lambda: timedelta(days=100),
            "옛날": lambda: timedelta(days=365),
        }
        
        # 미래 시간 패턴
        self.future_patterns = {
            "내일": lambda: timedelta(days=1),
            "모레": lambda: timedelta(days=2),
            "다음 주": lambda: timedelta(days=7),
            "다음 달": lambda: timedelta(days=30),
            "다음 해": lambda: timedelta(days=365),
            "내년": lambda: timedelta(days=365),
            
            r"(\d+)일 후": lambda m: timedelta(days=int(m.group(1))),
            r"(\d+)주 후": lambda m: timedelta(weeks=int(m.group(1))),
            r"(\d+)개월 후": lambda m: timedelta(days=int(m.group(1)) * 30),
            r"(\d+)년 후": lambda m: timedelta(days=int(m.group(1)) * 365),
        }
    
    def _setup_date_formats(self):
        """날짜 형식 패턴 설정"""
        self.date_patterns = [
            # ISO 형식 (2023-05-01)
            r"(\d{4}-\d{2}-\d{2})",
            # 년월일 형식 (2023년 5월 1일)
            r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일",
            # 월일 형식 (5월 1일)
            r"(\d{1,2})월\s*(\d{1,2})일",
            # 슬래시 형식 (2023/05/01)
            r"(\d{4})/(\d{1,2})/(\d{1,2})",
        ]
    
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
        
        # 1. 직접 매칭 (과거)
        for term, delta_func in self.time_patterns.items():
            if isinstance(term, str) and term in query:
                delta = delta_func()
                time_refs.append({
                    "term": term,
                    "delta": delta,
                    "is_future": False,
                    "from_date": now - delta,
                    "to_date": now
                })
        
        # 2. 정규식 매칭 (과거)
        for pattern, delta_func in self.time_patterns.items():
            if isinstance(pattern, str) and pattern.startswith('r'):
                regex = pattern[1:]  # 'r' 제거
                matches = re.finditer(regex, query)
                for match in matches:
                    delta = delta_func(match)
                    time_refs.append({
                        "term": match.group(0),
                        "delta": delta,
                        "is_future": False,
                        "from_date": now - delta,
                        "to_date": now
                    })
        
        # 3. 직접 매칭 (미래)
        for term, delta_func in self.future_patterns.items():
            if isinstance(term, str) and term in query:
                delta = delta_func()
                time_refs.append({
                    "term": term,
                    "delta": delta,
                    "is_future": True,
                    "from_date": now,
                    "to_date": now + delta
                })
        
        # 4. 정규식 매칭 (미래)
        for pattern, delta_func in self.future_patterns.items():
            if isinstance(pattern, str) and pattern.startswith('r'):
                regex = pattern[1:]  # 'r' 제거
                matches = re.finditer(regex, query)
                for match in matches:
                    delta = delta_func(match)
                    time_refs.append({
                        "term": match.group(0),
                        "delta": delta,
                        "is_future": True,
                        "from_date": now,
                        "to_date": now + delta
                    })
        
        # 5. 특정 날짜 패턴 검색
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, query)
            for match in matches:
                try:
                    if pattern == r"(\d{4}-\d{2}-\d{2})":
                        # ISO 형식
                        date_str = match.group(1)
                        target_date = datetime.fromisoformat(date_str)
                    elif pattern == r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일":
                        # 년월일 형식
                        year = int(match.group(1))
                        month = int(match.group(2))
                        day = int(match.group(3))
                        target_date = datetime(year, month, day)
                    elif pattern == r"(\d{1,2})월\s*(\d{1,2})일":
                        # 월일 형식 (현재 년도 가정)
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
                    
                    # 날짜 범위 설정 (해당 날짜의 시작부터 끝)
                    from_date = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
                    to_date = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)
                    
                    time_refs.append({
                        "term": match.group(0),
                        "is_specific_date": True,
                        "from_date": from_date,
                        "to_date": to_date
                    })
                except ValueError:
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
def evaluate_temporal_query(query: str) -> Dict[str, Any]:
    """
    시간 표현 평가 (테스트용)
    
    Args:
        query: 평가할 쿼리
        
    Returns:
        평가 결과
    """
    reasoner = TemporalReasoner()
    time_refs = reasoner.extract_time_references(query)
    
    if not time_refs:
        return {
            "query": query,
            "detected": False,
            "message": "시간 표현이 감지되지 않았습니다."
        }
    
    # 가장 구체적인 시간 참조 선택
    best_ref = reasoner.get_most_specific_time_reference(time_refs)
    
    return {
        "query": query,
        "detected": True,
        "time_refs": time_refs,
        "best_ref": best_ref,
        "message": f"감지된 시간 표현: {best_ref['term']}"
    } 