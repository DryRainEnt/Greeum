# Greeum Native MCP Server 설계서 v2.3.0a2

## 🎯 설계 목표

### 근본적 문제 해결
- **FastMCP AsyncIO 충돌 완전 해결**: `asyncio.run()` 중첩 호출 문제 근본 차단
- **모든 환경 호환성**: Windows, macOS, Linux, WSL, PowerShell 완전 지원
- **완전한 통제권**: 외부 프레임워크 의존성 없는 순수 네이티브 구현

### 검증된 공식 패턴 적용
- **Anthropic MCP Python SDK 공식 패턴 준수**
- **anyio + Pydantic 기반 안전한 AsyncIO 처리**
- **JSON-RPC 2.0 프로토콜 완전 준수**

## 🏗️ 아키텍처 설계

### 전체 구조
```
greeum/mcp/native/
├── __init__.py              # 패키지 초기화
├── server.py                # 메인 서버 클래스
├── transport.py             # STDIO 전송 계층
├── protocol.py              # JSON-RPC 메시지 처리
├── tools.py                 # MCP 도구 정의
└── types.py                 # Pydantic 타입 정의
```

### 레이어 분리
```
Application Layer    │ tools.py (Greeum 도구들)
Protocol Layer       │ protocol.py (JSON-RPC 2.0)  
Transport Layer      │ transport.py (STDIO)
Infrastructure Layer │ server.py (AsyncIO 관리)
```

## 🔧 기술 스택

### 핵심 의존성
```python
# ✅ 검증된 의존성만 사용
"anyio>=4.5"           # 크로스플랫폼 AsyncIO (FastMCP 대신)
"pydantic>=2.0.0"      # JSON 검증/직렬화
# mcp 의존성 완전 제거!
```

### AsyncIO 처리 패턴
```python
# ✅ 공식 패턴: anyio.create_task_group 사용
async with anyio.create_task_group() as tg:
    tg.start_soon(stdin_reader)
    tg.start_soon(stdout_writer) 
    tg.start_soon(message_processor)
```

## 📋 상세 설계

### 1. 서버 클래스 (server.py)
```python
class GreeumNativeMCPServer:
    """
    Greeum Native MCP Server
    - FastMCP 없는 순수 네이티브 구현
    - anyio 기반 안전한 AsyncIO 처리
    - 완전한 Windows 호환성
    """
    
    def __init__(self):
        self.greeum_components = None
        self.tools_registry = {}
        self.initialized = False
        
    async def initialize(self) -> None:
        """Greeum 컴포넌트 초기화"""
        
    async def run_stdio(self) -> None:
        """STDIO transport로 서버 실행"""
        
    async def shutdown(self) -> None:
        """서버 종료 처리"""
```

### 2. STDIO 전송 계층 (transport.py) 
```python
class STDIOTransport:
    """
    공식 패턴 기반 STDIO 처리
    - UTF-8 인코딩으로 Windows 호환성 보장  
    - anyio.wrap_file로 안전한 스트림 처리
    - Memory Object Streams로 읽기/쓰기 분리
    """
    
    @staticmethod
    async def create_stdio_streams():
        """Windows 호환 STDIO 스트림 생성"""
        from io import TextIOWrapper
        
        # ✅ 공식 패턴: Windows 인코딩 문제 해결
        stdin = anyio.wrap_file(
            TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
        )
        stdout = anyio.wrap_file(
            TextIOWrapper(sys.stdout.buffer, encoding="utf-8") 
        )
        
        return stdin, stdout
    
    async def run_transport(self, message_handler):
        """전송 계층 메인 루프"""
```

### 3. JSON-RPC 프로토콜 (protocol.py)
```python
class JSONRPCProcessor:
    """
    JSON-RPC 2.0 메시지 처리
    - Pydantic 기반 안전한 파싱/검증
    - MCP 프로토콜 스펙 완전 준수
    - 에러 처리 및 응답 생성
    """
    
    async def process_message(self, raw_message: str) -> Optional[dict]:
        """JSON-RPC 메시지 처리"""
        
    def create_response(self, id: Any, result: Any) -> dict:
        """성공 응답 생성"""
        
    def create_error(self, id: Any, code: int, message: str) -> dict:
        """에러 응답 생성"""
```

### 4. Pydantic 타입 정의 (types.py)
```python
# ✅ 공식 JSON-RPC 메시지 타입들
class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int, None]
    method: str
    params: Optional[Dict[str, Any]] = None

class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0" 
    id: Union[str, int, None]
    result: Optional[Any] = None

class JSONRPCError(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int, None]  
    error: Dict[str, Any]

# MCP 프로토콜 특화 타입들
class MCPInitializeRequest(BaseModel):
    protocolVersion: str
    capabilities: Dict[str, Any]
    clientInfo: Dict[str, str]
```

### 5. MCP 도구 구현 (tools.py)
```python
class GreeumMCPTools:
    """
    Greeum MCP 도구들
    - 기존 비즈니스 로직 100% 재사용
    - MCP 프로토콜 응답 형식 준수
    - 기존 API와 완전한 호환성
    """
    
    def __init__(self, greeum_components):
        self.components = greeum_components
        
    async def handle_add_memory(self, params: dict) -> dict:
        """add_memory 도구 처리"""
        
    async def handle_search_memory(self, params: dict) -> dict:
        """search_memory 도구 처리"""
        
    async def handle_get_memory_stats(self, params: dict) -> dict:
        """get_memory_stats 도구 처리"""
        
    async def handle_usage_analytics(self, params: dict) -> dict:
        """usage_analytics 도구 처리"""
```

