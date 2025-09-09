"""
AI-Powered Actant Parser for Legacy Memory Migration
Converts legacy memory blocks to actant-structured format
"""

import json
import re
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ParseConfidence(Enum):
    """Confidence levels for AI parsing results"""
    HIGH = 0.9
    MEDIUM = 0.7
    LOW = 0.5
    FAILED = 0.0


@dataclass
class ActantParseResult:
    """Result of AI actant parsing"""
    subject: Optional[str]
    action: Optional[str] 
    object_target: Optional[str]
    confidence: float
    original_context: str
    success: bool
    error: Optional[str] = None
    parsed_at: Optional[str] = None
    reasoning: Optional[str] = None


class AIActantParser:
    """
    AI-powered parser for converting legacy memories to actant structure
    Uses multiple parsing strategies for maximum accuracy
    """
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        self.parsing_stats = {
            "total_parsed": 0,
            "successful_parses": 0,
            "failed_parses": 0,
            "high_confidence": 0,
            "medium_confidence": 0,
            "low_confidence": 0
        }
        
        # Common patterns for fallback parsing
        self.subject_patterns = [
            r'(?:사용자|user)(?:가|이)',
            r'(?:Claude|claude)(?:가|이)',
            r'(?:시스템|system)(?:이|가)',
            r'(?:팀|team)(?:이|가)',
            r'(?:개발자|developer)(?:가|이)'
        ]
        
        self.action_patterns = [
            r'(?:요청|request)(?:했|함|한)',
            r'(?:발견|found|discover)(?:했|함|한)',
            r'(?:구현|implement)(?:했|함|한)',
            r'(?:수정|fix|modify)(?:했|함|한)',
            r'(?:테스트|test)(?:했|함|한)',
            r'(?:분석|analyze)(?:했|함|한)'
        ]
    
    def parse_legacy_memory(self, context: str) -> ActantParseResult:
        """
        Parse legacy memory context into actant structure
        
        Args:
            context: Original memory context text
            
        Returns:
            ActantParseResult with parsed actant components
        """
        self.parsing_stats["total_parsed"] += 1
        
        # First try AI parsing if available
        if self.ai_client:
            try:
                ai_result = self._parse_with_ai(context)
                if ai_result.success:
                    self._update_stats(ai_result)
                    return ai_result
            except Exception as e:
                logger.warning(f"AI parsing failed, falling back to rule-based: {e}")
        
        # Fallback to rule-based parsing
        fallback_result = self._parse_with_rules(context)
        self._update_stats(fallback_result)
        return fallback_result
    
    def _parse_with_ai(self, context: str) -> ActantParseResult:
        """Parse using AI model with structured prompt"""
        
        prompt = f'''
다음 메모리 텍스트를 그레마스 액탄트 모델의 [주체-행동-대상] 구조로 분석해주세요:

원본: "{context}"

분석 결과를 다음 JSON 형식으로 제공해주세요:
{{
    "subject": "행동을 수행한 주체 (사용자/Claude/팀/시스템/개발자 등)",
    "action": "구체적인 행동 (요청/발견/결정/구현/완료/테스트/분석 등)", 
    "object": "행동의 대상 (기능/버그/아키텍처/데이터/시스템 등)",
    "confidence": 0.0-1.0,
    "reasoning": "분석 근거 설명"
}}

주의사항:
- 원본 의미를 정확히 보존해야 합니다
- 애매한 경우 confidence를 낮게 설정하세요
- subject는 반드시 명확한 행위자여야 합니다
- action은 구체적인 동사여야 합니다
- object는 action의 명확한 대상이어야 합니다

만약 액탄트 구조로 분석이 어려운 경우 confidence를 0.3 이하로 설정하고 이유를 reasoning에 설명하세요.
'''

        try:
            # AI API 호출 (실제 구현에서는 OpenAI/Claude API 사용)
            response = self._call_ai_api(prompt)
            parsed = json.loads(response)
            
            # Validate parsed result
            if not self._validate_ai_response(parsed):
                raise ValueError("Invalid AI response format")
            
            return ActantParseResult(
                subject=parsed.get('subject'),
                action=parsed.get('action'),
                object_target=parsed.get('object'),
                confidence=float(parsed.get('confidence', 0.0)),
                original_context=context,
                success=True,
                reasoning=parsed.get('reasoning'),
                parsed_at=time.time()
            )
            
        except Exception as e:
            return ActantParseResult(
                subject=None,
                action=None,
                object_target=None,
                confidence=0.0,
                original_context=context,
                success=False,
                error=str(e)
            )
    
    def _call_ai_api(self, prompt: str) -> str:
        """
        Call AI API (placeholder - implement with actual AI client)
        
        Args:
            prompt: Formatted prompt for AI
            
        Returns:
            str: AI response
        """
        if not self.ai_client:
            raise RuntimeError("No AI client configured")
        
        # This would be replaced with actual AI API calls
        # For now, return a mock response for testing
        return self._mock_ai_response(prompt)
    
    def _mock_ai_response(self, prompt: str) -> str:
        """Mock AI response for testing"""
        # Extract context from prompt
        context_match = re.search(r'"([^"]+)"', prompt)
        if not context_match:
            raise ValueError("Could not extract context from prompt")
        
        context = context_match.group(1)
        
        # Simple pattern-based mock parsing
        subject = "사용자"
        if "claude" in context.lower():
            subject = "Claude"
        elif "시스템" in context:
            subject = "시스템"
        elif "팀" in context:
            subject = "팀"
        
        action = "작업"
        for pattern, act in [
            (r'요청', '요청'),
            (r'발견', '발견'),
            (r'구현', '구현'),
            (r'수정', '수정'),
            (r'테스트', '테스트'),
            (r'분석', '분석')
        ]:
            if re.search(pattern, context):
                action = act
                break
        
        obj = "시스템"
        if "기능" in context:
            obj = "기능"
        elif "버그" in context:
            obj = "버그"
        elif "데이터" in context:
            obj = "데이터"
        
        confidence = 0.8 if len(context) > 20 else 0.6
        
        return json.dumps({
            "subject": subject,
            "action": action,
            "object": obj,
            "confidence": confidence,
            "reasoning": f"패턴 기반 분석: {subject}가 {action}를 {obj}에 대해 수행"
        }, ensure_ascii=False)
    
    def _validate_ai_response(self, parsed: Dict[str, Any]) -> bool:
        """Validate AI response structure"""
        required_fields = ['subject', 'action', 'object', 'confidence']
        
        if not all(field in parsed for field in required_fields):
            return False
        
        confidence = parsed.get('confidence', 0)
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            return False
        
        return True
    
    def _parse_with_rules(self, context: str) -> ActantParseResult:
        """
        Rule-based fallback parsing using patterns
        
        Args:
            context: Memory context to parse
            
        Returns:
            ActantParseResult with rule-based parsing
        """
        subject = self._extract_subject(context)
        action = self._extract_action(context)
        obj = self._extract_object(context)
        
        # Calculate confidence based on extraction success
        confidence = 0.0
        if subject and action and obj:
            confidence = 0.7
        elif subject and action:
            confidence = 0.5
        elif subject or action:
            confidence = 0.3
        
        success = confidence >= 0.3
        
        return ActantParseResult(
            subject=subject,
            action=action,
            object_target=obj,
            confidence=confidence,
            original_context=context,
            success=success,
            reasoning=f"Rule-based parsing: S={bool(subject)}, A={bool(action)}, O={bool(obj)}",
            parsed_at=time.time()
        )
    
    def _extract_subject(self, context: str) -> Optional[str]:
        """Extract subject using pattern matching"""
        for pattern in self.subject_patterns:
            if re.search(pattern, context):
                match = re.search(pattern, context)
                if match:
                    subject_part = match.group(0)
                    return subject_part.replace('가', '').replace('이', '').strip()
        
        # Default fallback
        if any(word in context.lower() for word in ['i ', 'me', '나는', '내가']):
            return "사용자"
        elif 'claude' in context.lower():
            return "Claude"
        
        return None
    
    def _extract_action(self, context: str) -> Optional[str]:
        """Extract action using pattern matching"""
        for pattern in self.action_patterns:
            if re.search(pattern, context):
                match = re.search(pattern, context)
                if match:
                    action_part = match.group(0)
                    # Clean up action
                    for suffix in ['했', '함', '한', '다', '음']:
                        action_part = action_part.replace(suffix, '')
                    return action_part.strip()
        
        # Look for common verbs
        verbs = ['추가', '삭제', '변경', '생성', '확인', '검사', '실행']
        for verb in verbs:
            if verb in context:
                return verb
        
        return None
    
    def _extract_object(self, context: str) -> Optional[str]:
        """Extract object using keyword detection"""
        objects = [
            '기능', '함수', '클래스', '메서드',
            '버그', '오류', '에러',
            '파일', '코드', '데이터', '변수',
            '시스템', '모듈', '컴포넌트',
            '테스트', '검증', '배포',
            '문서', '주석', '설명'
        ]
        
        for obj in objects:
            if obj in context:
                return obj
        
        return None
    
    def _update_stats(self, result: ActantParseResult) -> None:
        """Update parsing statistics"""
        if result.success:
            self.parsing_stats["successful_parses"] += 1
            
            if result.confidence >= 0.8:
                self.parsing_stats["high_confidence"] += 1
            elif result.confidence >= 0.6:
                self.parsing_stats["medium_confidence"] += 1
            else:
                self.parsing_stats["low_confidence"] += 1
        else:
            self.parsing_stats["failed_parses"] += 1
    
    def get_parsing_stats(self) -> Dict[str, Any]:
        """Get parsing statistics"""
        total = self.parsing_stats["total_parsed"]
        if total == 0:
            return self.parsing_stats.copy()
        
        stats = self.parsing_stats.copy()
        stats["success_rate"] = stats["successful_parses"] / total
        stats["high_confidence_rate"] = stats["high_confidence"] / total
        stats["medium_confidence_rate"] = stats["medium_confidence"] / total
        stats["low_confidence_rate"] = stats["low_confidence"] / total
        
        return stats
    
    def batch_parse(self, contexts: List[str], batch_size: int = 10) -> List[ActantParseResult]:
        """
        Parse multiple contexts in batches
        
        Args:
            contexts: List of contexts to parse
            batch_size: Number of contexts to process per batch
            
        Returns:
            List of ActantParseResult
        """
        results = []
        
        for i in range(0, len(contexts), batch_size):
            batch = contexts[i:i + batch_size]
            
            for context in batch:
                result = self.parse_legacy_memory(context)
                results.append(result)
                
                # Add small delay between API calls if using real AI
                if self.ai_client:
                    time.sleep(0.1)
            
            logger.info(f"Processed batch {i//batch_size + 1}/{(len(contexts)-1)//batch_size + 1}")
        
        return results


