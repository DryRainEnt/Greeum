# Greeum v2.0 설치 및 사용 가이드

## 🚀 빠른 설치 (pipx 권장)

### 1. pipx로 설치
```bash
# pipx가 없다면 먼저 설치
brew install pipx  # macOS
# 또는 pip install --user pipx

# Greeum v2.0 모든 기능 포함 설치
pipx install greeum[all]
```

### 2. 설치 확인
```bash
greeum --version
greeum --help
```

## 📋 기본 사용법

### 메모리 기본 기능
```bash
# 장기 메모리에 추가
greeum memory add "새로운 아이디어가 떠올랐다"

# 메모리 검색
greeum memory search "아이디어"

# 메모리 시스템 상태 확인
greeum memory stats
```

### LTM (장기 기억) 전용 기능
```bash
# 메모리 패턴 분석
greeum ltm analyze --trends --period 6m

# 블록체인 무결성 검증
greeum ltm verify

# 데이터 내보내기
greeum ltm export --format blockchain --limit 100
```

### STM (단기 기억) 전용 기능
```bash
# TTL 기반 임시 메모리 추가
greeum stm add "회의 메모" --ttl 2h --importance 0.7

# 중요한 STM → LTM 자동 승격
greeum stm promote --threshold 0.8

# 지능형 STM 정리
greeum stm cleanup --smart --threshold 0.3
```

## 🔗 Claude Code MCP 연동

### 1. MCP 서버 시작
```bash
# 백그라운드에서 MCP 서버 실행
greeum mcp serve
```

### 2. Claude Code에서 MCP 연결
```bash
# Claude Code CLI에서 MCP 서버 추가
claude mcp add greeum greeum mcp serve
```

### 3. 연결 확인
```bash
claude mcp list
# 결과: greeum: greeum mcp serve - ✓ Connected
```

### 4. 사용 가능한 MCP 도구 (총 9개)

#### 기본 메모리 도구
- `add_memory`: LTM에 메모리 추가
- `search_memory`: 키워드/의미적 검색  
- `get_memory_stats`: 메모리 시스템 통계

#### LTM 전용 도구
- `ltm_analyze`: 패턴 및 트렌드 분석
- `ltm_verify`: 블록체인 무결성 검증
- `ltm_export`: JSON/블록체인/CSV 형식 내보내기

#### STM 전용 도구  
- `stm_add`: TTL 기반 임시 메모리 추가
- `stm_promote`: 중요도 기반 STM → LTM 자동 승격
- `stm_cleanup`: 지능형 STM 정리

## 📁 데이터 저장 위치

### 기본 저장 경로
- **macOS/Linux**: `~/.greeum/`
- **Windows**: `%APPDATA%\\Greeum`

### 저장되는 파일들
```
~/.greeum/
├── memory.db          # SQLite 메모리 데이터베이스
├── stm_cache.json     # 단기 메모리 캐시
├── vector_index/      # FAISS 벡터 인덱스 (선택사항)
└── exports/           # 내보내기 파일들
```

## ⚙️ 고급 설정

### 환경 변수
```bash
# 데이터 디렉토리 변경
export GREEUM_DATA_DIR="/custom/path"

# 로그 레벨 설정
export GREEUM_LOG_LEVEL="DEBUG"

# MCP 서버 포트 변경
export GREEUM_MCP_PORT="3001"
```

### 설정 파일
```bash
# 사용자별 설정 파일 위치
~/.greeum/config.json
```

## 🔧 문제 해결

### 일반적인 문제들

1. **"greeum command not found"**
   ```bash
   # pipx 경로 확인
   pipx list
   
   # 쉘 재시작 또는 PATH 추가
   export PATH="$HOME/.local/bin:$PATH"
   ```

2. **MCP 연결 실패**
   ```bash
   # MCP 서버 상태 확인
   greeum mcp serve --help
   
   # 포트 충돌 확인
   lsof -i :3000
   ```

3. **메모리 데이터 손실**
   ```bash
   # 데이터베이스 무결성 검증
   greeum ltm verify
   
   # 백업 복원
   greeum ltm export --format json
   ```

### MCP 연결 문제 해결

#### 문제: Claude Code에서 "연결 실패" 오류

**원인**: Greeum v2.0.0에서 하드코딩된 경로 문제가 있었습니다.

**해결책**:
1. **Greeum v2.0.1 이상으로 업데이트**:
   ```bash
   pipx upgrade greeum
   # 또는
   pipx uninstall greeum && pipx install greeum
   ```

2. **버전 확인**:
   ```bash
   greeum --version
   # 출력: greeum, version 2.0.1 이상이어야 함
   ```

3. **MCP 서버 테스트**:
   ```bash
   # 서버가 정상 시작하는지 확인
   greeum mcp serve --transport stdio
   ```

4. **Claude Code 설정 확인**:
   ```json
   // ~/.claude_desktop_config.json에서 확인
   {
     "mcpServers": {
       "greeum": {
         "command": "greeum",
         "args": ["mcp", "serve", "--transport", "stdio"]
       }
     }
   }
   ```

#### 추가 진단 단계

1. **MCP 서버 직접 테스트**:
   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | greeum mcp serve --transport stdio
   ```

2. **데이터 디렉토리 확인**:
   ```bash
   ls -la ~/.greeum/
   # memory.db 파일이 있어야 함
   ```

3. **권한 문제 해결**:
   ```bash
   # 데이터 디렉토리 권한 확인
   chmod -R 755 ~/.greeum/
   ```

### 디버그 모드 실행
```bash
# 상세한 로그와 함께 실행
GREEUM_LOG_LEVEL=DEBUG greeum memory add "디버그 테스트"
```

## 📚 추가 리소스

### 문서
- [GitHub Repository](https://github.com/DryRainEnt/Greeum)
- [API Reference](./docs/api-reference.md)
- [튜토리얼](./docs/tutorials.md)

### 커뮤니티
- [Issues](https://github.com/DryRainEnt/Greeum/issues)
- [Discussions](https://github.com/DryRainEnt/Greeum/discussions)

## 🆕 v2.0 신기능

### 주요 개선사항
- ✅ **단일 패키지**: Greeum + GreeumMCP 통합
- ✅ **pipx 지원**: 격리된 환경에서 안전한 설치
- ✅ **CLI 확장**: LTM/STM 전용 명령어 추가
- ✅ **MCP 통합**: 9개 도구로 Claude Code 완전 연동
- ✅ **환경 독립성**: 어떤 Python 환경에서도 안정적 동작

### 마이그레이션 가이드
```bash
# v1.x 사용자의 경우
pipx uninstall greeum greeummcp  # 기존 버전 제거
pipx install greeum[all]         # v2.0 설치

# 데이터는 자동으로 마이그레이션됩니다
```

---

**Greeum v2.0 - Universal Memory for LLMs** 🧠✨

완전히 새로워진 Greeum으로 더 스마트한 AI 메모리 관리를 경험하세요!