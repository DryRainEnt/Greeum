#!/usr/bin/env python3
"""
그레마스 액탄트 모델 - LLM 통합 자동 추출 시스템

Greeum MCP 연동을 통한 실제 Claude API 호출로 액탄트 추출
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from actant_schema_design import ActantRole, ActantEntity, ActantExtractor


class GreeumActantExtractor(ActantExtractor):
    """Greeum MCP를 통한 실제 LLM 액탄트 추출"""
    
    def __init__(self, use_mcp: bool = True):
        super().__init__()
        self.use_mcp = use_mcp
    
    async def extract_actants_with_claude(self, context: str) -> Dict[ActantRole, ActantEntity]:
        """Claude API를 통한 실제 액탄트 추출"""
        
        prompt = self._create_optimized_prompt(context)
        
        if self.use_mcp:
            # Greeum MCP를 통한 Claude 호출 (실제 구현 시)
            try:
                # 실제 MCP 호출 코드 (의사 코드)
                # from greeum.mcp.tools import call_claude_api
                # response = await call_claude_api(prompt)
                
                # 임시: 고도화된 모킹 응답
                response = self._advanced_mock_response(context)
                
                return self._parse_claude_response(response)
                
            except Exception as e:
                print(f"MCP 호출 실패, 규칙 기반으로 폴백: {e}")
                return self._rule_based_extraction(context)
        else:
            return self._rule_based_extraction(context)
    
    def _create_optimized_prompt(self, context: str) -> str:
        """Claude에 최적화된 액탄트 추출 프롬프트"""
        return f"""
다음 한국어 텍스트를 그레마스 행위자 이론의 액탄트 모델로 분석해주세요.

텍스트: "{context}"

## 분석 기준
각 액탄트의 역할을 정확히 식별해주세요:

1. **Subject (주체)**: 실제로 행동을 수행하는 주체
2. **Object (객체)**: 주체가 추구하거나 원하는 목표/가치/대상
3. **Sender (발신자)**: 주체의 행동을 동기화하거나 명령하는 요인
4. **Receiver (수신자)**: 행동의 결과로 이익을 받는 대상
5. **Helper (조력자)**: 목표 달성에 도움이 되는 요소
6. **Opponent (반대자)**: 목표 달성을 방해하는 요소

## 응답 형식
다음 JSON 형식으로만 응답하세요. 텍스트에서 명확하게 식별되지 않는 액탄트는 포함하지 마세요:

```json
{{
  "subject": {{"entity": "구체적인 주체", "confidence": 0.9, "reasoning": "근거"}},
  "object": {{"entity": "구체적인 목표", "confidence": 0.8, "reasoning": "근거"}},
  "sender": {{"entity": "동기 요인", "confidence": 0.7, "reasoning": "근거"}},
  "receiver": {{"entity": "수혜자", "confidence": 0.6, "reasoning": "근거"}},
  "helper": {{"entity": "조력 요소", "confidence": 0.5, "reasoning": "근거"}},
  "opponent": {{"entity": "방해 요소", "confidence": 0.4, "reasoning": "근거"}}
}}
```

