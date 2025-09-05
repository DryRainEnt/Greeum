#!/usr/bin/env python3
"""
그레마스 액탄트 모델 기반 메모리 블록 스키마 설계안

이 설계안은 기존 Greeum 메모리 블록 구조에 그레마스의 6개 액탄트 모델을 통합합니다.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json


class ActantRole(Enum):
    """그레마스 액탄트 역할 정의"""
    SUBJECT = "subject"      # 주체: 행위의 수행자
    OBJECT = "object"        # 객체: 추구하는 목표/가치
    SENDER = "sender"        # 발신자: 행위를 동기화하는 요인
    RECEIVER = "receiver"    # 수신자: 행위의 수혜자
    HELPER = "helper"        # 조력자: 목표 달성을 돕는 요소
    OPPONENT = "opponent"    # 반대자: 목표 달성을 방해하는 요소


@dataclass
class ActantEntity:
    """액탄트 개체 정의"""
    role: ActantRole
    entity: str              # 액탄트의 구체적 내용
    confidence: float        # 추출 신뢰도 (0.0-1.0)
    extraction_method: str   # 추출 방법 ('llm', 'rule', 'hybrid')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role.value,
            "entity": self.entity,
            "confidence": self.confidence,
            "extraction_method": self.extraction_method
        }


class ActantMemorySchema:
    """그레마스 액탄트 모델 확장 메모리 스키마"""
    
    @staticmethod
    def create_actant_enhanced_block(
        # 기존 필수 필드들
        context: str,
        keywords: List[str],
        tags: List[str], 
        embedding: List[float],
        importance: float,
        # 새로운 액탄트 필드들
        actants: Optional[Dict[str, ActantEntity]] = None,
        narrative_pattern: Optional[str] = None,
        action_sequence: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """액탄트 모델이 통합된 메모리 블록 생성"""
        
        # 기존 메모리 블록 구조 유지
        base_block = {
            "context": context,
            "keywords": keywords,
            "tags": tags,
            "embedding": embedding,
            "importance": importance
        }
        
        # 액탄트 정보를 metadata에 통합
        actant_metadata = {
            "actant_analysis": {
                "actants": {role.value: actant.to_dict() 
                          for role, actant in (actants or {}).items()},
                "narrative_pattern": narrative_pattern,
                "action_sequence": action_sequence or [],
                "analysis_timestamp": None,  # 분석 시점 기록
                "analysis_version": "1.0"    # 분석 모델 버전
            }
        }
        
        base_block["metadata"] = actant_metadata
        return base_block


class ActantAnalysisPrompts:
    """액탄트 분석을 위한 LLM 프롬프트 템플릿"""
    
    EXTRACT_ACTANTS_PROMPT = """
다음 텍스트를 그레마스 행위자 이론의 6개 액탄트 모델로 분석해주세요:

텍스트: "{context}"

각 액탄트를 JSON 형식으로 추출해주세요:
- subject (주체): 행위의 수행자
- object (객체): 추구하는 목표나 가치
- sender (발신자): 행위를 동기화하는 요인
- receiver (수신자): 행위의 수혜자
- helper (조력자): 목표 달성을 돕는 요소
- opponent (반대자): 목표 달성을 방해하는 요소

응답 형식:
{{
  "subject": {{"entity": "...", "confidence": 0.8}},
  "object": {{"entity": "...", "confidence": 0.9}},
  ...
}}

텍스트에서 명확하게 식별되지 않는 액탄트는 제외하고, 
신뢰도는 0.0-1.0 사이의 값으로 평가해주세요.
"""

    NARRATIVE_PATTERN_PROMPT = """
다음 텍스트의 서사 패턴을 분석해주세요:

텍스트: "{context}"