## 🔄 메시지 플로우

### 1. 초기화 시퀀스
```
1. Claude Desktop → initialize 요청
2. Server → Greeum 컴포넌트 초기화  
3. Server → capabilities 응답
4. Claude Desktop → initialized 통지
```

### 2. 도구 목록 요청
```
1. Claude Desktop → tools/list 요청
2. Server → 4개 도구 (add_memory, search_memory, get_memory_stats, usage_analytics) 응답
```

### 3. 도구 호출
```
1. Claude Desktop → tools/call 요청 (add_memory)
2. Server → Greeum 비즈니스 로직 실행
3. Server → MCP 형식 결과 응답
```

## 🛡️ 안전성 보장

### AsyncIO 충돌 방지
```python
# ✅ anyio 사용으로 asyncio.run() 충돌 완전 회피
# ❌ asyncio.run() 절대 사용 금지
# ✅ anyio.create_task_group()만 사용
```

### Windows 호환성
```python
# ✅ TextIOWrapper + UTF-8로 인코딩 문제 해결
# ✅ anyio.wrap_file로 크로스플랫폼 지원
```

### STDOUT 오염 방지
```python
# ✅ 모든 로그는 stderr 전용
# ✅ STDOUT은 JSON-RPC 메시지만
# ✅ 디버그 출력 완전 차단
```

## 📊 성능 최적화

### 메모리 효율성
- **Memory Object Streams**: 읽기/쓰기 버퍼 분리로 메모리 효율화
- **Lazy Loading**: Greeum 컴포넌트 필요시에만 초기화
- **Pydantic 최적화**: model_dump_json()으로 직렬화 성능 향상

### 처리 속도
- **비동기 스트림**: anyio 기반 논블로킹 I/O
- **병렬 처리**: Task Group으로 동시 메시지 처리
- **캐시 활용**: 기존 Greeum 캐시 시스템 완전 활용

## 🧪 테스트 전략

### 단위 테스트
```python
# 각 레이어별 독립 테스트
test_stdio_transport()      # 전송 계층
test_jsonrpc_processor()    # 프로토콜 계층  
test_greeum_tools()         # 도구 계층
test_server_lifecycle()     # 서버 라이프사이클
```

### 통합 테스트
```python
# 전체 플로우 테스트
test_claude_desktop_integration()  # Claude Desktop 연동
test_windows_compatibility()       # Windows 환경
test_asyncio_safety()             # AsyncIO 안전성
```

### 호환성 테스트
```python
# 다양한 환경 테스트
test_macos_terminal()      # macOS Terminal
test_windows_powershell()  # Windows PowerShell  
test_wsl_environment()     # WSL 환경
test_linux_bash()          # Linux Bash
```

## 🚀 배포 계획

### 버전 로드맵
- **v2.3.0a2**: Native MCP Server 구현 완료 (현재 목표)
- **v2.3.0b1**: 모든 환경 호환성 테스트 통과
- **v2.3.0**: 안정 버전 배포

### 의존성 변경
```toml
# Before
dependencies = [
    "mcp>=1.0.0",  # ❌ 제거
    # ...
]

# After  
dependencies = [
    "anyio>=4.5",  # ✅ 추가
    # mcp 의존성 완전 제거!
    # ...
]
```

### 하위 호환성
- **기존 API 100% 호환**: CLI 명령어 변경 없음
- **기존 사용자 투명성**: 내부 구현 변경만
- **설정 파일 호환**: 기존 Claude Desktop 설정 유지

## 💡 기대 효과

### 안정성 향상
- ✅ **AsyncIO 충돌 완전 해결**: "Already running asyncio" 에러 근절
- ✅ **모든 환경 호환**: Windows, macOS, Linux, WSL 완전 지원
- ✅ **의존성 최소화**: 외부 프레임워크 의존성 제거

### 유지보수성 향상
- ✅ **완전한 통제권**: 모든 코드를 직접 제어
- ✅ **디버깅 용이성**: 스택 추적 명확화
- ✅ **확장성 보장**: 향후 기능 추가 유연성

### 사용자 경험 개선
- ✅ **무중단 연동**: 모든 환경에서 즉시 작동
- ✅ **에러 해결**: 설치-연동-사용 과정에서 막히는 경험 근절
- ✅ **성능 최적화**: 중간 레이어 제거로 성능 향상

---

## 📋 구현 체크리스트

### Phase 1: 기반 구조
- [ ] types.py - Pydantic 타입 정의
- [ ] transport.py - STDIO 전송 계층
- [ ] protocol.py - JSON-RPC 처리

### Phase 2: 핵심 로직  
- [ ] server.py - 메인 서버 클래스
- [ ] tools.py - Greeum MCP 도구
- [ ] CLI 연동 - 기존 CLI와 통합

### Phase 3: 테스트 & 검증
- [ ] 단위 테스트 작성
- [ ] Windows 환경 테스트
- [ ] Claude Desktop 연동 테스트
- [ ] 성능 벤치마크

### Phase 4: 배포
- [ ] 버전 2.3.0a2 Native MCP 구현 완료
- [ ] PyPI 배포
- [ ] 사용자 테스트 피드백

---

**이 설계서는 2.2.6-2.2.8의 "치명적인 시행착오" 경험을 바탕으로, Anthropic 공식 패턴을 준수하여 2.3.0a2에서 근본적이고 안전한 해결책을 제시합니다.**