class RelationshipExtractor:
    """Extract relationships from actant-parsed memories"""
    
    def __init__(self):
        self.subject_collaborations = {}
        self.action_causalities = {}
        self.object_dependencies = {}
    
    def extract_relationships(self, parsed_memories: List[ActantParseResult]) -> Dict[str, List[Dict]]:
        """
        Extract relationships from parsed actant data
        
        Args:
            parsed_memories: List of successfully parsed memories
            
        Returns:
            Dict containing different types of relationships
        """
        # Filter successful parses with good confidence
        quality_memories = [
            mem for mem in parsed_memories 
            if mem.success and mem.confidence >= 0.5
        ]
        
        relationships = {
            "subject_collaborations": self._find_subject_collaborations(quality_memories),
            "action_causalities": self._find_action_causalities(quality_memories),
            "object_dependencies": self._find_object_dependencies(quality_memories)
        }
        
        return relationships
    
    def _find_subject_collaborations(self, memories: List[ActantParseResult]) -> List[Dict]:
        """Find collaborations between subjects"""
        collaborations = []
        subject_groups = {}
        
        # Group memories by subject
        for mem in memories:
            if mem.subject:
                if mem.subject not in subject_groups:
                    subject_groups[mem.subject] = []
                subject_groups[mem.subject].append(mem)
        
        # Find subjects that work on similar objects
        for subject1, mems1 in subject_groups.items():
            for subject2, mems2 in subject_groups.items():
                if subject1 >= subject2:  # Avoid duplicates
                    continue
                
                # Find common objects
                objs1 = {mem.object_target for mem in mems1 if mem.object_target}
                objs2 = {mem.object_target for mem in mems2 if mem.object_target}
                
                common_objects = objs1 & objs2
                if common_objects:
                    collaborations.append({
                        "subject1": subject1,
                        "subject2": subject2,
                        "relationship_type": "collaboration",
                        "common_objects": list(common_objects),
                        "confidence": 0.8
                    })
        
        return collaborations
    
    def _find_action_causalities(self, memories: List[ActantParseResult]) -> List[Dict]:
        """Find causal relationships between actions"""
        causalities = []
        
        # Define causal action pairs
        causal_patterns = [
            ("요청", "구현"),
            ("발견", "수정"),
            ("테스트", "배포"),
            ("분석", "결정"),
            ("설계", "구현")
        ]
        
        for i, mem1 in enumerate(memories):
            if not mem1.action:
                continue
                
            for j, mem2 in enumerate(memories[i+1:], i+1):
                if not mem2.action:
                    continue
                
                # Check if actions form causal pair
                for cause_action, effect_action in causal_patterns:
                    if (cause_action in mem1.action and 
                        effect_action in mem2.action):
                        
                        causalities.append({
                            "source_memory": i,
                            "target_memory": j,
                            "cause_action": mem1.action,
                            "effect_action": mem2.action,
                            "relationship_type": "causality",
                            "confidence": 0.7
                        })
        
        return causalities
    
    def _find_object_dependencies(self, memories: List[ActantParseResult]) -> List[Dict]:
        """Find dependencies between objects"""
        dependencies = []
        
        # Define dependency patterns
        dependency_keywords = [
            ("기능", "시스템"),
            ("버그", "코드"),
            ("테스트", "기능"),
            ("문서", "코드")
        ]
        
        object_memories = {}
        for i, mem in enumerate(memories):
            if mem.object_target:
                if mem.object_target not in object_memories:
                    object_memories[mem.object_target] = []
                object_memories[mem.object_target].append((i, mem))
        
        # Find objects that appear in related contexts
        for obj1, mems1 in object_memories.items():
            for obj2, mems2 in object_memories.items():
                if obj1 >= obj2:
                    continue
                
                # Check for dependency patterns
                for dep_obj1, dep_obj2 in dependency_keywords:
                    if (dep_obj1 in obj1 and dep_obj2 in obj2) or \
                       (dep_obj2 in obj1 and dep_obj1 in obj2):
                        
                        dependencies.append({
                            "object1": obj1,
                            "object2": obj2,
                            "relationship_type": "dependency",
                            "confidence": 0.6
                        })
        
        return dependencies