# Greeum 개발자 가이드

이 문서는 Greeum의 핵심 API를 활용하여 개발하려는 개발자를 위한 간결한 레퍼런스입니다. GreeumMCP와 같은 외부 프로젝트 개발 시 특히 유용합니다.

## 목차

1. [BlockManager - 장기 기억 관리](#blockmanager---장기-기억-관리)
2. [STMManager - 단기 기억 관리](#stmmanager---단기-기억-관리)
3. [CacheManager - 캐시 관리](#cachemanager---캐시-관리)
4. [PromptWrapper - 프롬프트 생성](#promptwrapper---프롬프트-생성)
5. [TemporalReasoner - 시간 추론](#temporalreasoner---시간-추론)
6. [텍스트 유틸리티](#텍스트-유틸리티)
7. [통합 예제](#통합-예제)

## BlockManager - 장기 기억 관리

장기 기억을 블록체인 구조로 저장하고 관리합니다.

```python
from memory_engine.block_manager import BlockManager

# 초기화
block_manager = BlockManager(data_dir="./data")

# 기억 추가
memory_id = block_manager.add_memory("이것은 장기 기억에 저장될 내용입니다.")
# 또는 상세 정보와 함께 추가
memory_id = block_manager.add_block(
    context="상세한 기억 내용",
    keywords=["키워드1", "키워드2"],
    tags=["태그1", "태그2"],
    importance=0.8  # 0.0~1.0
)

# 기억 조회
memory = block_manager.get_memory(memory_id)
# 또는
block = block_manager.get_block(block_index)

# 기억 검색
blocks = block_manager.search_blocks_by_keyword(["키워드1", "키워드2"], limit=5)
# 임베딩 기반 검색
similar_blocks = block_manager.search_blocks_by_embedding(embedding_vector, top_k=5)
# 날짜 범위 검색
date_blocks = block_manager.search_blocks_by_date_range("2023-01-01", "2023-01-31")

# 기억 업데이트
block_manager.update_memory(memory_id, "업데이트된 내용")

# 기억 삭제
block_manager.delete_memory(memory_id)

# 블록체인 무결성 검증
is_valid = block_manager.verify_chain()
```

핵심 속성:
- `data_dir`: 데이터 저장 경로
- `blocks`: 모든 블록 목록
- `embedding_model`: 임베딩 생성에 사용되는 모델

## STMManager - 단기 기억 관리

TTL(Time-To-Live) 기반의 단기 기억을 관리합니다.

```python
from memory_engine.stm_manager import STMManager

# 초기화
stm_manager = STMManager(data_dir="./data")

# 단기 기억 추가
memory_id = stm_manager.add_memory(
    "이것은 단기 기억입니다.",
    ttl=3600,  # 초 단위 (1시간)
    importance=0.7  # 0.0~1.0
)
# 또는 사전 정의된 TTL 유형 사용
memory_id = stm_manager.add_memory(
    "이것은 중기 기억입니다.",
    ttl_type="medium"  # "short", "medium", "long" 중 하나
)

# 단기 기억 조회
memories = stm_manager.get_memories(limit=10)
# 만료된 기억 포함
all_memories = stm_manager.get_memories(include_expired=True)

# 단기 기억 검색
results = stm_manager.search("검색어", limit=5)

# 특정 단기 기억 삭제
stm_manager.forget(memory_id)

# 만료된 모든 기억 정리
cleaned_count = stm_manager.cleanup_expired()
```

핵심 속성:
- `ttl_short`: 단기 기억 TTL (기본값: 1시간)
- `ttl_medium`: 중기 기억 TTL (기본값: 1일)
- `ttl_long`: 장기 기억 TTL (기본값: 1주일)

## CacheManager - 캐시 관리

효율적인 기억 검색을 위한 웨이포인트 캐시를 관리합니다.

```python
from memory_engine.block_manager import BlockManager
from memory_engine.cache_manager import CacheManager

# 블록 관리자 초기화
block_manager = BlockManager(data_dir="./data")

# 캐시 관리자 초기화
cache_manager = CacheManager(block_manager=block_manager, capacity=10)

# 캐시 업데이트
cache_manager.update_cache(
    query_embedding=[0.1, 0.2, ...],  # 쿼리 임베딩 벡터
    query_keywords=["키워드1", "키워드2"]  # 쿼리 키워드
)

# 관련 블록 검색
relevant_blocks = cache_manager.get_relevant_blocks(
    query_embedding=[0.1, 0.2, ...],
    query_keywords=["키워드1", "키워드2"],
    limit=5
)

# 키워드만으로 검색
keyword_blocks = cache_manager.search("키워드", limit=5)

# 캐시 비우기
cache_manager.clear_cache()
```

핵심 속성:
- `capacity`: 캐시의 최대 용량
- `block_manager`: 연결된 BlockManager 인스턴스

## PromptWrapper - 프롬프트 생성

기억을 포함한 LLM 프롬프트를 자동 생성합니다.

```python
from memory_engine.block_manager import BlockManager
from memory_engine.cache_manager import CacheManager
from memory_engine.stm_manager import STMManager
from memory_engine.prompt_wrapper import PromptWrapper

# 관리자 초기화
block_manager = BlockManager(data_dir="./data")
cache_manager = CacheManager(block_manager=block_manager)
stm_manager = STMManager(data_dir="./data")

# 프롬프트 래퍼 초기화
prompt_wrapper = PromptWrapper(
    cache_manager=cache_manager,
    stm_manager=stm_manager
)

# 기본 프롬프트 생성
prompt = prompt_wrapper.compose_prompt(
    user_input="프로젝트 진행 상황은 어때?",
    include_stm=True,  # 단기 기억 포함 여부
    max_blocks=3,  # 최대 블록 수
    max_stm=5  # 최대 단기 기억 수
)

# 사용자 정의 템플릿 설정
custom_template = """
너는 기억을 가진 AI 비서야. 다음 정보를 기반으로 질문에 답변해줘:

<장기 기억>
{long_term_memories}
</장기 기억>

<단기 기억>
{short_term_memories}
</단기 기억>

유저: {user_input}
AI: 
"""
prompt_wrapper.set_template(custom_template)

# 새 템플릿으로 프롬프트 생성
prompt = prompt_wrapper.compose_prompt("새 프로젝트는 어떻게 진행되고 있어?")

# LLM에 전달
# llm_response = call_your_llm(prompt)
```

핵심 속성:
- `cache_manager`: 캐시 관리자 인스턴스
- `stm_manager`: 단기 기억 관리자 인스턴스 (선택 사항)
- `template`: 프롬프트 템플릿

## TemporalReasoner - 시간 추론

시간 표현 인식 및 처리를 담당합니다.

```python
from memory_engine.block_manager import BlockManager
from memory_engine.temporal_reasoner import TemporalReasoner

# 블록 관리자 초기화
block_manager = BlockManager(data_dir="./data")

# 시간 추론기 초기화
temporal_reasoner = TemporalReasoner(
    db_manager=block_manager,
    default_language="auto"  # "ko", "en", "auto" 중 하나
)

# 시간 참조 추출
time_refs = temporal_reasoner.extract_time_references("3일 전에 뭐 했어?")

# 시간 기반 검색
results = temporal_reasoner.search_by_time_reference(
    "어제 먹은 저녁 메뉴가 뭐였지?",
    margin_hours=12  # 시간 경계 확장
)

# 하이브리드 검색 (시간 + 임베딩 + 키워드)
hybrid_results = temporal_reasoner.hybrid_search(
    query="어제 읽은 책 제목이 뭐였지?",
    embedding=[0.1, 0.2, ...],
    keywords=["책", "제목"],
    time_weight=0.3,
    embedding_weight=0.5,
    keyword_weight=0.2,
    top_k=5
)
```

핵심 속성:
- `db_manager`: 연결된 BlockManager 인스턴스
- `default_language`: 기본 언어 설정

## 텍스트 유틸리티

텍스트 처리를 위한 유틸리티 함수들입니다.

```python
from memory_engine.text_utils import (
    process_user_input,
    extract_keywords,
    extract_tags,
    compute_embedding,
    estimate_importance
)

# 사용자 입력 처리
processed = process_user_input(
    "이것은 처리할 텍스트입니다.",
    extract_keywords=True,
    extract_tags=True,
    compute_embedding=True
)
# 결과: {"context": "...", "keywords": [...], "tags": [...], "embedding": [...], "importance": 0.x}

# 키워드 추출
keywords = extract_keywords(
    "키워드를 추출할 텍스트입니다.",
    language="ko",  # "ko", "en", "auto" 중 하나
    max_keywords=5
)

# 태그 추출
tags = extract_tags(
    "태그를 추출할 텍스트입니다.",
    language="auto"
)

# 임베딩 계산
embedding = compute_embedding("임베딩을 계산할 텍스트입니다.")

# 중요도 추정
importance = estimate_importance("중요도를 계산할 텍스트입니다.")  # 0.0~1.0 사이 값
```

## 통합 예제

다음은 Greeum의 핵심 구성 요소를 통합하여 사용하는 예제입니다:

```python
from memory_engine.block_manager import BlockManager
from memory_engine.stm_manager import STMManager
from memory_engine.cache_manager import CacheManager
from memory_engine.prompt_wrapper import PromptWrapper
from memory_engine.temporal_reasoner import TemporalReasoner
from memory_engine.text_utils import process_user_input

# 기본 경로 설정
data_dir = "./data"

# 컴포넌트 초기화
block_manager = BlockManager(data_dir=data_dir)
stm_manager = STMManager(data_dir=data_dir)
cache_manager = CacheManager(block_manager=block_manager)
prompt_wrapper = PromptWrapper(cache_manager=cache_manager, stm_manager=stm_manager)
temporal_reasoner = TemporalReasoner(db_manager=block_manager, default_language="auto")

# 사용자 입력 처리
user_input = "프로젝트를 시작했는데 정말 흥미진진해!"
processed = process_user_input(user_input)

# 장기 기억 추가
memory_id = block_manager.add_block(
    context=processed["context"],
    keywords=processed["keywords"],
    tags=processed["tags"],
    embedding=processed["embedding"],
    importance=processed["importance"]
)

# 단기 기억에도 추가
stm_id = stm_manager.add_memory(processed["context"], ttl_type="medium")

# 캐시 업데이트
cache_manager.update_cache(
    query_embedding=processed["embedding"],
    query_keywords=processed["keywords"]
)

# 시간 기반 검색 질의
time_query = "어제 무슨 일이 있었지?"
time_results = temporal_reasoner.search_by_time_reference(time_query)

# 프롬프트 생성
user_question = "그 프로젝트 진행 상황은 어때?"
prompt = prompt_wrapper.compose_prompt(user_question)

# LLM에 전달하여 응답 생성
# llm_response = call_your_llm(prompt)
```

## 확장 및 통합 포인트

Greeum을 다른 시스템과 통합할 때 사용할 수 있는 주요 포인트:

1. **임베딩 모델 교체**:
   ```python
   from custom_embedding import CustomEmbeddingModel
   
   custom_model = CustomEmbeddingModel()
   block_manager = BlockManager(embedding_model=custom_model)
   ```

2. **데이터 저장소 확장**:
   BlockManager와 STMManager는 기본적으로 파일 시스템에 데이터를 저장하지만, 데이터베이스 통합을 위해 확장할 수 있습니다.

3. **커스텀 프롬프트 템플릿**:
   PromptWrapper의 템플릿을 사용자 정의하여 다양한 LLM에 최적화된 프롬프트를 생성할 수 있습니다.

4. **확장 클래스 구현**:
   기본 클래스를 상속받아 기능을 확장하는 방식으로 커스텀 기능을 구현할 수 있습니다.

더 자세한 API 설명은 [API 레퍼런스](api-reference.md)를 참조하세요. 
