# Greeum v2.0 MCP Connection Guide

## 개요

Greeum v2.0에서는 완전히 새로운 방식의 안정적이고 환경 독립적인 MCP (Model Control Protocol) 연동 방법을 제공합니다. 기존의 복잡한 환경 설정 없이도 어떤 환경에서든 쉽게 Claude Code와 연동할 수 있습니다.

## 🎯 핵심 특징

### 🆕 새로운 Simple MCP Bridge 방식
- **환경 독립적**: 어떤 Python 환경에서도 동작
- **최소 의존성**: 내장 라이브러리만 사용 (numpy, faiss 등 불필요)
- **단일 파일**: 복잡한 설정 없이 바로 실행
- **CLI 기반**: Greeum v2.0 통합 CLI를 직접 호출
- **강력한 오류 처리**: 연결 실패 시 자동 복구 시도

### 🔧 기술적 구조
```
greeum/mcp/simple_mcp_bridge.py  ← 핵심 MCP 서버
├── SimpleMCPBridge             ← Greeum CLI 호출 브리지
├── SimpleMCPProtocol           ← JSON-RPC 프로토콜 처리
└── CLI 자동 감지                ← 환경별 최적 실행 방법 선택
```

## 🚀 설치 및 연동 방법

### 1. 전제 조건 확인
```bash
# Python 3.6+ 설치 확인
python3 --version

# Greeum v2.0 설치 확인
cd /Users/dryrain/DevRoom/Greeum
python3 -c "import greeum; print('Greeum v2.0 ready')"
```

### 2. Claude Code MCP 연결
```bash
# Claude Code에서 MCP 서버 추가
claude mcp add greeum python3 /Users/dryrain/DevRoom/Greeum/greeum/mcp/simple_mcp_bridge.py --env PYTHONPATH=/Users/dryrain/DevRoom/Greeum

# 연결 상태 확인
claude mcp list
# 결과: greeum: python3 ... - ✓ Connected
```

### 3. 연결 성공 확인
```bash
# MCP 도구 사용 가능 확인
# Claude Code 세션에서 mcp__greeum_mcp__add_memory, mcp__greeum_mcp__search_memory 도구 사용 가능
```

## 🛠️ 사용 가능한 MCP 도구

### 1. add_memory
메모리를 Greeum v2.0 장기 저장소에 추가합니다.

**파라미터:**
- `content` (string, 필수): 저장할 메모리 내용
- `importance` (number, 선택): 중요도 점수 (0.0-1.0, 기본값: 0.5)

**예시:**
```python
# Claude Code에서 사용
mcp__greeum_mcp__add_memory(content="새로운 프로젝트 아이디어", importance=0.8)
```

### 2. search_memory  
키워드나 의미적 유사성으로 메모리를 검색합니다.

**파라미터:**
- `query` (string, 필수): 검색 쿼리
- `limit` (number, 선택): 최대 결과 개수 (기본값: 5)

**예시:**
```python
# Claude Code에서 사용
mcp__greeum_mcp__search_memory(query="프로젝트", limit=10)
```

### 3. memory_stats
Greeum v2.0 메모리 시스템의 통계 정보를 조회합니다.

**파라미터:** 없음

**예시:**
```python
# Claude Code에서 사용
mcp__greeum_mcp__memory_stats()
```

## 🔍 기술적 세부사항

### CLI 자동 감지 로직
1. **Python 모듈 방식**: `python3 -m greeum.cli` (권장)
2. **설치된 명령어**: `greeum` (pip install 후)
3. **직접 실행**: Python 파일 직접 호출

### 명령어 변환 예시
```python
# MCP 호출: add_memory(content="테스트", importance=0.7)
# CLI 변환: greeum memory add "테스트" --importance 0.7

# MCP 호출: search_memory(query="검색어", limit=5) 
# CLI 변환: greeum memory search "검색어" --limit 5
```

### 오류 처리
- **CLI 실행 실패**: JSON 형태로 오류 메시지 반환
- **파싱 오류**: 안전한 기본값으로 처리
- **연결 실패**: 자동 재시도 및 상세 로그

## 🔄 기존 방식과의 차이점

### ❌ 기존 복잡한 방식
- 복잡한 환경 변수 설정 필요
- numpy, faiss 등 의존성 설치 필요
- 환경별 호환성 문제
- 연결 실패 시 디버깅 어려움

### ✅ 새로운 Simple Bridge 방식
- 환경 설정 최소화
- 내장 라이브러리만 사용
- 어떤 Python 환경에서도 동작
- 명확한 오류 메시지와 로그

## 🐛 문제 해결

### 연결 실패 시
1. **Python 경로 확인**
   ```bash
   which python3
   python3 --version
   ```

2. **Greeum 경로 확인**
   ```bash
   ls -la /Users/dryrain/DevRoom/Greeum/greeum/mcp/simple_mcp_bridge.py
   ```

3. **PYTHONPATH 확인**
   ```bash
   export PYTHONPATH=/Users/dryrain/DevRoom/Greeum:$PYTHONPATH
   python3 -c "import greeum.core; print('Import successful')"
   ```

4. **수동 테스트**
   ```bash
   cd /Users/dryrain/DevRoom/Greeum
   echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python3 greeum/mcp/simple_mcp_bridge.py
   ```

### CLI 오류 시
```bash
# Greeum v2.0 CLI 직접 테스트
python3 -m greeum.cli memory add "테스트 메모리"
python3 -m greeum.cli memory search "테스트"
```

## 📈 성공 사례

### 연결 성공 확인 방법
```bash
$ claude mcp list
Checking MCP server health...

greeum: python3 /Users/dryrain/DevRoom/Greeum/greeum/mcp/simple_mcp_bridge.py - ✓ Connected
```

### 실제 사용 예시
```python
# Claude Code 세션에서
>>> mcp__greeum_mcp__add_memory(content="MCP connection successful with Greeum v2.0 simple bridge")
Memory added: MCP connection successful with Greeum v2.0 simple bridge

>>> mcp__greeum_mcp__search_memory(query="MCP connection")
[검색 결과 반환]
```

## 🎉 결론

Greeum v2.0의 새로운 Simple MCP Bridge는 기존의 복잡한 연동 방식을 완전히 개선하여:

- **개발자 경험 향상**: 간단한 한 줄 명령어로 연동 완료
- **안정성 증대**: 환경 독립적이고 강력한 오류 처리
- **유지보수성**: 단일 파일로 모든 기능 제공
- **확장성**: Greeum v2.0의 모든 기능에 MCP를 통해 접근 가능

이 방식을 통해 어떤 환경에서도 Claude Code와 Greeum 간의 안정적인 메모리 연동이 가능합니다.

---

## 📝 업데이트 기록

- **2025-07-30**: Greeum v2.0 Simple MCP Bridge 첫 버전 출시
- **핵심 성과**: 환경 독립적 MCP 연동 방식 확립, 기존 복잡한 설정 방식 대체