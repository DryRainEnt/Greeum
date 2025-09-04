"""
인과관계 감지 시스템 (v2.4.0.dev1)

브릿지 메모리 개념과 벡터 기반 최적화를 통한 인과관계 연결 시스템
"""
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import re
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class CausalityScore:
    """인과관계 강도 점수"""
    strength: float  # 0.0 ~ 1.0
    confidence: float  # 신뢰도
    breakdown: Dict[str, float]  # 세부 점수 분석
    direction: str  # 'forward' or 'backward' 또는 'bidirectional'

@dataclass 
class BridgeConnection:
    """브릿지 메모리 연결 정보"""
    start_memory_id: int
    bridge_memory_id: int  
    end_memory_id: int
    bridge_score: float
    chain_type: str  # 'problem_solving', 'learning', 'decision_making' 등
    
@dataclass
class CausalChain:
    """완전한 인과관계 체인"""
    memories: List[Dict[str, Any]]
    causality_scores: List[float]
    chain_confidence: float
    story_summary: str

class VectorBasedCausalityFilter:
    """128차원 벡터를 활용한 인과관계 후보 축소"""
    
    def __init__(self, similarity_threshold_min=0.1, similarity_threshold_max=0.95):
        self.similarity_threshold_min = similarity_threshold_min
        self.similarity_threshold_max = similarity_threshold_max
        
    def find_causality_candidates(self, new_memory: Dict[str, Any], 
                                 existing_memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """벡터 유사도로 인과관계 후보 축소 (1000개 → 30개)"""
        
        if 'embedding' not in new_memory or not new_memory['embedding']:
            logger.warning("새 메모리에 임베딩 벡터가 없음")
            return existing_memories[:50]  # 임베딩 없으면 최근 50개만
            
        new_vector = np.array(new_memory['embedding'])
        candidates = []
        
        for memory in existing_memories:
            if 'embedding' not in memory or not memory['embedding']:
                continue
                
            existing_vector = np.array(memory['embedding'])
            
            # 코사인 유사도 계산
            similarity = self._cosine_similarity(new_vector, existing_vector)
            
            # Sweet Spot: 너무 높으면 중복, 너무 낮으면 무관함
            if self.similarity_threshold_min <= similarity <= self.similarity_threshold_max:
                candidates.append((memory, similarity))
                
        # 유사도 순 정렬 후 상위 30개 반환
        candidates.sort(key=lambda x: x[1], reverse=True)
        result = [mem for mem, sim in candidates[:30]]
        
        logger.debug(f"벡터 필터링: {len(existing_memories)}개 → {len(result)}개")
        return result
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """코사인 유사도 계산"""
        if vec1.size == 0 or vec2.size == 0:
            return 0.0
            
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return float(np.dot(vec1, vec2) / (norm1 * norm2))


class BasicCausalityDetector:
    """기본 인과관계 패턴 매칭 시스템"""
    
    def __init__(self):
        # 한국어/영어 인과관계 키워드 패턴
        self.causal_patterns = {
            'strong_cause': [
                # 한국어 강한 인과관계 패턴
                r'(.+)(때문에|덕분에|으로 인해|의 결과로)(.+)',
                r'(.+)(해서|니까|라서|여서)(.+)', 
                # 영어 강한 인과관계 패턴
                r'(.+)(because|due to|as a result|consequently)(.+)',
                r'(.+)(so|therefore|thus|hence)(.+)'
            ],
            'medium_cause': [
                # 중간 강도 패턴
                r'(.+)(그래서|그러니까|따라서|이에)(.+)',
                r'(.+)(then|next|after that|subsequently)(.+)',
                r'(.+)(해결|개선|수정|fix|solve|resolve)(.+)'
            ],
            'weak_cause': [
                # 약한 인과관계 패턴
                r'(.+)(이후|다음|후에|later|after)(.+)',
                r'(.+)(관련|연관|관해서|about|regarding)(.+)'
            ],
            'problem_solution': [
                r'(.+)(문제|이슈|버그|오류).*(해결|수정|개선)',
                r'(.+)(problem|issue|error).*(fix|solve|resolve)',
            ]
        }
        
        # 패턴별 가중치
        self.pattern_weights = {
            'strong_cause': 1.0,
            'medium_cause': 0.7, 
            'weak_cause': 0.4,
            'problem_solution': 0.9
        }
        
    def detect_causality(self, memory_a: Dict[str, Any], 
                        memory_b: Dict[str, Any]) -> CausalityScore:
        """두 메모리 간 인과관계 감지 및 점수 계산"""
        
        # 1. 시간적 관계 점수
        temporal_score = self._calculate_temporal_score(memory_a, memory_b)
        
        # 2. 언어적 패턴 점수
        linguistic_score = self._calculate_linguistic_score(memory_a, memory_b)
        
        # 3. 벡터 유사도 점수 (의미적 관련성)
        semantic_score = self._calculate_semantic_score(memory_a, memory_b)
        
        # 4. 종합 점수 계산 (가중 평균)
        final_score = (
            temporal_score * 0.25 +
            linguistic_score * 0.35 +  # 언어적 신호가 가장 중요
            semantic_score * 0.40
        )
        
        # 5. 방향성 결정
        direction = self._determine_direction(memory_a, memory_b, temporal_score, linguistic_score)
        
        # 6. 신뢰도 계산
        confidence = self._calculate_confidence(temporal_score, linguistic_score, semantic_score)
        
        return CausalityScore(
            strength=final_score,
            confidence=confidence,
            breakdown={
                'temporal': temporal_score,
                'linguistic': linguistic_score,
                'semantic': semantic_score
            },
            direction=direction
        )
    
    def _calculate_temporal_score(self, memory_a: Dict[str, Any], 
                                 memory_b: Dict[str, Any]) -> float:
        """시간적 관계 점수 계산"""
        try:
            time_a = datetime.fromisoformat(memory_a['timestamp'])
            time_b = datetime.fromisoformat(memory_b['timestamp'])
            
            time_diff = abs((time_b - time_a).total_seconds())
            
            # 시간 차이에 따른 점수 (가까울수록 높은 점수)
            if time_diff < 3600:  # 1시간 이내
                return 1.0
            elif time_diff < 86400:  # 1일 이내  
                return 0.8
            elif time_diff < 604800:  # 1주 이내
                return 0.6
            elif time_diff < 2592000:  # 1개월 이내
                return 0.4
            else:
                return 0.2
                
        except (ValueError, KeyError):
            return 0.3  # 시간 정보 없으면 중간 점수
    
    def _calculate_linguistic_score(self, memory_a: Dict[str, Any], 
                                   memory_b: Dict[str, Any]) -> float:
        """언어적 패턴 점수 계산"""
        
        text_combined = f"{memory_a.get('context', '')} {memory_b.get('context', '')}"
        max_score = 0.0
        
        for pattern_type, patterns in self.causal_patterns.items():
            weight = self.pattern_weights[pattern_type]
            
            for pattern in patterns:
                if re.search(pattern, text_combined, re.IGNORECASE):
                    score = weight
                    max_score = max(max_score, score)
                    break  # 패턴 타입별로 하나만 매칭
                    
        return max_score
    
    def _calculate_semantic_score(self, memory_a: Dict[str, Any], 
                                 memory_b: Dict[str, Any]) -> float:
        """의미적 유사도 점수 계산"""
        
        if 'embedding' not in memory_a or 'embedding' not in memory_b:
            return 0.5  # 임베딩 없으면 중간 점수
            
        try:
            vec_a = np.array(memory_a['embedding'])
            vec_b = np.array(memory_b['embedding'])
            
            # 코사인 유사도 계산
            similarity = VectorBasedCausalityFilter()._cosine_similarity(vec_a, vec_b)
            
            # 0~1 범위로 정규화 (코사인 유사도는 -1~1)
            return (similarity + 1) / 2
            
        except (ValueError, TypeError):
            return 0.5
    
    def _determine_direction(self, memory_a: Dict[str, Any], memory_b: Dict[str, Any], 
                           temporal_score: float, linguistic_score: float) -> str:
        """인과관계 방향성 결정"""
        
        try:
            time_a = datetime.fromisoformat(memory_a['timestamp'])
            time_b = datetime.fromisoformat(memory_b['timestamp'])
            
            # 시간 순서 기반 방향성
            if time_a < time_b:
                return 'forward'  # A → B
            elif time_a > time_b:
                return 'backward'  # B → A  
            else:
                return 'bidirectional'  # 동시간대
                
        except (ValueError, KeyError):
            return 'unknown'
    
    def _calculate_confidence(self, temporal: float, linguistic: float, semantic: float) -> float:
        """종합 신뢰도 계산"""
        
        # 세 점수가 모두 높을 때 높은 신뢰도
        min_score = min(temporal, linguistic, semantic)
        avg_score = (temporal + linguistic + semantic) / 3
        
        # 최소값과 평균값의 조화평균 (모든 지표가 균형있게 높아야 함)
        if min_score + avg_score == 0:
            return 0.0
            
        confidence = 2 * min_score * avg_score / (min_score + avg_score)
        return min(confidence, 1.0)


class BridgeMemoryDetector:
    """브릿지 메모리 감지 시스템 - 핵심 혁신 기능"""
    
    def __init__(self):
        self.causality_detector = BasicCausalityDetector()
        self.vector_filter = VectorBasedCausalityFilter()
        
    def detect_bridge_opportunities(self, new_memory: Dict[str, Any], 
                                   existing_memories: List[Dict[str, Any]]) -> List[BridgeConnection]:
        """새 메모리가 기존 메모리들을 연결하는 브릿지 역할 감지"""
        
        bridge_connections = []
        
        # 1단계: 벡터 기반으로 관련성 높은 메모리들 선별
        relevant_memories = self.vector_filter.find_causality_candidates(new_memory, existing_memories)
        
        if len(relevant_memories) < 2:
            return []  # 브릿지 역할 불가능
            
        # 2단계: 관련 메모리들 중에서 브릿지 기회 탐색
        for i, mem_a in enumerate(relevant_memories):
            for j, mem_c in enumerate(relevant_memories[i+1:], i+1):
                
                # A와 C 사이에 직접적 연결이 없는 경우만 (향후 구현)
                # if self._has_direct_connection(mem_a, mem_c):
                #     continue
                
                # 새 메모리가 A → new_memory → C 체인을 만들 수 있는지 검사
                bridge_score = self._calculate_bridge_score(mem_a, new_memory, mem_c)
                
                if bridge_score.strength > 0.4:  # 브릿지 임계값 낮춤 (dev1 테스트용)
                    bridge_connections.append(
                        BridgeConnection(
                            start_memory_id=mem_a.get('block_index', 0),
                            bridge_memory_id=new_memory.get('block_index', 0),
                            end_memory_id=mem_c.get('block_index', 0), 
                            bridge_score=bridge_score.strength,
                            chain_type=self._identify_chain_type(mem_a, new_memory, mem_c)
                        )
                    )
                    
        logger.info(f"브릿지 연결 발견: {len(bridge_connections)}개")
        return bridge_connections
    
    def _calculate_bridge_score(self, mem_a: Dict[str, Any], bridge: Dict[str, Any], 
                               mem_c: Dict[str, Any]) -> CausalityScore:
        """A → Bridge → C 체인의 타당성 점수"""
        
        # A → Bridge 인과관계 점수
        causality_ab = self.causality_detector.detect_causality(mem_a, bridge)
        
        # Bridge → C 인과관계 점수  
        causality_bc = self.causality_detector.detect_causality(bridge, mem_c)
        
        # 시간적 순서 검증 (A < Bridge < C)
        temporal_order_score = self._validate_temporal_order(mem_a, bridge, mem_c)
        
        # 브릿지 점수 = 두 연결의 조화평균 * 시간 순서 가중치
        if causality_ab.strength + causality_bc.strength == 0:
            bridge_strength = 0.0
        else:
            bridge_strength = (2 * causality_ab.strength * causality_bc.strength) / \
                            (causality_ab.strength + causality_bc.strength)
            bridge_strength *= temporal_order_score  # 시간 순서 가중치 적용
            
        # 종합 신뢰도
        bridge_confidence = min(causality_ab.confidence, causality_bc.confidence) * temporal_order_score
        
        return CausalityScore(
            strength=bridge_strength,
            confidence=bridge_confidence,
            breakdown={
                'causality_ab': causality_ab.strength,
                'causality_bc': causality_bc.strength,
                'temporal_order': temporal_order_score
            },
            direction='bridge'
        )
    
    def _validate_temporal_order(self, mem_a: Dict[str, Any], bridge: Dict[str, Any], 
                                mem_c: Dict[str, Any]) -> float:
        """시간적 순서 검증 (A ≤ Bridge ≤ C)"""
        
        try:
            time_a = datetime.fromisoformat(mem_a['timestamp'])
            time_bridge = datetime.fromisoformat(bridge['timestamp'])
            time_c = datetime.fromisoformat(mem_c['timestamp'])
            
            # 완벽한 순서: A ≤ Bridge ≤ C
            if time_a <= time_bridge <= time_c:
                return 1.0
            
            # 부분적 순서 (일부만 맞음)
            if time_a <= time_bridge or time_bridge <= time_c:
                return 0.7
                
            # 순서가 맞지 않지만 시간 차이가 작음 (동시간대)
            max_diff = max(
                abs((time_bridge - time_a).total_seconds()),
                abs((time_c - time_bridge).total_seconds())
            )
            
            if max_diff < 86400:  # 1일 이내
                return 0.5
            else:
                return 0.2
                
        except (ValueError, KeyError):
            return 0.3  # 시간 정보 없으면 중간 점수
    
    def _identify_chain_type(self, mem_a: Dict[str, Any], bridge: Dict[str, Any], 
                           mem_c: Dict[str, Any]) -> str:
        """인과관계 체인 타입 식별"""
        
        contexts = [
            mem_a.get('context', '').lower(),
            bridge.get('context', '').lower(), 
            mem_c.get('context', '').lower()
        ]
        
        combined_text = ' '.join(contexts)
        
        # 문제해결 패턴
        if any(word in combined_text for word in ['문제', '이슈', '버그', '해결', 'problem', 'issue', 'fix', 'solve']):
            return 'problem_solving'
        
        # 학습 패턴    
        if any(word in combined_text for word in ['공부', '학습', '배웠', 'learn', 'study', 'understand']):
            return 'learning'
        
        # 의사결정 패턴
        if any(word in combined_text for word in ['결정', '선택', '결론', 'decide', 'choose', 'decision']):
            return 'decision_making'
        
        # 개발 패턴
        if any(word in combined_text for word in ['개발', '구현', '코딩', 'develop', 'implement', 'code']):
            return 'development'
            
        return 'general'


class CausalitySystem:
    """통합 인과관계 시스템 - 메인 엔트리 포인트"""
    
    def __init__(self):
        self.vector_filter = VectorBasedCausalityFilter()
        self.causality_detector = BasicCausalityDetector()
        self.bridge_detector = BridgeMemoryDetector()
        
    def process_new_memory(self, new_memory: Dict[str, Any], 
                          existing_memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """새 메모리 추가 시 인과관계 분석 및 연결"""
        
        logger.info(f"새 메모리 인과관계 분석 시작: {new_memory.get('block_index', 'N/A')}")
        
        # 1단계: 벡터 기반 후보 축소 (성능 최적화)
        candidates = self.vector_filter.find_causality_candidates(new_memory, existing_memories)
        
        # 2단계: 직접적 인과관계 감지
        direct_causality = []
        for candidate in candidates:
            causality_score = self.causality_detector.detect_causality(new_memory, candidate)
            
            if causality_score.strength > 0.3:  # 임계값 낮춤 (dev1 테스트용)
                direct_causality.append({
                    'memory_id': candidate.get('block_index', 0),
                    'causality_score': causality_score.strength,
                    'confidence': causality_score.confidence,
                    'direction': causality_score.direction
                })
        
        # 3단계: 브릿지 메모리 기회 감지 (핵심 혁신!)  
        bridge_connections = self.bridge_detector.detect_bridge_opportunities(new_memory, candidates)
        
        # 4단계: 결과 정리
        result = {
            'new_memory_id': new_memory.get('block_index', 0),
            'analyzed_candidates': len(candidates),
            'direct_causality_links': len(direct_causality),
            'bridge_connections': len(bridge_connections),
            'causality_details': direct_causality,
            'bridge_details': [
                {
                    'start_id': bc.start_memory_id,
                    'bridge_id': bc.bridge_memory_id, 
                    'end_id': bc.end_memory_id,
                    'score': bc.bridge_score,
                    'type': bc.chain_type
                } for bc in bridge_connections
            ]
        }
        
        logger.info(f"인과관계 분석 완료: 직접연결 {len(direct_causality)}개, 브릿지연결 {len(bridge_connections)}개")
        return result


# 편의 함수들
def detect_causality_for_memory(new_memory: Dict[str, Any], 
                               existing_memories: List[Dict[str, Any]]) -> Dict[str, Any]:
    """새 메모리의 인과관계 분석 (메인 API)"""
    
    system = CausalitySystem()
    return system.process_new_memory(new_memory, existing_memories)


def get_causality_chains(memory_ids: List[int], memories: List[Dict[str, Any]]) -> List[CausalChain]:
    """메모리 ID 목록으로부터 인과관계 체인 구성"""
    
    # TODO: 추후 구현 예정 (체인 재구성 및 스토리 생성)
    pass