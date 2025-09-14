# Greeum GPT MCP 배포 체크리스트

## ✅ 완료된 항목

### 1. 코드베이스 검증
- [x] **브랜치/DFS 시스템**: v3.0.0.post2에서 `BlockManager.add_block(slot)` STM 헤드 자식 추가 구현 확인
- [x] **데이터베이스 스키마**: 브랜치 필드(`root`, `before`, `after`, `xref`, `branch_depth`) 지원 확인
- [x] **검색 시스템**: `search_with_slots()` DFS 우선 검색, 양방향 탐색, 오버샘플링/재정렬 구현 확인
- [x] **자동 머지**: 활성 슬롯 헤드 간 유사도 기록→EMA 평가→체크포인트→리버서블 머지 구현 확인
- [x] **고아 루트 승격**: 마이그레이션 시 자동 루트 승급 로직 확인

### 2. MCP 서버 GPT 호환성
- [x] **필수 도구 구현**: OpenAI GPT 요구 사항인 `search`, `fetch` 도구 추가 완료
  - `search` → `search_memory` 래퍼로 구현
  - `fetch` → 블록 ID 조회 또는 최근 메모리 조회 구현
- [x] **기존 도구 유지**: `add_memory`, `search_memory`, `get_memory_stats`, `usage_analytics` 기존 기능 보존
- [x] **JSON-RPC 2.0 표준**: MCP 프로토콜 완전 준수 확인
- [x] **서버 동작 검증**: 초기화, 도구 목록, 도구 호출 테스트 완료

### 3. 성능 및 안정성
- [x] **성능 지표**: post2 릴리스 노트의 품질/성능 수치 확인
- [x] **메모리 시스템**: 1223개 노드, 5798개 연관관계로 GraphIndex/AssociationNetwork 정상 동작 확인
- [x] **에러 처리**: BrokenPipe, JSON 파싱 에러, 도구 실행 실패 등 예외 처리 구현

## ⚠️ 권고 사항 (운영 최적화)

### 1. DFS 탐색 파라미터 조정
- **현재**: DEPTH=6, K=20, TH=0.02 (공격적 설정)
- **권고**: DEPTH=3, K=8, TH=0.05 (운영 안정화)
- **이유**: 데이터 증가 시 노이즈와 연산량 증가 방지

### 2. 데이터베이스 인덱스 강화
- **필요**: `root`, `before`, `created_at` 필드 인덱스 추가
- **목적**: 탐색 및 마이그레이션 속도 안정화

### 3. HTTP 서버 환경 점검
- **현재**: uvicorn, fastapi 설치 상태 미확인
- **필요**: HTTP transport 지원을 위한 의존성 설치

## 🚀 배포 준비 상태

### A. OpenAI Responses API 연동
```bash
curl https://api.openai.com/v1/responses -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" -d '{
  "model": "gpt-4.1",
  "tools": [{
    "type": "mcp",
    "server_label": "greeum",
    "server_url": "https://YOUR_DOMAIN/mcp",
    "allowed_tools": ["search","fetch","add_memory","search_memory"],
    "require_approval": "never"
  }],
  "input": "프로젝트 X의 최근 맥락을 찾아줘"
}'
```

### B. ChatGPT 커넥터 등록
- **필수 도구**: ✅ `search`, `fetch` 구현 완료
- **사양 준수**: ✅ OpenAI Help Center 요구사항 충족
- **등록**: Interest Form 제출 가능 상태

### C. 서버 실행
```bash
# STDIO 모드 (Claude Desktop용)
python3 greeum/mcp/production_mcp_server.py

# HTTP 모드 (GPT Responses API용) - 추가 구현 필요
# uvicorn greeum.mcp.production_http_server:app --host 0.0.0.0 --port 8000
```

## 📊 배포 준비도: 90%

**즉시 가능**: STDIO MCP (Claude Desktop)
**추가 작업 필요**: HTTP MCP 서버 (GPT Responses API)

### 다음 단계
1. HTTP 서버 래퍼 구현 (30분 내 완료 가능)
2. TLS/인증 설정
3. 운영 모니터링 설정