# Greeum v3.0.0: LLM 기반 액탄트 파싱 시스템
## MCP를 통한 고정확도 구조화 전략

---

## 🎯 **핵심 아이디어**

**"파싱 엔진을 만들지 말고, LLM의 언어 이해력을 활용하자"**

### 장점
- ✅ **정확도**: 90-95% (자체 파서 60-80% 대비)
- ✅ **개발 속도**: 2-3주 (자체 개발 3-4개월 대비)
- ✅ **유지보수**: LLM 자체 개선으로 자동 향상
- ✅ **다국어**: 완벽한 한국어/영어/혼합 처리
- ✅ **문맥 이해**: 암묵적 의미까지 파악

---

## 🏗️ **시스템 아키텍처**

```mermaid
graph LR
    A[새 메모리] --> B[Greeum MCP Tool]
    B --> C[LLM 파싱 요청]
    C --> D[구조화된 액탄트]
    D --> E[DB 저장]
    E --> F[관계 분석]
```

### 1. **MCP Tool 정의**

```python
# greeum/mcp/tools/llm_parsing_tools.py

class LLMParsingTools:
    """LLM을 활용한 액탄트 파싱 도구"""
    
    @tool(
        name="parse_memory_to_actant",
        description="Parse memory text into structured actant format"
    )
    async def parse_to_actant(self, text: str) -> Dict:
        """
        메모리 텍스트를 액탄트 구조로 파싱 요청
        
        LLM이 이 도구를 호출받으면:
        1. 텍스트 분석
        2. [주체-행동-객체] 추출
        3. 신뢰도 평가
        4. 구조화된 결과 반환
        """
        
        # LLM에게 전달될 프롬프트
        prompt = f"""
        다음 텍스트를 액탄트 모델로 분석해주세요:
        
        텍스트: "{text}"
        
        다음 형식으로 응답:
        {{
            "subject": "주체 (누가/무엇이)",
            "action": "행동 (무엇을 했는지)",
            "object": "객체 (대상/목적)",
            "confidence": 0.0-1.0,
            "reasoning": "판단 근거"
        }}
        
        예시:
        텍스트: "사용자가 새로운 기능을 요청했다"
        응답: {{
            "subject": "사용자",
            "action": "요청",
            "object": "새로운 기능",
            "confidence": 0.95,
            "reasoning": "명시적 주체-행동-객체 구조"
        }}
        """
        
        # 이 부분이 핵심: LLM이 직접 파싱 수행
        return await self.llm_request(prompt)
```

### 2. **통합 플로우**

```python
class MemoryProcessor:
    """메모리 처리 파이프라인"""
    
    async def process_new_memory(self, text: str):
        # Step 1: LLM 파싱 (MCP를 통해)
        actant_data = await self.mcp_client.call_tool(
            "parse_memory_to_actant",
            {"text": text}
        )
        
        # Step 2: 동일성 확인
        subject_hash = await self.mcp_client.call_tool(
            "get_actant_hash",
            {"actant": actant_data["subject"], "type": "subject"}
        )
        
        # Step 3: DB 저장
        block = self.save_to_database({
            "context": text,
            "actant_subject": actant_data["subject"],
            "actant_action": actant_data["action"],
            "actant_object": actant_data["object"],
            "subject_hash": subject_hash,
            "parsing_confidence": actant_data["confidence"]
        })
        
        # Step 4: 관계 분석 (역시 LLM 활용)
        relationships = await self.analyze_relationships(block)
        
        return block, relationships
```

### 3. **실시간 파싱 예시**

```python
# Claude가 실제로 수행할 작업

@when_memory_added
async def on_memory_added(memory_text: str):
    """새 메모리 추가시 자동 파싱"""
    
    # Claude에게 파싱 요청
    result = await claude.parse(memory_text)
    
    # 예시 응답
    if memory_text == "프로젝트가 성공해서 팀이 보너스를 받았다":
        return {
            "actants": [
                {
                    "subject": "프로젝트",
                    "action": "성공",
                    "object": None,
                    "confidence": 0.90
                },
                {
                    "subject": "팀", 
                    "action": "받다",
                    "object": "보너스",
                    "confidence": 0.95
                }
            ],
            "causal_relation": {
                "cause": "프로젝트 성공",
                "effect": "팀 보너스",
                "confidence": 0.85
            }
        }
```

---

## 🔄 **배치 마이그레이션 전략**

### 기존 247개 메모리 처리

```python
async def migrate_existing_memories():
    """기존 메모리 LLM 파싱 마이그레이션"""
    
    memories = get_all_memories()  # 247개
    batch_size = 10  # API 제한 고려
    
    for batch in chunks(memories, batch_size):
        # 배치 파싱 요청
        parsing_prompt = f"""
        다음 {len(batch)}개 메모리를 액탄트 구조로 파싱:
        
        {format_batch(batch)}
        
        각각에 대해 [주체-행동-객체] 추출
        """
        
        results = await llm_batch_parse(parsing_prompt)
        
        # DB 업데이트
        for memory, result in zip(batch, results):
            update_memory_actants(memory.id, result)
        
        # Rate limiting
        await asyncio.sleep(1)
```

