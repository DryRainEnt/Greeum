# Greeum API 레퍼런스

이 문서는 Greeum의 모든 주요 API를 설명합니다. Greeum의 각 클래스와 기능을 활용하여 고급 기억 시스템을 구축할 수 있습니다.

## 목차

- [BlockManager](#blockmanager) - 장기 기억 관리
- [STMManager](#stmmanager) - 단기 기억 관리
- [CacheManager](#cachemanager) - 웨이포인트 캐시
- [PromptWrapper](#promptwrapper) - 프롬프트 조합
- [TemporalReasoner](#temporalreasoner) - 시간 기반 추론
- [MCPClient](#mcpclient) - MCP 클라이언트
- [MCPService](#mcpservice) - MCP 서비스
- [MCPIntegrations](#mcpintegrations) - MCP 통합 유틸리티
- [텍스트 유틸리티](#텍스트-유틸리티) - 텍스트 처리 도구

---

## BlockManager

블록체인 구조의 장기 기억을 관리하는 클래스입니다.

### 주요 메서드

#### `__init__(storage_dir=None, embedding_model=None)`

BlockManager 객체를 초기화합니다.

- `storage_dir` (str, 선택): 메모리 블록을 저장할 디렉토리 경로
- `embedding_model` (object, 선택): 임베딩 생성에 사용할 모델

#### `add_block(context, keywords=None, tags=None, embedding=None, importance=None, timestamp=None)`

새로운 메모리 블록을 생성하고 저장합니다.

- `context` (str): 기억의 내용
- `keywords` (list, 선택): 관련 키워드 목록
- `tags` (list, 선택): 관련 태그 목록
- `embedding` (list, 선택): 사전 계산된 임베딩 벡터
- `importance` (float, 선택): 기억의 중요도 (0.0~1.0)
- `timestamp` (str, 선택): ISO 형식의 타임스탬프 (기본값: 현재 시간)

**반환**: 생성된 블록 객체

#### `get_block(block_index)`

특정 인덱스의 블록을 검색합니다.

- `block_index` (int): 검색할 블록의 인덱스

**반환**: 블록 객체 또는 None

#### `get_blocks(limit=100, offset=0, sort="desc")`

여러 블록을 검색합니다.

- `limit` (int, 선택): 반환할 최대 블록 수
- `offset` (int, 선택): 시작 오프셋
- `sort` (str, 선택): 정렬 방향 ("desc" 또는 "asc")

**반환**: 블록 객체 목록

#### `search_blocks_by_keyword(keywords, limit=10, operator="or")`

키워드로 블록을 검색합니다.

- `keywords` (list): 검색할 키워드 목록
- `limit` (int, 선택): 반환할 최대 블록 수
- `operator` (str, 선택): 검색 연산자 ("or" 또는 "and")

**반환**: 블록 객체 목록

#### `search_blocks_by_embedding(embedding, top_k=5)`

임베딩 유사도로 블록을 검색합니다.

- `embedding` (list): 검색할 임베딩 벡터
- `top_k` (int, 선택): 반환할 최대 블록 수

**반환**: 블록 객체 목록

#### `search_blocks_by_date_range(from_date, to_date, limit=100)`

날짜 범위로 블록을 검색합니다.

- `from_date` (str): ISO 형식의 시작 날짜
- `to_date` (str): ISO 형식의 종료 날짜
- `limit` (int, 선택): 반환할 최대 블록 수

**반환**: 블록 객체 목록

#### `verify_chain()`

블록체인 무결성을 검증합니다.

**반환**: 검증 결과 (bool)

---

## STMManager

TTL 기반의 단기 기억을 관리하는 클래스입니다.

### 주요 메서드

#### `__init__(ttl_short=3600, ttl_medium=86400, ttl_long=604800)`

STMManager 객체를 초기화합니다.

- `ttl_short` (int, 선택): 단기 기억 TTL (초)
- `ttl_medium` (int, 선택): 중기 기억 TTL (초)
- `ttl_long` (int, 선택): 장기 기억 TTL (초)

#### `add_memory(content, ttl_type="medium", importance=0.5)`

새로운 단기 기억을 추가합니다.

- `content` (str): 기억 내용
- `ttl_type` (str, 선택): TTL 유형 ("short", "medium", "long")
- `importance` (float, 선택): 기억 중요도 (0.0~1.0)

**반환**: 메모리 ID

#### `get_memories(limit=10, include_expired=False)`

단기 기억을 검색합니다.

- `limit` (int, 선택): 반환할 최대 기억 수
- `include_expired` (bool, 선택): 만료된 기억 포함 여부

**반환**: 기억 객체 목록

#### `forget(memory_id)`

특정 단기 기억을 삭제합니다.

- `memory_id` (str): 삭제할 기억의 ID

**반환**: 성공 여부 (bool)

#### `cleanup_expired()`

만료된 단기 기억을 정리합니다.

**반환**: 정리된 기억 수

---

## CacheManager

효율적인 기억 검색을 위한 웨이포인트 캐시 관리 클래스입니다.

### 주요 메서드

#### `__init__(block_manager, capacity=10)`

CacheManager 객체를 초기화합니다.

- `block_manager` (BlockManager): 블록 관리자 인스턴스
- `capacity` (int, 선택): 캐시 용량

#### `update_cache(query_embedding, query_keywords=None)`

쿼리 컨텍스트에 따라 캐시를 업데이트합니다.

- `query_embedding` (list): 쿼리 임베딩 벡터
- `query_keywords` (list, 선택): 쿼리 관련 키워드

**반환**: 캐시된 블록 목록

#### `get_relevant_blocks(query_embedding, query_keywords=None, limit=5)`

쿼리와 관련된 블록을 검색합니다.

- `query_embedding` (list): 쿼리 임베딩 벡터
- `query_keywords` (list, 선택): 쿼리 관련 키워드
- `limit` (int, 선택): 반환할 최대 블록 수

**반환**: 관련 블록 목록

#### `clear_cache()`

캐시를 비웁니다.

---

## PromptWrapper

기억을 포함한 LLM 프롬프트를 자동 생성하는 클래스입니다.

### 주요 메서드

#### `__init__(cache_manager, stm_manager=None, template=None)`

PromptWrapper 객체를 초기화합니다.

- `cache_manager` (CacheManager): 캐시 관리자 인스턴스
- `stm_manager` (STMManager, 선택): 단기 기억 관리자 인스턴스
- `template` (str, 선택): 프롬프트 템플릿

#### `compose_prompt(user_input, include_stm=True, max_blocks=3, max_stm=5)`

사용자 입력과 관련 기억을 포함한 프롬프트를 생성합니다.

- `user_input` (str): 사용자 입력
- `include_stm` (bool, 선택): 단기 기억 포함 여부
- `max_blocks` (int, 선택): 포함할 최대 블록 수
- `max_stm` (int, 선택): 포함할 최대 단기 기억 수

**반환**: 생성된 프롬프트 문자열

#### `set_template(template)`

프롬프트 템플릿을 설정합니다.

- `template` (str): 새 템플릿

---

## TemporalReasoner

시간 표현 인식 및 처리를 위한 클래스입니다.

### 주요 메서드

#### `__init__(db_manager=None, default_language="auto")`

TemporalReasoner 객체를 초기화합니다.

- `db_manager` (BlockManager, 선택): 블록 관리자 인스턴스
- `default_language` (str, 선택): 기본 언어 ("ko", "en", "auto" 등)

#### `extract_time_references(query)`

쿼리에서 시간 참조를 추출합니다.

- `query` (str): 검색 쿼리

**반환**: 시간 참조 목록

#### `search_by_time_reference(query, margin_hours=12)`

시간 참조를 기반으로 메모리를 검색합니다.

- `query` (str): 검색 쿼리
- `margin_hours` (int, 선택): 시간 여유 (경계 확장)

**반환**: 검색 결과 및 메타데이터

#### `hybrid_search(query, embedding, keywords, time_weight=0.3, embedding_weight=0.5, keyword_weight=0.2, top_k=5)`

시간, 임베딩, 키워드 기반 하이브리드 검색을 수행합니다.

- `query` (str): 검색 쿼리
- `embedding` (list): 쿼리 임베딩
- `keywords` (list): 추출된 키워드
- `time_weight` (float, 선택): 시간 가중치
- `embedding_weight` (float, 선택): 임베딩 가중치
- `keyword_weight` (float, 선택): 키워드 가중치
- `top_k` (int, 선택): 상위 k개 결과 반환

**반환**: 하이브리드 검색 결과

---

## MCPClient

MCP(Model Control Protocol) 클라이언트 클래스입니다. 외부 도구와 Greeum을 연결합니다.

### 주요 메서드

#### `__init__(api_key, base_url="http://localhost:8000/api/mcp")`

MCPClient 객체를 초기화합니다.

- `api_key` (str): MCP API 키
- `base_url` (str, 선택): MCP API 기본 URL

#### `manage_memory(action, memory_content="", memory_id=None, query=None, limit=10)`

메모리 관리 API 호출을 수행합니다.

- `action` (str): 수행할 작업 - "add", "get", "query", "update", "delete"
- `memory_content` (str, 선택): 추가/업데이트할 메모리 내용
- `memory_id` (str, 선택): 메모리 ID (get, update, delete 시 필요)
- `query` (str, 선택): 검색 쿼리 (query 작업 시 필요)
- `limit` (int, 선택): 반환할 최대 결과 수

**반환**: API 응답 (Dict)

#### `execute_menu_item(menu_path)`

Unity 메뉴 아이템을 실행합니다.

- `menu_path` (str): 메뉴 경로 (예: "GameObject/Create Empty")

**반환**: API 응답 (Dict)

#### `select_gameobject(object_path=None, instance_id=None)`

Unity 게임오브젝트를 선택합니다.

- `object_path` (str, 선택): 게임오브젝트 경로
- `instance_id` (int, 선택): 게임오브젝트 인스턴스 ID

**반환**: API 응답 (Dict)

#### `add_package(source, **kwargs)`

Unity 패키지를 추가합니다.

- `source` (str): 패키지 소스 (registry, github, disk)
- `**kwargs`: 패키지 추가에 필요한 추가 파라미터

**반환**: API 응답 (Dict)

#### `run_tests(test_mode="EditMode", test_filter="", return_only_failures=True)`

Unity 테스트를 실행합니다.

- `test_mode` (str, 선택): 테스트 모드 (EditMode 또는 PlayMode)
- `test_filter` (str, 선택): 테스트 필터
- `return_only_failures` (bool, 선택): 실패한 테스트만 반환 여부

**반환**: API 응답 (Dict)

#### `send_console_log(message, log_type="info")`

Unity 콘솔에 로그 메시지를 전송합니다.

- `message` (str): 로그 메시지
- `log_type` (str, 선택): 로그 타입 (info, warning, error)

**반환**: API 응답 (Dict)

#### `update_component(component_name, **kwargs)`

Unity 컴포넌트를 업데이트합니다.

- `component_name` (str): 컴포넌트 이름
- `**kwargs`: 컴포넌트 업데이트에 필요한 추가 파라미터

**반환**: API 응답 (Dict)

#### `add_asset_to_scene(**kwargs)`

Unity 씬에 에셋을 추가합니다.

- `**kwargs`: 에셋 추가에 필요한 파라미터

**반환**: API 응답 (Dict)

---

## MCPService

MCP 서비스를 제공하는 클래스입니다.

### 주요 메서드

#### `__init__(data_dir="./data", port=8000)`

MCPService 객체를 초기화합니다.

- `data_dir` (str, 선택): 데이터 디렉토리 경로
- `port` (int, 선택): 서비스 포트

#### `start()`

MCP 서비스를 시작합니다.

### CLI 도구 인터페이스

CLI를 통해 MCP 서비스를 실행할 수 있습니다:

```bash
greeum-mcp --data-dir ./data --port 8000
```

또는 Python 모듈로 직접 실행:

```bash
python -m memory_engine.mcp_service --data-dir ./data --port 8000
```

---

## MCPIntegrations

외부 도구와 Greeum을 통합하는 유틸리티 클래스입니다.

### 주요 메서드

#### `__init__(data_dir="./data", config_path="./data/mcp_config.json")`

MCPIntegrations 객체를 초기화합니다.

- `data_dir` (str, 선택): 데이터 디렉토리 경로
- `config_path` (str, 선택): MCP 구성 파일 경로

#### `store_unity_event(event_type, event_data)`

Unity 이벤트를 기억으로 저장합니다.

- `event_type` (str): 이벤트 타입
- `event_data` (Dict): 이벤트 데이터

**반환**: 생성된 기억 ID

#### `store_discord_event(event_type, event_data)`

Discord 이벤트를 기억으로 저장합니다.

- `event_type` (str): 이벤트 타입
- `event_data` (Dict): 이벤트 데이터

**반환**: 생성된 기억 ID

#### `get_related_unity_memories(query, limit=5)`

Unity 관련 기억을 검색합니다.

- `query` (str): 검색 쿼리
- `limit` (int, 선택): 반환할 최대 결과 수

**반환**: 검색 결과 목록

#### `get_related_discord_memories(query, limit=5)`

Discord 관련 기억을 검색합니다.

- `query` (str): 검색 쿼리
- `limit` (int, 선택): 반환할 최대 결과 수

**반환**: 검색 결과 목록

---

## 텍스트 유틸리티

텍스트 처리를 위한 유틸리티 함수들입니다.

### 주요 함수

#### `process_user_input(text, extract_keywords=True, extract_tags=True, compute_embedding=True)`

사용자 입력을 처리합니다.

- `text` (str): 처리할 텍스트
- `extract_keywords` (bool, 선택): 키워드 추출 여부
- `extract_tags` (bool, 선택): 태그 추출 여부
- `compute_embedding` (bool, 선택): 임베딩 계산 여부

**반환**: 처리된 결과 딕셔너리

#### `extract_keywords(text, language="auto", max_keywords=5)`

텍스트에서 키워드를 추출합니다.

- `text` (str): 처리할 텍스트
- `language` (str, 선택): 텍스트 언어
- `max_keywords` (int, 선택): 최대 키워드 수

**반환**: 키워드 목록

#### `extract_tags(text, language="auto")`

텍스트에서 태그를 추출합니다.

- `text` (str): 처리할 텍스트
- `language` (str, 선택): 텍스트 언어

**반환**: 태그 목록

#### `compute_embedding(text)`

텍스트의 임베딩 벡터를 계산합니다.

- `text` (str): 임베딩할 텍스트

**반환**: 임베딩 벡터

#### `estimate_importance(text)`

텍스트의 중요도를 추정합니다.

- `text` (str): 평가할 텍스트

**반환**: 중요도 점수 (0.0~1.0)

---

## 고급 사용법

### CLI 도구

Greeum은 다양한 명령줄 도구를 제공합니다. 자세한 내용은 [CLI 도구 문서](tutorials.md#cli-도구)를 참조하세요.

### REST API

Greeum의 REST API를 사용하여 애플리케이션을 통합할 수 있습니다. 자세한 내용은 [API 서버 문서](tutorials.md#rest-api-서버)를 참조하세요.

### MCP 활용

MCP를 통해 Greeum과 외부 도구를 연동하는 방법은 [MCP 예제](../examples/README.md)를 참조하세요. 