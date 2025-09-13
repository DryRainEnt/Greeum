"""
AI의 세밀한 메모리 저장 패턴 유도 시스템
- 정보, 경험, 추론 메모리 분류
- 세부 작업별 연속 메모리 저장 가이드
- Todo 기반 작업 시 중간 과정 메모리 저장 유도
"""
from typing import Dict, List, Any, Optional
from enum import Enum
import re
from datetime import datetime

class MemoryType(Enum):
    INFORMATION = "information"  # 정보 기억 (사실, 데이터, 참고사항)
    EXPERIENCE = "experience"    # 경험 기억 (과정, 시행착오, 학습)
    INFERENCE = "inference"      # 추론 기억 (결론, 통찰, 의사결정)

class AIMemoryGuidance:
    """AI의 메모리 저장 패턴을 개선하기 위한 가이드 시스템"""
    
    def __init__(self):
        # 메모리 저장을 유도할 핵심 신호들
        self.memory_triggers = {
            # 정보 기억 트리거
            'information_triggers': [
                r'확인했습니다', r'발견했습니다', r'알아냈습니다',
                r'파악했습니다', r'조사 결과', r'검색 결과',
                r'데이터를 보니', r'통계에 따르면', r'분석 결과'
            ],
            
            # 경험 기억 트리거  
            'experience_triggers': [
                r'시도해보겠습니다', r'테스트해보니', r'실행해보니',
                r'오류가 발생했습니다', r'성공했습니다', r'실패했습니다',
                r'개선했습니다', r'수정했습니다', r'해결했습니다'
            ],
            
            # 추론 기억 트리거
            'inference_triggers': [
                r'결론적으로', r'따라서', r'이를 통해',
                r'추론할 수 있습니다', r'판단됩니다', r'결정했습니다',
                r'최적화 방향', r'개선 방안', r'다음 단계'
            ]
        }
        
        # Todo 작업 시 메모리 저장 패턴
        self.todo_memory_patterns = {
            'task_start': "작업 시작: {task_name} - {context}",
            'task_progress': "진행 중: {task_name} - 현재 {current_step} 단계에서 {finding}",
            'task_obstacle': "장애 발생: {task_name} - {obstacle} 문제 해결 중",
            'task_breakthrough': "돌파구 발견: {task_name} - {solution} 방법으로 해결",
            'task_completion': "작업 완료: {task_name} - {result} 달성"
        }
        
        # 세밀한 저장을 위한 정보 분할 기준
        self.granular_patterns = {
            'code_changes': "코드 수정: {file_path}에서 {function_name} 함수 {change_type}",
            'config_updates': "설정 변경: {config_name}의 {parameter} 값을 {old_value}에서 {new_value}로 변경",
            'test_results': "테스트 결과: {test_name} - {result} ({details})",
            'error_analysis': "오류 분석: {error_type} 오류의 원인은 {cause}, 해결책: {solution}",
            'performance_metrics': "성능 측정: {operation}이 {duration}초 소요, {improvement} 개선"
        }
    
    def analyze_context_for_memory_opportunities(self, context: str, current_task: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        주어진 컨텍스트에서 메모리 저장 기회를 분석하고 구체적인 메모리 제안 생성
        """
        memory_suggestions = []
        
        # 1. 메모리 타입별 트리거 검사
        for memory_type, triggers in self.memory_triggers.items():
            for trigger_pattern in triggers:
                if re.search(trigger_pattern, context, re.IGNORECASE):
                    memory_type_enum = self._get_memory_type_from_string(memory_type)
                    suggestion = self._create_memory_suggestion(
                        context, memory_type_enum, trigger_pattern, current_task
                    )
                    memory_suggestions.append(suggestion)
        
        # 2. Todo 기반 작업 시 추가 메모리 제안
        if current_task:
            todo_suggestions = self._analyze_todo_memory_opportunities(context, current_task)
            memory_suggestions.extend(todo_suggestions)
        
        # 3. 세밀한 정보 분할 제안
        granular_suggestions = self._suggest_granular_memories(context)
        memory_suggestions.extend(granular_suggestions)
        
        return memory_suggestions
    
    def _get_memory_type_from_string(self, type_string: str) -> MemoryType:
        """문자열에서 MemoryType enum 반환"""
        type_mapping = {
            'information_triggers': MemoryType.INFORMATION,
            'experience_triggers': MemoryType.EXPERIENCE,
            'inference_triggers': MemoryType.INFERENCE
        }
        return type_mapping.get(type_string, MemoryType.INFORMATION)
    
    def _create_memory_suggestion(self, context: str, memory_type: MemoryType, 
                                trigger_pattern: str, current_task: Optional[str] = None) -> Dict[str, Any]:
        """메모리 저장 제안 생성"""
        
        # 컨텍스트에서 핵심 정보 추출
        key_info = self._extract_key_information(context, trigger_pattern)
        
        # 메모리 타입에 따른 최적화된 저장 형식
        memory_content = self._format_memory_by_type(key_info, memory_type, current_task)
        
        return {
            'memory_type': memory_type.value,
            'content': memory_content,
            'importance': self._calculate_importance(context, memory_type),
            'trigger_pattern': trigger_pattern,
            'extraction_context': key_info,
            'suggested_tags': self._suggest_tags(context, memory_type)
        }
    
    def _analyze_todo_memory_opportunities(self, context: str, current_task: str) -> List[Dict[str, Any]]:
        """Todo 작업 시 메모리 저장 기회 분석"""
        suggestions = []
        
        # Todo 패턴별 메모리 제안
        if "시작" in context or "start" in context.lower():
            content = self.todo_memory_patterns['task_start'].format(
                task_name=current_task,
                context=context[:100]
            )
            suggestions.append({
                'memory_type': MemoryType.EXPERIENCE.value,
                'content': content,
                'importance': 0.6,
                'tags': ['todo', 'task_start', current_task]
            })
        
        if "진행" in context or "progress" in context.lower():
            # 현재 단계와 발견사항 추출 시도
            current_step = self._extract_current_step(context)
            finding = self._extract_finding(context)
            
            content = self.todo_memory_patterns['task_progress'].format(
                task_name=current_task,
                current_step=current_step,
                finding=finding
            )
            suggestions.append({
                'memory_type': MemoryType.EXPERIENCE.value,
                'content': content,
                'importance': 0.7,
                'tags': ['todo', 'task_progress', current_task]
            })
        
        return suggestions
    
    def _suggest_granular_memories(self, context: str) -> List[Dict[str, Any]]:
        """세밀한 정보 분할을 위한 메모리 제안"""
        suggestions = []
        
        # 코드 변경 감지
        if re.search(r'파일.*수정|코드.*변경|함수.*추가', context):
            file_match = re.search(r'[/\w]+\.(py|js|ts|java|cpp)', context)
            file_path = file_match.group(0) if file_match else "파일"
            
            content = self.granular_patterns['code_changes'].format(
                file_path=file_path,
                function_name=self._extract_function_name(context),
                change_type=self._extract_change_type(context)
            )
            suggestions.append({
                'memory_type': MemoryType.INFORMATION.value,
                'content': content,
                'importance': 0.8,
                'tags': ['code', 'modification', file_path.split('.')[-1]]
            })
        
        # 설정 변경 감지
        if re.search(r'설정.*변경|config.*update|파라미터.*수정', context):
            content = f"Configuration change: {context[:100]}"
            suggestions.append({
                'memory_type': MemoryType.INFORMATION.value,
                'content': content,
                'importance': 0.7,
                'tags': ['configuration', 'update']
            })
        
        return suggestions
    
    def _extract_key_information(self, context: str, trigger_pattern: str) -> str:
        """트리거 패턴 주변의 핵심 정보 추출"""
        # 트리거 패턴 전후 50자씩 추출
        match = re.search(trigger_pattern, context, re.IGNORECASE)
        if match:
            start = max(0, match.start() - 50)
            end = min(len(context), match.end() + 50)
            return context[start:end].strip()
        return context[:100]
    
    def _format_memory_by_type(self, key_info: str, memory_type: MemoryType, current_task: Optional[str]) -> str:
        """메모리 타입에 따른 최적화된 형식"""
        timestamp = datetime.now().strftime("%H:%M")
        
        if memory_type == MemoryType.INFORMATION:
            return f"[INFO {timestamp}] {key_info}"
        elif memory_type == MemoryType.EXPERIENCE:
            task_prefix = f"[{current_task}] " if current_task else ""
            return f"[EXPERIENCE {timestamp}] {task_prefix}{key_info}"
        elif memory_type == MemoryType.INFERENCE:
            return f"[INFERENCE {timestamp}] {key_info}"
        
        return key_info
    
    def _calculate_importance(self, context: str, memory_type: MemoryType) -> float:
        """메모리 타입과 컨텍스트 기반 중요도 계산"""
        base_importance = {
            MemoryType.INFORMATION: 0.6,
            MemoryType.EXPERIENCE: 0.8,  # 경험은 더 중요
            MemoryType.INFERENCE: 0.9    # 추론은 가장 중요
        }
        
        # 컨텍스트 길이 고려 (길수록 중요)
        length_bonus = min(0.2, len(context) / 500)
        
        # 특정 키워드 포함 시 중요도 증가
        high_importance_keywords = ['문제', '해결', '중요', '발견', '성공', '실패']
        keyword_bonus = sum(0.1 for keyword in high_importance_keywords if keyword in context)
        
        return min(1.0, base_importance[memory_type] + length_bonus + keyword_bonus)
    
    def _suggest_tags(self, context: str, memory_type: MemoryType) -> List[str]:
        """컨텍스트 기반 태그 제안"""
        tags = [memory_type.value]
        
        # 기술 관련 태그
        tech_keywords = {
            'python': 'python', 'javascript': 'js', 'typescript': 'ts',
            'react': 'react', 'node': 'node', 'api': 'api',
            'database': 'db', 'sql': 'sql', 'docker': 'docker'
        }
        
        for keyword, tag in tech_keywords.items():
            if keyword in context.lower():
                tags.append(tag)
        
        # 작업 유형 태그
        work_types = {
            '개발': 'development', '테스트': 'testing', '배포': 'deployment',
            '디버그': 'debugging', '최적화': 'optimization', '설계': 'design'
        }
        
        for work_type, tag in work_types.items():
            if work_type in context:
                tags.append(tag)
        
        return tags
    
    def _extract_current_step(self, context: str) -> str:
        """현재 작업 단계 추출"""
        step_patterns = [
            r'(\d+)\s*단계', r'step\s*(\d+)', r'phase\s*(\d+)',
            r'첫.*단계', r'마지막.*단계', r'중간.*과정'
        ]
        
        for pattern in step_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return "current"
    
    def _extract_finding(self, context: str) -> str:
        """발견사항 추출"""
        # 문장을 나누어 핵심 발견사항 추출
        sentences = context.split('.')
        for sentence in sentences:
            if any(keyword in sentence for keyword in ['발견', '확인', '알아낸', '파악']):
                return sentence.strip()[:50]
        
        return context[:30]
    
    def _extract_function_name(self, context: str) -> str:
        """함수명 추출"""
        func_match = re.search(r'def\s+(\w+)|function\s+(\w+)|(\w+)\s*\(', context)
        if func_match:
            return func_match.group(1) or func_match.group(2) or func_match.group(3)
        return "function"
    
    def _extract_change_type(self, context: str) -> str:
        """변경 타입 추출"""
        if '추가' in context or 'add' in context.lower():
            return "added"
        elif '수정' in context or 'modify' in context.lower():
            return "modified"
        elif '삭제' in context or 'delete' in context.lower():
            return "deleted"
        return "changed"

def generate_memory_guidance_prompt() -> str:
    """AI에게 제공할 메모리 저장 가이드 프롬프트 생성"""
    return """
## [MEMORY] Greeum 메모리 저장 최적화 가이드

### [NOTE] 기본 원칙
1. **세밀한 분할**: 큰 정보를 작은 단위로 나누어 저장
2. **연속 기록**: Todo 작업 시 각 단계마다 메모리 저장
3. **타입 분류**: 정보/경험/추론으로 명확히 구분

### 🎯 필수 메모리 저장 시점
- **작업 시작 시**: "시작: [작업명] - [초기 상황]"  
- **진행 과정 중**: "진행: [작업명] - [현재 단계]에서 [발견사항]"
- **문제 발생 시**: "장애: [작업명] - [문제 상황] 해결 중"
- **돌파구 시**: "해결: [작업명] - [해결책] 적용"
- **완료 시**: "완료: [작업명] - [최종 결과]"

### 📊 메모리 타입별 저장 형식
- **[정보]**: 객관적 사실, 데이터, 참고사항
- **[경험]**: 과정, 시행착오, 학습 내용  
- **[추론]**: 결론, 통찰, 의사결정

### [FAST] 즉시 메모리 저장이 필요한 신호
- "확인했습니다", "발견했습니다", "파악했습니다" → 정보 메모리
- "시도해보니", "테스트 결과", "오류 발생" → 경험 메모리  
- "결론적으로", "따라서", "최적화 방향" → 추론 메모리

**중요**: 길고 포괄적인 메모리보다는 짧고 구체적인 메모리를 자주 저장하세요.
"""