---

## 💡 **고급 기능: LLM 추론 활용**

### 1. **동일성 판별**

```python
async def are_same_entity(text1: str, text2: str) -> bool:
    """LLM에게 동일 개체 여부 판단 요청"""
    
    prompt = f"""
    다음 두 표현이 같은 대상을 가리키는지 판단:
    
    1. "{text1}"
    2. "{text2}"
    
    맥락:
    - 개발 프로젝트 환경
    - 한국어/영어 혼용 가능
    - 대명사 치환 고려
    
    응답: {{"same": true/false, "confidence": 0.0-1.0}}
    """
    
    result = await llm_request(prompt)
    return result["same"] and result["confidence"] > 0.7
```

### 2. **인과관계 추론**

```python
async def analyze_causality(memory1: Dict, memory2: Dict) -> Dict:
    """LLM 기반 인과관계 분석"""
    
    prompt = f"""
    두 사건의 인과관계 분석:
    
    사건 1: {memory1["actant_subject"]}가 {memory1["actant_action"]}
    시간: {memory1["timestamp"]}
    
    사건 2: {memory2["actant_subject"]}가 {memory2["actant_action"]}  
    시간: {memory2["timestamp"]}
    
    분석 관점:
    1. 시간적 순서
    2. 논리적 연결성
    3. 주체/객체 연관성
    
    응답 형식:
    {{
        "has_causal_relation": true/false,
        "direction": "1→2" or "2→1" or "bidirectional",
        "confidence": 0.0-1.0,
        "reasoning": "판단 근거"
    }}
    """
    
    return await llm_request(prompt)
```

### 3. **패턴 발견**

```python
async def discover_patterns(memories: List[Dict]) -> List[Pattern]:
    """LLM이 메모리 패턴 발견"""
    
    prompt = f"""
    다음 메모리들에서 반복되는 패턴을 찾아주세요:
    
    {format_memories(memories)}
    
    찾을 패턴:
    - 반복되는 행동 시퀀스
    - 주기적 이벤트
    - 인과관계 체인
    - 협업 패턴
    """
    
    patterns = await llm_request(prompt)
    return patterns
```

---

## 📊 **성능 및 비용 분석**

### 정확도 비교

| 방법 | 정확도 | 개발시간 | 유지보수 |
|------|--------|----------|----------|
| 자체 파서 | 60-80% | 3-4개월 | 지속 필요 |
| LLM 활용 | 90-95% | 2-3주 | 자동 개선 |

### API 비용 예상

```python
# Claude API 기준 (예상)
- 파싱: $0.01 per 1K tokens
- 247개 메모리: ~$2-3
- 일일 신규 50개: ~$0.5/day
- 월 비용: ~$15-20

# 비용 최적화
1. 배치 처리로 API 호출 최소화
2. 캐싱으로 중복 파싱 방지
3. 신뢰도 높은 결과만 재파싱
```

---

## 🚀 **구현 로드맵 (수정)**

### Phase 1: MCP Tool 구현 (1주)
```
- parse_memory_to_actant 도구 구현
- get_actant_hash 도구 구현
- analyze_causality 도구 구현
```

### Phase 2: 통합 파이프라인 (1주)
```
- 메모리 추가시 자동 파싱
- 배치 마이그레이션 시스템
- 결과 검증 도구
```

### Phase 3: 고급 기능 (1주)
```
- 패턴 발견 시스템
- 실시간 인사이트 생성
- 사용자 피드백 반영
```

---

## 🎯 **예상 결과**

### Before (자체 파서)
```
"프로젝트가 성공했다" 
→ 주체: "프로젝트" (60% 확신)
→ 행동: "성공" (불확실)
→ 객체: ??? (파싱 실패)
```

### After (LLM 파싱)
```
"프로젝트가 성공했다"
→ 주체: "프로젝트" (95% 확신)
→ 행동: "성공하다" (90% 확신)
→ 객체: null (해당없음으로 정확 판단)
→ 추가 인사이트: "긍정적 결과, 후속 액션 예상"
```

---

## 💬 **실제 대화 예시**

```python
# 사용자가 메모리 추가
User: greeum memory add "버그 수정 후 배포 완료"

# Claude가 자동으로 파싱
Claude (내부):
- 텍스트 분석 중...
- 액탄트 추출: 
  * 주체: (암묵적 - 개발자/나)
  * 행동: "수정" → "배포"
  * 객체: "버그" → "시스템"
- 인과관계: 수정 → 배포 (순차적)

# 저장 결과
Memory #251:
- Context: "버그 수정 후 배포 완료"
- Subject: "개발자" (inferred)
- Actions: ["수정", "배포"]  
- Objects: ["버그", "시스템"]
- Causality: fix→deploy (0.9)
```

---

## 🏆 **결론**

**LLM 활용 = 게임 체인저**

- 개발 기간: 3-4개월 → 2-3주
- 정확도: 60-80% → 90-95%
- 유지보수: 지속 필요 → 자동 개선
- 비용: 월 $15-20 (충분히 감당 가능)

**"왜 바퀴를 재발명하나? LLM이 이미 완벽한 바퀴다!"**