# Greeum 사용법 가이드 (외부 공유용)

[![PyPI version](https://badge.fury.io/py/greeum.svg)](https://badge.fury.io/py/greeum)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**AI가 기억하는 대화.** 컨텍스트 반복 설명은 이제 그만.

## ⚡ 빠른 시작

```bash
# 설치
pip install greeum

# 첫 메모리 추가
greeum memory add "새 대시보드 프로젝트 시작"

# 메모리 앵커 설정 (빠른 접근용)
greeum anchors set A 123  # 중요한 메모리를 A 슬롯에 고정

# 앵커 기반 국소 검색
greeum memory search "대시보드 프로젝트" --slot A --radius 2
```

끝. 이제 AI가 기억합니다.

## ✨ 주요 기능

🧠 **컨텍스트 기억** - AI가 이전 대화와 결정사항을 기억  
⚡ **280배 빠른 검색** - 체크포인트 기반 메모리 검색  
🔄 **모든 AI와 호환** - GPT, Claude, 커스텀 모델 지원  
🛡️ **데이터는 당신 것** - 로컬 저장, 클라우드 불필요  

## 🔧 설치 및 설정

### 기본 설치
```bash
pip install greeum
```

### 모든 기능 포함 설치
```bash
pip install greeum[all]  # 벡터 검색, 임베딩 포함
```

### Claude Code 사용자용
```bash
# Greeum 설치 후 MCP 서버 시작
pip install greeum
greeum mcp serve

# Claude Desktop 설정 (~/.config/claude-desktop/claude_desktop_config.json)
{
  "mcpServers": {
    "greeum": {
      "command": "greeum",
      "args": ["mcp", "serve"]
    }
  }
}
```

## 📖 기본 사용법

### 1. 메모리 추가
```bash
# 기본 메모리 추가
greeum memory add "오늘 React 훅 최적화 작업 완료"

# 중요도 설정 (0.0-1.0)
greeum memory add "핵심 API 설계 완료" --importance 0.9

# 태그와 함께 추가
greeum memory add "버그 수정: 로그인 이슈" --tags bug,login
```

### 2. 메모리 검색
```bash
# 기본 검색
greeum memory search "React 훅"

# 결과 개수 지정
greeum memory search "API" --count 10

# 최근 메모리 조회
greeum recent-memories --count 5
```

### 3. 메모리 앵커 활용
```bash
# 앵커 상태 확인
greeum anchors status

# 앵커 설정 (A, B, C 슬롯 사용)
greeum anchors set A 145    # 블록 #145를 A 슬롯에 설정
greeum anchors set B 167    # 블록 #167을 B 슬롯에 설정

# 앵커 고정/해제
greeum anchors pin A        # A 슬롯 고정 (자동 이동 방지)
greeum anchors unpin A      # A 슬롯 고정 해제

# 앵커 기반 국소 검색
greeum memory search "프로젝트" --slot A --radius 2
```

### 4. 고급 검색 옵션
```bash
# 연관관계 확장 검색 (깊이 지정)
greeum memory search "데이터베이스" --depth 2 --tolerance 0.7

# 특정 앵커 주변 검색
greeum memory search "버그" --slot B --radius 3

# 검색 결과 상세 정보 포함
greeum memory search "성능" --verbose
```

## 🎯 Claude Code MCP 통합

Greeum은 Claude Code와 완벽하게 통합되어 대화 중 자동으로 메모리를 활용할 수 있습니다.

### 사용 가능한 MCP 도구들:
- `add_memory` - 새 메모리 추가
- `search_memory` - 메모리 검색  
- `get_memory_stats` - 메모리 통계 확인
- `usage_analytics` - 사용 분석 리포트

### Claude Code에서 사용 예시:
```
사용자: "지난주에 논의했던 API 최적화 방안이 뭐였지?"

Claude: 지난주 API 최적화 논의 내용을 찾아보겠습니다.
[자동으로 search_memory 실행]

관련 메모리를 찾았습니다:
1. [2024-01-15] API 캐싱 전략 논의 - Redis 도입 결정
2. [2024-01-16] DB 쿼리 최적화 - N+1 문제 해결방안
3. [2024-01-17] CDN 적용 계획 - 정적 리소스 캐싱

이 중에서 어떤 부분에 대해 더 자세히 알고 싶으신가요?
```

## 📊 메모리 관리

### 통계 확인
```bash
# 전체 메모리 통계
greeum memory stats

# 사용 분석 리포트 (최근 7일)
greeum analytics --days 7

# 데이터베이스 정보
greeum memory info
```

### 메모리 내보내기/가져오기
```bash
# JSON 형태로 내보내기
greeum export --format json --output my_memories.json

# 특정 기간 내보내기
greeum export --since "2024-01-01" --until "2024-01-31"

# 메모리 가져오기
greeum import my_memories.json
```

## 🔍 고급 활용법

### 1. 프로젝트별 메모리 관리
```bash
# 환경변수로 데이터 디렉토리 지정
export GREEUM_DATA_DIR="/project/memories"
greeum memory add "프로젝트 A 시작"

# 다른 프로젝트 전환
export GREEUM_DATA_DIR="/other/project/memories" 
greeum memory add "프로젝트 B 관련 메모"
```

### 2. API를 통한 프로그래밍 방식 사용
```python
from greeum import BlockManager, DatabaseManager

# 초기화
db_manager = DatabaseManager()
block_manager = BlockManager(db_manager)

# 메모리 추가
block_index = block_manager.add_block(
    context="새로운 기능 구현 완료",
    importance=0.8
)

# 메모리 검색
results = block_manager.search_blocks("기능 구현", limit=5)
```

### 3. 배치 스크립트 활용
```bash
#!/bin/bash
# 일일 메모리 백업 스크립트

DATE=$(date +%Y%m%d)
greeum export --output "backup_${DATE}.json"
echo "메모리 백업 완료: backup_${DATE}.json"
```

## ⚙️ 설정 옵션

### 환경 변수
- `GREEUM_DATA_DIR`: 데이터 저장 디렉토리 경로
- `GREEUM_LOG_LEVEL`: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
- `GREEUM_MAX_BLOCKS`: 최대 블록 수 제한

### 설정 파일 (greeum.conf)
```ini
[memory]
default_importance = 0.5
auto_cleanup_days = 365
max_search_results = 20

[performance]
cache_size = 1000
enable_compression = true
```

## 🎯 모범 사례

### 1. 효과적인 메모리 작성법
```bash
# 좋은 예: 구체적이고 맥락이 있는 메모리
greeum memory add "React useEffect 의존성 배열에서 함수 참조 문제 해결 - useCallback 사용"

# 피해야 할 예: 너무 간단하거나 애매한 메모리  
greeum memory add "버그 고침"
```

### 2. 앵커 전략
- **A 슬롯**: 현재 주요 작업/프로젝트
- **B 슬롯**: 참고 자료나 문서
- **C 슬롯**: 반복되는 이슈나 해결책

### 3. 검색 전략
- 키워드가 정확할 때: 기본 검색
- 관련 내용을 폭넓게 찾을 때: `--depth 2` 사용
- 특정 맥락 내에서 찾을 때: `--slot` 옵션 사용

## 🔧 문제 해결

### 자주 발생하는 문제들

**Q: "No memories found" 메시지가 계속 나타남**
```bash
# 데이터베이스 상태 확인
greeum memory stats

# 메모리 다시 초기화
greeum init
```

**Q: MCP 연결이 되지 않음**
```bash
# MCP 서버 상태 확인
greeum mcp serve --verbose

# Claude Desktop 설정 확인
cat ~/.config/claude-desktop/claude_desktop_config.json
```

**Q: 검색 성능이 느림**
```bash
# 캐시 최적화
greeum optimize

# 오래된 메모리 정리
greeum cleanup --days 180
```

## 📚 더 많은 정보

- **GitHub**: [https://github.com/your-org/greeum](https://github.com/your-org/greeum)
- **문서**: [https://greeum.readthedocs.io](https://greeum.readthedocs.io)  
- **이슈 리포트**: [https://github.com/your-org/greeum/issues](https://github.com/your-org/greeum/issues)

---

**Greeum**: AI conversations that remember everything. 🧠✨