가능한 패턴들:
- quest (탐구): 목표 달성을 위한 여정
- conflict (갈등): 대립하는 힘들의 충돌
- transformation (변화): 상태나 관점의 변화
- acquisition (획득): 무엇인가를 얻는 과정
- loss (상실): 무엇인가를 잃는 과정
- exchange (교환): 상호 작용이나 거래
- maintenance (유지): 현재 상태 보존
- other (기타): 위 패턴에 해당하지 않음

응답: 가장 적합한 패턴 하나를 선택해주세요.
"""


class ActantExtractor:
    """LLM을 사용한 액탄트 자동 추출 시스템"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.prompts = ActantAnalysisPrompts()
    
    async def extract_actants(self, context: str) -> Dict[ActantRole, ActantEntity]:
        """LLM을 사용하여 텍스트에서 액탄트 추출"""
        if not self.llm_client:
            return self._rule_based_extraction(context)
        
        # LLM 기반 추출 (실제 구현 시 Claude API 사용)
        prompt = self.prompts.EXTRACT_ACTANTS_PROMPT.format(context=context)
        
        try:
            # 실제 LLM 호출 코드 (의사 코드)
            # response = await self.llm_client.complete(prompt)
            # actant_data = json.loads(response)
            
            # 임시 구현 - 실제로는 LLM 응답 파싱
            actant_data = self._mock_llm_response(context)
            
            actants = {}
            for role_str, data in actant_data.items():
                if role_str in [r.value for r in ActantRole]:
                    role = ActantRole(role_str)
                    actants[role] = ActantEntity(
                        role=role,
                        entity=data["entity"],
                        confidence=data["confidence"],
                        extraction_method="llm"
                    )
            
            return actants
            
        except Exception as e:
            # LLM 실패 시 규칙 기반으로 폴백
            return self._rule_based_extraction(context)
    
    def _rule_based_extraction(self, context: str) -> Dict[ActantRole, ActantEntity]:
        """규칙 기반 액탄트 추출 (폴백 방법)"""
        actants = {}
        
        # 간단한 규칙 기반 추출 예시
        if "나" in context or "내가" in context:
            actants[ActantRole.SUBJECT] = ActantEntity(
                role=ActantRole.SUBJECT,
                entity="나/사용자",
                confidence=0.7,
                extraction_method="rule"
            )
        
        if "프로젝트" in context:
            actants[ActantRole.OBJECT] = ActantEntity(
                role=ActantRole.OBJECT,
                entity="프로젝트",
                confidence=0.6,
                extraction_method="rule"
            )
        
        return actants
    
    def _mock_llm_response(self, context: str) -> Dict[str, Dict[str, Any]]:
        """LLM 응답 모킹 (테스트용)"""
        return {
            "subject": {"entity": "나", "confidence": 0.8},
            "object": {"entity": "프로젝트 완성", "confidence": 0.7},
            "sender": {"entity": "호기심", "confidence": 0.6}
        }


# 사용 예시
def example_usage():
    """액탄트 모델 사용 예시"""
    
    # 1. 액탄트 추출
    extractor = ActantExtractor()
    context = "새로운 AI 프로젝트를 시작했고 정말 흥미로워요"
    
    # actants = await extractor.extract_actants(context)  # 실제 비동기 호출
    actants = extractor._rule_based_extraction(context)  # 동기 버전
    
    # 2. 액탄트 모델 통합 블록 생성
    enhanced_block = ActantMemorySchema.create_actant_enhanced_block(
        context=context,
        keywords=["AI", "프로젝트", "시작", "흥미"],
        tags=["긍정적", "시작", "동기부여"],
        embedding=[0.1, 0.2, 0.3],  # 실제 임베딩
        importance=0.8,
        actants=actants,
        narrative_pattern="quest",
        action_sequence=["프로젝트_계획", "개발_시작", "진행_중"]
    )
    
    return enhanced_block


if __name__ == "__main__":
    # 예시 실행
    example_block = example_usage()
    print("=== 그레마스 액탄트 모델 확장 메모리 블록 ===")
    print(json.dumps(example_block, ensure_ascii=False, indent=2))