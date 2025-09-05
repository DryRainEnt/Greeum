# Greeum 메모리 시스템 사용 지침

## 🧠 Greeum이란?

Greeum은 Claude Code와 완벽 통합된 **AI용 외부 기억 시스템**입니다. 대화 내용, 코드 분석 결과, 프로젝트 진행사항을 영구 저장하여 컨텍스트 제한 없이 지속적인 작업이 가능합니다.

## 🚀 빠른 설정

### 1. Greeum 설치 및 MCP 연결
```bash
# Greeum 설치
pip install greeum

# Claude Desktop 설정 파일에 추가
# (~/.config/claude-desktop/claude_desktop_config.json)
{
  "mcpServers": {
    "greeum": {
      "command": "greeum", 
      "args": ["mcp", "serve"]
    }
  }
}
```

### 2. 사용 가능한 도구들
- `add_memory` - 중요한 내용 영구 저장
- `search_memory` - 과거 기억 검색
- `get_memory_stats` - 메모리 현황 확인
- `usage_analytics` - 사용 분석 리포트

## 📖 기본 사용 패턴

### 대화 시작 시 - 맥락 파악
```
먼저 관련된 이전 작업이나 논의사항이 있는지 확인해보겠습니다.
```
→ `search_memory("현재 프로젝트명")` 자동 실행

### 중요한 결과나 결정사항 저장
```
이 분석 결과를 기억해두겠습니다.
```
→ `add_memory("구체적인 내용과 맥락", importance=0.8)` 실행

### 이전 논의 내용 찾기
```
지난번에 논의했던 API 설계 방안을 찾아보겠습니다.
```
→ `search_memory("API 설계", limit=5)` 실행

## 🎯 효과적인 메모리 사용법

### 1. 그레마스 액탄트 모델로 저장
```python
# 좋은 메모리 저장 예시
add_memory("[사용자-요청-성능최적화] React 컴포넌트 렌더링 최적화 방안 요청, 현재 초기 로딩 3초 → 1초 미만 목표")

add_memory("[Claude-발견-메모리릭] useEffect 정리 함수 누락으로 인한 메모리 누수 발견, cleanup 함수 추가 필요")

add_memory("[팀-결정-아키텍처] 마이크로서비스에서 모놀리스로 전환 결정, 복잡성 감소와 배포 단순화 목적")
```

### 2. 적절한 중요도 설정
```python
# 중요도 가이드라인
importance=0.9  # 핵심 아키텍처 결정, 중요한 버그 수정
importance=0.7  # 주요 기능 구현, 성능 개선
importance=0.5  # 일반적인 작업, 코드 리뷰 결과  
importance=0.3  # 단순 정보, 임시 메모
```

### 3. 검색 전략
```python
# 기본 검색 (최근 관련 내용)
search_memory("React 최적화", limit=5)

# 심화 검색 (연관 내용까지)  
search_memory("성능 개선", limit=10, depth=2, tolerance=0.7)

# 특정 기간 검색
search_memory("API 설계 2024-01월")
```

## 🔄 워크플로우 통합

### 1. 프로젝트 시작 시
```markdown
## 프로젝트 초기 설정
1. 이전 유사 프로젝트 경험 검색
2. 주요 기술스택과 아키텍처 결정사항 저장
3. 팀 논의 결과와 요구사항 기록
```

### 2. 개발 과정 중
```markdown
## 개발 진행 중 기록
- 발견한 문제점과 해결방법
- 성능 측정 결과와 개선사항
- 코드 리뷰 피드백과 적용사항
- 라이브러리 선택 이유와 평가
```

### 3. 프로젝트 완료 후  
```markdown
## 마무리 단계 기록
- 최종 성과와 달성 지표
- 마주친 어려움과 극복 과정
- 다음 프로젝트를 위한 교훈
- 재사용 가능한 코드나 패턴
```

## ⚡ 고급 활용 팁

### 1. 컨텍스트 체인 구축
```python
# 연관된 메모리들을 체인으로 연결
add_memory("[Claude-연결-후속작업] 인증 시스템 구현 완료, 다음 단계로 권한 관리 시스템 필요")
```

### 2. 패턴 학습 활용
```python
# 반복되는 이슈나 해결책 패턴 기록
add_memory("[패턴-인식-CORS이슈] Express.js + React 조합에서 CORS 에러 빈발, cors 미들웨어 설정 필수")
```

### 3. 성능 추적
```python
# 성능 관련 메트릭과 개선사항 추적
add_memory("[성능-측정-응답시간] API 응답시간 평균 200ms → 80ms로 개선, 인덱스 최적화 효과")
```

## 🛠️ 문제 해결

### 자주 하는 실수들

**❌ 너무 간단한 메모리**
```python
add_memory("버그 수정")  # 구체성 부족
```

**✅ 구체적이고 맥락있는 메모리**
```python
add_memory("[Claude-수정-로그인버그] JWT 토큰 만료 시간 검증 로직 오류 수정, 1시간 → 24시간으로 조정")
```

**❌ 중요도 미설정**
```python
add_memory("새 기능 추가")  # 기본 중요도만 사용
```

**✅ 적절한 중요도 설정**
```python
add_memory("사용자 인증 시스템 완성", importance=0.8)  # 중요도 명시
```

### 검색이 잘 안될 때
```python
# 1. 키워드를 다양하게 시도
search_memory("인증")  
search_memory("로그인")
search_memory("JWT")

# 2. 연관 검색으로 범위 확장  
search_memory("보안", depth=2)

# 3. 최근 메모리 전체 확인
get_memory_stats()
```

## 🎯 모범 사례

### 1. 세션 시작 시 루틴
```
1. search_memory로 관련 맥락 파악
2. 이전 작업의 연속성 확인  
3. 새로운 발견사항 즉시 기록
```

### 2. 코드 분석 시 패턴
```  
1. 분석 대상과 목적 기록
2. 발견한 문제점들 상세 저장
3. 제안한 해결방안과 근거 기록
4. 구현 결과와 검증 내용 저장
```

### 3. 에러 해결 시 패턴
```
1. 에러 상황과 재현 조건 기록
2. 시도한 해결 방법들 나열  
3. 최종 해결책과 근본 원인 설명
4. 향후 예방을 위한 체크포인트 설정
```

## 📊 메모리 관리

### 정기적인 관리 작업
```python
# 월 1회 정도 실행 권장
get_memory_stats()           # 전체 현황 파악
usage_analytics(days=30)     # 한 달 사용 패턴 분석  
```

### 데이터 백업 (옵션)
```bash  
# 터미널에서 백업 (선택사항)
greeum export --output backup_$(date +%Y%m%d).json
```

---

**이 지침을 CLAUDE.md에 추가하면 Greeum을 활용한 지속적이고 체계적인 AI 협업이 가능합니다.** 🧠✨

## 🔗 추가 리소스
- Greeum 공식 가이드: `GREEUM_USAGE_GUIDE_EXTERNAL.md` 참조
- 고급 메모리 전략: `GREEUM_MEMORY_USAGE_GUIDELINES.md` 참조