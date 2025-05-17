# 변경 내역 (Changelog)

## v0.5.2 (2025-05-19)

### 개선 사항

- `__init__.py` 모듈 임포트 순서 개선 및 예외 처리 강화
- 모듈 로딩 시 안정성 향상 및 순환 참조 방지
- `process_text` 별명이 모듈 네임스페이스에 올바르게 노출되도록 수정

### 버그 수정

- `convert_numpy_types` 중복 임포트 문제 해결
- 일부 모듈 임포트 실패 시 적절한 예외 처리 추가

## v0.5.1 (2025-05-18)

### 개선 사항

- numpy 데이터 타입을 Python 기본 타입으로 변환하는 유틸리티 함수 `convert_numpy_types` 추가
- API 클라이언트에 `proxies` 및 `timeout` 옵션 지원 추가
- OpenAI 임베딩 모델 클래스를 최신 API 스펙(OpenAI v1.0.0+)에 맞게 업데이트
- 다양한 프록시 환경에서의 호환성 개선

### 버그 수정

- JSON 직렬화 시 numpy 타입으로 인한 오류 해결

# Changelog

모든 중요한 변경 사항은 이 파일에 기록됩니다.

## [0.5.0] - 2025-05-17

### 추가
- 코드 모듈화 및 구조 개선
- 테스트 프레임워크 구축
- API 안정화 및 문서화 개선
- 오픈소스 기여 가이드라인 준비

### 변경
- 핵심 코드베이스를 greeum-core로 리브랜딩
- 메모리 검색 알고리즘 최적화
- 기본 템플릿 및 예제 개선

## [0.4.1] - 2025-05-16

### 변경
- MCP 기능을 [GreeumMCP](https://github.com/DryRainEnt/GreeumMCP) 프로젝트로 이전
- `memory_engine/mcp_*.py` 파일 및 관련 예제 제거
- setup.py에서 MCP 관련 엔트리 포인트 및 의존성 제거
- 문서 업데이트: README.md에서 MCP 관련 내용을 GreeumMCP 레포지토리 링크로 대체

## [0.4.0] - 2025-05-16

### 추가
- MCP(Model Control Protocol) 지원 기능 추가
  - `memory_engine/mcp_client.py`: MCP 클라이언트 구현
  - `memory_engine/mcp_service.py`: MCP 서비스 구현
  - `memory_engine/mcp_integrations.py`: Unity, Discord 등 외부 도구 연동 지원
- `examples/mcp_example.py`: MCP 사용 예제 추가
- WebSocket 기반 실시간 통신 지원
- API 키 관리 기능

### 변경
- 문서 업데이트: README.md에 MCP 관련 내용 추가
- 의존성 패키지 추가: websocket-client, jwt, uuid

## [0.3.0] - 2025-05-15

### 추가
- 다국어 시간 표현 인식 기능
- 임베딩 모델 통합
- 시간적 추론 메커니즘
- 키워드 추출 성능 개선

### 변경
- 블록체인 구조 최적화
- 웨이포인트 캐시 시스템 개선
- 단기 기억 만료 로직 개선

## [0.2.0] - 2025-05-15

### 추가
- REST API 서버 구현
- CLI 인터페이스 개선
- 프롬프트 생성 기능 강화

### 변경
- 메모리 블록 구조 개선
- 검색 알고리즘 성능 향상

## [0.1.0] - 2025-05-14

### 추가
- 최초 공개 릴리스
- 장기 기억 블록 관리자
- 단기 기억 관리자
- 기본 검색 기능 
