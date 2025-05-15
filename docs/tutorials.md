# Greeum 튜토리얼

이 튜토리얼에서는 Greeum을 사용하여 다양한 기능을 구현하는 방법을 단계별로 설명합니다. 이 가이드를 통해 Greeum의 핵심 기능을 빠르게 배울 수 있습니다.

## 목차

1. [시작하기](#시작하기)
2. [기본 기억 관리](#기본-기억-관리)
3. [시간 기반 검색](#시간-기반-검색)
4. [다국어 지원 활용](#다국어-지원-활용)
5. [LLM 통합](#llm-통합)
6. [CLI 도구](#cli-도구)
7. [REST API 서버](#rest-api-서버)
8. [고급 기능](#고급-기능)

## 시작하기

Greeum을 설치하고 기본 초기화하는 방법을 알아봅니다.

### 필수 설정

먼저 [설치 가이드](installation.md)에 따라 Greeum을 설치하세요.

### 기본 초기화

```python
from greeum import BlockManager, STMManager, CacheManager, PromptWrapper

# 기본 블록 매니저 초기화
block_manager = BlockManager(storage_dir="./data/memory")

# 단기 기억 매니저 초기화
stm_manager = STMManager(
    ttl_short=3600,      # 1시간
    ttl_medium=86400,    # 1일
    ttl_long=604800      # 1주일
)

# 캐시 매니저 초기화
cache_manager = CacheManager(
    block_manager=block_manager,
    capacity=10
)

# 프롬프트 래퍼 초기화
prompt_wrapper = PromptWrapper(
    cache_manager=cache_manager,
    stm_manager=stm_manager
)

print("Greeum 초기화 완료!")
```

## 기본 기억 관리

Greeum을 사용하여 기억을 저장하고 검색하는 방법을 알아봅니다.

### 장기 기억 저장

```python
from greeum import BlockManager
from greeum.text_utils import process_user_input

# 블록 매니저 초기화
block_manager = BlockManager()

# 사용자 입력 처리
user_input = "새로운 프로젝트를 시작했는데 머신러닝 알고리즘을 활용해 이미지 인식 시스템을 개발할 계획이야."
processed = process_user_input(user_input)

# 중요도를 높게 설정하여 블록 저장
block = block_manager.add_block(
    context=processed["context"],
    keywords=processed["keywords"],
    tags=processed["tags"],
    embedding=processed["embedding"],
    importance=0.9  # 중요한 기억이므로 높은 값 설정
)

print(f"저장된 블록 인덱스: {block['block_index']}")
```

### 키워드로 기억 검색

```python
# 키워드로 기억 검색
search_results = block_manager.search_blocks_by_keyword(
    keywords=["프로젝트", "머신러닝"],
    limit=5
)

print(f"검색 결과 수: {len(search_results)}")
for result in search_results:
    print(f"블록 {result['block_index']}: {result['context'][:50]}...")
```

### 단기 기억 관리

```python
from greeum import STMManager

# 단기 기억 매니저 초기화
stm_manager = STMManager()

# 다양한 TTL로 단기 기억 추가
stm_manager.add_memory(
    content="미팅은 오후 3시에 예정되어 있습니다.",
    ttl_type="short"  # 짧은 유지 시간 (기본 1시간)
)

stm_manager.add_memory(
    content="프로젝트 제안서는 다음 주 금요일까지 제출해야 합니다.",
    ttl_type="medium"  # 중간 유지 시간 (기본 1일)
)

stm_manager.add_memory(
    content="새 머신러닝 알고리즘은 98.5% 정확도를 달성했습니다.",
    ttl_type="long",   # 긴 유지 시간 (기본 1주일)
    importance=0.8     # 중요한 정보
)

# 단기 기억 조회
memories = stm_manager.get_memories(limit=10)
for mem in memories:
    print(f"[{mem['ttl_type']}] {mem['content']}")
```

## 시간 기반 검색

시간 표현을 인식하고 시간에 따라 기억을 검색하는 방법을 알아봅니다.

### 시간 표현 인식

```python
from greeum.temporal_reasoner import TemporalReasoner, evaluate_temporal_query

# 시간 표현 평가 (한국어)
ko_result = evaluate_temporal_query("어제 회의에서 결정된 사항을 알려줘", language="ko")
print(f"한국어 시간 표현: {ko_result['detected']}, 표현: {ko_result.get('best_ref', {}).get('term')}")

# 시간 표현 평가 (영어)
en_result = evaluate_temporal_query("Tell me what was decided in yesterday's meeting", language="en")
print(f"영어 시간 표현: {en_result['detected']}, 표현: {en_result.get('best_ref', {}).get('term')}")

# 자동 언어 감지
auto_result = evaluate_temporal_query("What did I do 3 days ago?")
print(f"감지된 언어: {auto_result['language']}, 표현: {auto_result.get('best_ref', {}).get('term')}")
```

### 시간 기반 기억 검색

```python
# 시간 기반 검색 설정
temporal_reasoner = TemporalReasoner(db_manager=block_manager, default_language="auto")

# 시간 표현을 이용한 검색
query = "지난주에 있었던 미팅 내용을 알려줘"
results = temporal_reasoner.search_by_time_reference(query)

print(f"감지된 시간 표현: {results.get('time_ref', {}).get('term')}")
print(f"검색 범위: {results.get('search_range', {})}")
print(f"검색 결과 수: {len(results.get('blocks', []))}")

# 결과 출력
for block in results.get('blocks', []):
    print(f"[{block['timestamp']}] {block['context'][:50]}...")
```

## 다국어 지원 활용

Greeum의 다국어 지원 기능을 사용하는 방법을 알아봅니다.

### 다국어 처리 설정

```python
from greeum.temporal_reasoner import TemporalReasoner
from greeum.text_utils import extract_keywords, extract_tags

# 자동 언어 감지 설정
temporal_reasoner = TemporalReasoner(default_language="auto")

# 다양한 언어 처리 예제
languages = {
    "ko": "어제 프로젝트 회의에서 새로운 아이디어를 논의했습니다.",
    "en": "We discussed new ideas in yesterday's project meeting.",
    "mixed": "프로젝트 meeting에서 new ideas를 discussed."
}

for lang_name, text in languages.items():
    # 언어 감지
    detected_lang = temporal_reasoner._detect_language(text)
    
    # 키워드 추출
    keywords = extract_keywords(text, language="auto")
    
    # 태그 추출
    tags = extract_tags(text, language="auto")
    
    print(f"텍스트 ({lang_name}): {text}")
    print(f"감지된 언어: {detected_lang}")
    print(f"추출된 키워드: {keywords}")
    print(f"추출된 태그: {tags}")
    print("-" * 50)
```

### 다국어 시간 표현 처리

```python
# 다양한 언어의 시간 표현 예제
time_expressions = {
    "ko": [
        "어제 회의",
        "3일 전에 작성한 문서",
        "지난주 금요일에 보낸 이메일",
        "2023년 5월 15일 미팅"
    ],
    "en": [
        "yesterday's meeting",
        "document written 3 days ago",
        "email sent last Friday",
        "meeting on May 15, 2023"
    ]
}

for lang, expressions in time_expressions.items():
    print(f"언어: {lang}")
    for expr in expressions:
        result = evaluate_temporal_query(expr, language=lang)
        if result["detected"]:
            time_ref = result.get("best_ref", {})
            print(f"  표현: '{expr}' -> '{time_ref.get('term')}' 감지됨")
            from_date = time_ref.get("from_date", "N/A")
            to_date = time_ref.get("to_date", "N/A")
            print(f"  시간 범위: {from_date} ~ {to_date}")
        else:
            print(f"  표현: '{expr}' -> 시간 표현 감지되지 않음")
    print("-" * 50)
```

## LLM 통합

Greeum을 LLM과 통합하는 방법을 알아봅니다.

### 프롬프트 생성

```python
from greeum import BlockManager, STMManager, CacheManager, PromptWrapper
from greeum.text_utils import process_user_input, compute_embedding

# 매니저 초기화
block_manager = BlockManager()
stm_manager = STMManager()
cache_manager = CacheManager(block_manager=block_manager)

# 몇 가지 기억 추가
block_manager.add_block(
    context="프로젝트의 첫 번째 단계로 데이터 수집 방법을 연구하기로 했습니다.",
    keywords=["프로젝트", "데이터", "수집", "연구"],
    importance=0.8
)

stm_manager.add_memory(
    content="클라이언트는 다음 주까지 초기 프로토타입을 원합니다.",
    ttl_type="medium",
    importance=0.9
)

# 프롬프트 래퍼 설정
prompt_wrapper = PromptWrapper(
    cache_manager=cache_manager,
    stm_manager=stm_manager
)

# 사용자 질문
user_question = "프로젝트 진행 상황에 대해 알려줘"

# 질문 임베딩 계산
question_embedding = compute_embedding(user_question)

# 캐시 업데이트
cache_manager.update_cache(
    query_embedding=question_embedding,
    query_keywords=["프로젝트", "진행", "상황"]
)

# 프롬프트 생성
prompt = prompt_wrapper.compose_prompt(
    user_input=user_question,
    include_stm=True,
    max_blocks=3,
    max_stm=3
)

print("생성된 프롬프트:")
print("-" * 50)
print(prompt)
print("-" * 50)

# 실제 LLM 호출 (예시)
# llm_response = call_your_llm(prompt)
# print("LLM 응답:", llm_response)
```

### 커스텀 프롬프트 템플릿

```python
# 커스텀 템플릿 설정
custom_template = """
당신은 기억을 가진 지능형 비서입니다.

다음은 당신이 알고 있는 중요한 정보입니다:
{memory_blocks}

다음은 최근에 언급된 정보입니다:
{short_term_memories}

사용자 질문: {user_input}

위 정보를 바탕으로 사용자의 질문에 친절하고 자세하게 대답해주세요.
"""

# 프롬프트 래퍼에 템플릿 설정
prompt_wrapper.set_template(custom_template)

# 새 프롬프트 생성
new_prompt = prompt_wrapper.compose_prompt(user_question)

print("커스텀 템플릿으로 생성된 프롬프트:")
print("-" * 50)
print(new_prompt)
print("-" * 50)
```

## CLI 도구

Greeum CLI 도구를 사용하는 방법을 알아봅니다.

### 기본 CLI 명령어

```bash
# 장기 기억 추가
python cli/memory_cli.py add -c "머신러닝 프로젝트의 첫 번째 단계로 데이터 수집을 시작했습니다."

# 키워드로 기억 검색
python cli/memory_cli.py search -k "머신러닝,프로젝트,데이터"

# 시간 표현으로 기억 검색
python cli/memory_cli.py search-time -q "어제 한 일을 알려줘" -l "ko"

# 단기 기억 추가
python cli/memory_cli.py stm "다음 미팅은 수요일 오후 3시입니다."

# 단기 기억 조회
python cli/memory_cli.py get-stm

# 프롬프트 생성
python cli/memory_cli.py prompt -i "프로젝트 진행 상황은 어떻게 되고 있나요?"
```

### CLI 고급 옵션

```bash
# 중요도를 지정하여 기억 추가
python cli/memory_cli.py add -c "새로운 알고리즘 개발 완료" -i 0.9

# 태그 지정하여 기억 추가
python cli/memory_cli.py add -c "클라이언트 미팅에서 요구사항 변경됨" -t "미팅,중요,클라이언트"

# 블록 세부 정보 보기
python cli/memory_cli.py get-block -i 1

# 블록체인 무결성 검증
python cli/memory_cli.py verify

# 단기 기억 삭제
python cli/memory_cli.py forget-stm -i "memory_id_here"

# 만료된 단기 기억 정리
python cli/memory_cli.py cleanup-stm
```

## REST API 서버

Greeum REST API를 사용하는 방법을 알아봅니다.

### 서버 실행

```bash
# API 서버 실행
python api/memory_api.py
```

서버는 기본적으로 http://localhost:5000 에서 실행됩니다.

### API 호출 예제

#### cURL을 사용한 API 호출

```bash
# 상태 확인
curl http://localhost:5000/api/v1/health

# 블록 추가
curl -X POST \
  http://localhost:5000/api/v1/blocks \
  -H "Content-Type: application/json" \
  -d '{"context": "새로운 데이터 분석 결과가 나왔습니다.", "keywords": ["데이터", "분석", "결과"], "importance": 0.8}'

# 키워드로 검색
curl http://localhost:5000/api/v1/search?keywords=데이터,분석

# 시간 표현으로 검색
curl http://localhost:5000/api/v1/search/time?query=어제&language=ko

# 단기 기억 추가
curl -X POST \
  http://localhost:5000/api/v1/stm \
  -H "Content-Type: application/json" \
  -d '{"content": "내일 회의에서 데이터 분석 결과를 발표합니다.", "ttl_type": "medium"}'

# 단기 기억 조회
curl http://localhost:5000/api/v1/stm

# 프롬프트 생성
curl -X POST \
  http://localhost:5000/api/v1/prompt \
  -H "Content-Type: application/json" \
  -d '{"input": "데이터 분석 결과에 대해 알려줘", "include_stm": true}'
```

#### Python 클라이언트 예제

```python
import requests
import json

# API 기본 URL
base_url = "http://localhost:5000/api/v1"

# 블록 추가
def add_block(context, keywords=None, tags=None, importance=0.5):
    url = f"{base_url}/blocks"
    data = {
        "context": context,
        "keywords": keywords or [],
        "tags": tags or [],
        "importance": importance
    }
    response = requests.post(url, json=data)
    return response.json()

# 키워드로 검색
def search_by_keywords(keywords, limit=10):
    url = f"{base_url}/search"
    params = {
        "keywords": ",".join(keywords),
        "limit": limit
    }
    response = requests.get(url, params=params)
    return response.json()

# 시간 표현으로 검색
def search_by_time(query, language="auto", margin_hours=12):
    url = f"{base_url}/search/time"
    params = {
        "query": query,
        "language": language,
        "margin_hours": margin_hours
    }
    response = requests.get(url, params=params)
    return response.json()

# 사용 예
block = add_block(
    context="새로운 머신러닝 알고리즘이 95% 정확도를 달성했습니다.",
    keywords=["머신러닝", "알고리즘", "정확도"],
    tags=["연구", "성공", "AI"],
    importance=0.9
)
print(f"추가된 블록: {block}")

results = search_by_keywords(["머신러닝", "알고리즘"])
print(f"검색 결과: {len(results)} 블록 찾음")

time_results = search_by_time("어제 연구한 내용", language="ko")
print(f"시간 검색 결과: {len(time_results.get('blocks', []))} 블록 찾음")
```

## 고급 기능

Greeum의 고급 기능을 사용하는 방법을 알아봅니다.

### 하이브리드 검색

```python
from greeum.temporal_reasoner import TemporalReasoner
from greeum.text_utils import process_user_input

# 설정
block_manager = BlockManager()
temporal_reasoner = TemporalReasoner(db_manager=block_manager)

# 사용자 쿼리 처리
query = "어제 머신러닝 프로젝트에서 발생한 문제에 대해 알려줘"
processed = process_user_input(query)

# 하이브리드 검색 실행
results = temporal_reasoner.hybrid_search(
    query=query,
    embedding=processed["embedding"],
    keywords=processed["keywords"],
    time_weight=0.4,       # 시간 가중치 증가
    embedding_weight=0.4,  # 임베딩 가중치
    keyword_weight=0.2,    # 키워드 가중치
    top_k=10               # 상위 10개 결과
)

print(f"하이브리드 검색 결과: {len(results.get('blocks', []))} 블록 찾음")
print(f"적용된 가중치: {results.get('weights')}")

# 결과 표시
for block in results.get('blocks', []):
    print(f"[점수: {block.get('relevance_score', 0):.2f}] {block['context'][:50]}...")
```

### 임베딩 모델 커스텀

```python
from greeum import BlockManager
from greeum.embedding_models import DefaultEmbedding

# 기본 임베딩 모델 대신 커스텀 모델 구현
class CustomEmbedding(DefaultEmbedding):
    def encode(self, text):
        # 여기에 원하는 외부 임베딩 모델을 호출하는 코드 작성
        # 예: sentence-transformers, OpenAI embeddings 등
        print(f"커스텀 임베딩: '{text[:30]}...'")
        
        # 예시 임베딩 반환 (실제 구현에서는 실제 모델 사용)
        import numpy as np
        vector = np.random.randn(384)  # 384차원 랜덤 벡터
        return vector.tolist()

# 커스텀 임베딩 모델로 블록 매니저 초기화
custom_embedding = CustomEmbedding()
block_manager = BlockManager(embedding_model=custom_embedding)

# 블록 추가 시 커스텀 임베딩 사용
block = block_manager.add_block(
    context="커스텀 임베딩 모델을 사용한 기억 저장 테스트입니다.",
    keywords=["임베딩", "커스텀", "테스트"]
)

print(f"임베딩 벡터 길이: {len(block['embedding'])}")
```

이 튜토리얼을 통해 Greeum의 기본 기능부터 고급 기능까지 다양한 사용법을 배웠습니다. 더 많은 정보와 세부 사항은 [API 레퍼런스](api-reference.md)를 참조하세요. 