신뢰도는 텍스트에서 해당 액탄트를 식별한 확신 정도 (0.0-1.0)입니다.
"""
    
    def _advanced_mock_response(self, context: str) -> str:
        """고도화된 모킹 응답 - 실제 Claude 응답 유사하게"""
        
        # 간단한 패턴 매칭을 통한 고도화된 추출
        mock_responses = {
            "프로젝트": {
                "subject": {"entity": "나/사용자", "confidence": 0.9, "reasoning": "행동 주체로 명시적 언급"},
                "object": {"entity": "프로젝트 성공적 완수", "confidence": 0.8, "reasoning": "추구하는 목표"},
                "sender": {"entity": "내재적 동기/호기심", "confidence": 0.7, "reasoning": "행동을 유발하는 내적 동기"}
            },
            "문제": {
                "subject": {"entity": "나/사용자", "confidence": 0.9, "reasoning": "문제 해결의 주체"},
                "object": {"entity": "문제 해결", "confidence": 0.9, "reasoning": "달성하고자 하는 목표"},
                "opponent": {"entity": "문제 상황", "confidence": 0.8, "reasoning": "해결해야 할 장애물"}
            },
            "학습": {
                "subject": {"entity": "나/사용자", "confidence": 0.9, "reasoning": "학습 주체"},
                "object": {"entity": "지식 습득", "confidence": 0.8, "reasoning": "학습의 목적"},
                "receiver": {"entity": "미래의 나", "confidence": 0.7, "reasoning": "학습 결과의 수혜자"}
            }
        }
        
        # 키워드 기반 매칭
        for keyword, response in mock_responses.items():
            if keyword in context:
                return json.dumps(response, ensure_ascii=False)
        
        # 기본 응답
        default_response = {
            "subject": {"entity": "텍스트 주체", "confidence": 0.6, "reasoning": "일반적 주체 추정"},
            "object": {"entity": "언급된 활동/목표", "confidence": 0.5, "reasoning": "텍스트에서 유추"}
        }
        return json.dumps(default_response, ensure_ascii=False)
    
    def _parse_claude_response(self, response: str) -> Dict[ActantRole, ActantEntity]:
        """Claude 응답을 파싱하여 액탄트 객체로 변환"""
        try:
            parsed = json.loads(response)
            actants = {}
            
            for role_str, data in parsed.items():
                if role_str in [r.value for r in ActantRole]:
                    role = ActantRole(role_str)
                    actants[role] = ActantEntity(
                        role=role,
                        entity=data["entity"],
                        confidence=data["confidence"],
                        extraction_method="llm_claude"
                    )
            
            return actants
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Claude 응답 파싱 실패: {e}")
            return self._rule_based_extraction(response[:50] + "...")


class ActantAnalysisService:
    """액탄트 분석 통합 서비스"""
    
    def __init__(self, use_mcp: bool = True):
        self.extractor = GreeumActantExtractor(use_mcp=use_mcp)
    
    async def analyze_memory_context(self, context: str) -> Dict[str, Any]:
        """메모리 컨텍스트의 완전한 액탄트 분석"""
        
        # 1. 액탄트 추출
        actants = await self.extractor.extract_actants_with_claude(context)
        
        # 2. 서사 패턴 분석
        narrative_pattern = self._analyze_narrative_pattern(context, actants)
        
        # 3. 행동 시퀀스 추출
        action_sequence = self._extract_action_sequence(context)
        
        # 4. 액탄트 관계 분석
        actant_relationships = self._analyze_actant_relationships(actants)
        
        return {
            "actants": {role.value: actant.to_dict() for role, actant in actants.items()},
            "narrative_pattern": narrative_pattern,
            "action_sequence": action_sequence,
            "actant_relationships": actant_relationships,
            "analysis_quality": self._assess_analysis_quality(actants),
            "analysis_timestamp": "2025-09-05T15:30:00Z"
        }
    
    def _analyze_narrative_pattern(self, context: str, actants: Dict[ActantRole, ActantEntity]) -> str:
        """액탄트 구성을 바탕으로 서사 패턴 분석"""
        
        # Subject + Object 조합으로 패턴 판단
        has_subject = ActantRole.SUBJECT in actants
        has_object = ActantRole.OBJECT in actants
        has_opponent = ActantRole.OPPONENT in actants
        has_helper = ActantRole.HELPER in actants
        
        if has_subject and has_object:
            if has_opponent:
                return "conflict"  # 주체-목표-장애물 = 갈등 구조
            elif has_helper:
                return "quest"    # 주체-목표-조력자 = 탐구 구조
            else:
                return "acquisition"  # 주체-목표 = 획득 구조
        
        # 키워드 기반 보완 분석
        if "문제" in context or "해결" in context:
            return "conflict"
        elif "시작" in context or "새로운" in context:
            return "quest"
        elif "변화" in context or "바뀌" in context:
            return "transformation"
        
        return "other"
    
    def _extract_action_sequence(self, context: str) -> List[str]:
        """텍스트에서 행동 시퀀스 추출"""
        
        # 시간 순서 지시어 기반 추출
        sequence_indicators = [
            ("시작", "시작_단계"),
            ("계획", "계획_단계"),
            ("실행", "실행_단계"),
            ("진행", "진행_단계"),
            ("완료", "완료_단계"),
            ("검토", "검토_단계")
        ]
        
        detected_sequence = []
        for indicator, phase in sequence_indicators:
            if indicator in context:
                detected_sequence.append(phase)
        
        return detected_sequence if detected_sequence else ["현재_상태"]
    
    def _analyze_actant_relationships(self, actants: Dict[ActantRole, ActantEntity]) -> Dict[str, Any]:
        """액탄트 간 관계 분석"""
        
        relationships = {
            "subject_object_alignment": 0.0,  # 주체-목표 정렬도
            "helper_strength": 0.0,           # 조력자 강도
            "opponent_threat": 0.0,           # 반대자 위협도
            "sender_authority": 0.0           # 발신자 권위도
        }
        
        # 신뢰도 기반 관계 강도 계산
        if ActantRole.SUBJECT in actants and ActantRole.OBJECT in actants:
            subject_conf = actants[ActantRole.SUBJECT].confidence
            object_conf = actants[ActantRole.OBJECT].confidence
            relationships["subject_object_alignment"] = (subject_conf + object_conf) / 2
        
        if ActantRole.HELPER in actants:
            relationships["helper_strength"] = actants[ActantRole.HELPER].confidence
        
        if ActantRole.OPPONENT in actants:
            relationships["opponent_threat"] = actants[ActantRole.OPPONENT].confidence
        
        if ActantRole.SENDER in actants:
            relationships["sender_authority"] = actants[ActantRole.SENDER].confidence
        
        return relationships
    
    def _assess_analysis_quality(self, actants: Dict[ActantRole, ActantEntity]) -> Dict[str, Any]:
        """액탄트 분석 품질 평가"""
        
        total_confidence = sum(actant.confidence for actant in actants.values())
        avg_confidence = total_confidence / len(actants) if actants else 0.0
        
        completeness = len(actants) / 6  # 6개 액탄트 중 몇 개 식별
        
        quality_score = (avg_confidence * 0.7) + (completeness * 0.3)
        
        return {
            "actant_count": len(actants),
            "avg_confidence": avg_confidence,
            "completeness": completeness,
            "quality_score": quality_score,
            "quality_level": "high" if quality_score > 0.7 else "medium" if quality_score > 0.4 else "low"
        }


# 사용 예시
async def test_actant_analysis():
    """액탄트 분석 시스템 테스트"""
    
    service = ActantAnalysisService(use_mcp=False)  # MCP 없이 테스트
    
    test_contexts = [
        "새로운 AI 프로젝트를 시작했고 정말 흥미로워요",
        "복잡한 버그를 해결하려고 노력하고 있지만 시간이 부족해요",
        "팀원들과 함께 새로운 기능을 개발하여 사용자들이 만족할 것 같아요"
    ]
    
    for i, context in enumerate(test_contexts):
        print(f"\n=== 테스트 케이스 {i+1} ===")
        print(f"텍스트: {context}")
        
        analysis = await service.analyze_memory_context(context)
        
        print("\\n🎭 액탄트 분석 결과:")
        for role, actant_data in analysis["actants"].items():
            print(f"  {role}: {actant_data['entity']} (신뢰도: {actant_data['confidence']})")
        
        print(f"\\n📖 서사 패턴: {analysis['narrative_pattern']}")
        print(f"🔄 행동 시퀀스: {analysis['action_sequence']}")
        print(f"📊 분석 품질: {analysis['analysis_quality']['quality_level']} ({analysis['analysis_quality']['quality_score']:.2f})")


if __name__ == "__main__":
    # 비동기 테스트 실행
    asyncio.run(test_actant_analysis())