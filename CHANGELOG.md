# Changelog

모든 중요한 변경 사항은 이 파일에 기록됩니다.

## [0.4.1] - 2023-11-10

### 변경
- MCP 기능을 [GreeumMCP](https://github.com/DryRainEnt/GreeumMCP) 프로젝트로 이전
- `memory_engine/mcp_*.py` 파일 및 관련 예제 제거
- setup.py에서 MCP 관련 엔트리 포인트 및 의존성 제거
- 문서 업데이트: README.md에서 MCP 관련 내용을 GreeumMCP 레포지토리 링크로 대체

## [0.4.0] - 2023-11-07

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

## [0.3.0] - 2023-10-15

### 추가
- 다국어 시간 표현 인식 기능
- 임베딩 모델 통합
- 시간적 추론 메커니즘
- 키워드 추출 성능 개선

### 변경
- 블록체인 구조 최적화
- 웨이포인트 캐시 시스템 개선
- 단기 기억 만료 로직 개선

## [0.2.0] - 2023-09-20

### 추가
- REST API 서버 구현
- CLI 인터페이스 개선
- 프롬프트 생성 기능 강화

### 변경
- 메모리 블록 구조 개선
- 검색 알고리즘 성능 향상

## [0.1.0] - 2023-08-10

### 추가
- 최초 공개 릴리스
- 장기 기억 블록 관리자
- 단기 기억 관리자
- 기본 검색 기능 