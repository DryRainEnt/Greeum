# WSL에서 Native MCP Server 직접 테스트 가이드

## 🚀 **배포 없이 WSL 테스트하는 방법**

### **방법 1: 직접 경로 사용** ⭐ **추천**

**Windows Claude Desktop 설정**:
```json
{
  "mcpServers": {
    "greeum_wsl_direct": {
      "command": "wsl",
      "args": [
        "python3",
        "/mnt/c/Users/username/path/to/Greeum/greeum/mcp/native_mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/mnt/c/Users/username/path/to/Greeum",
        "GREEUM_DATA_DIR": "/home/username/greeum-data"
      }
    }
  }
}
```

### **방법 2: WSL 내부에 복사**

```bash
# 1. WSL 내부로 프로젝트 복사
cp -r /mnt/c/path/to/Greeum /home/username/

# 2. Claude Desktop 설정
{
  "mcpServers": {
    "greeum_wsl": {
      "command": "wsl",
      "args": [
        "python3",
        "/home/username/Greeum/greeum/mcp/native_mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/home/username/Greeum",
        "GREEUM_DATA_DIR": "/home/username/greeum-data"
      }
    }
  }
}
```

### **방법 3: WSL에서 직접 테스트**

```bash
# WSL 터미널에서 직접 실행
cd /path/to/Greeum
PYTHONPATH="/path/to/Greeum" python3 greeum/mcp/native_mcp_server.py

# JSON-RPC 테스트
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | PYTHONPATH="/path/to/Greeum" python3 greeum/mcp/native_mcp_server.py
```

## 🔍 **핵심 확인 사항**

### **1. WSL에서 Native MCP Server 직접 테스트**
```bash
# 기본 동작 확인
python3 -c "
import sys
sys.path.insert(0, '/path/to/Greeum')
from greeum.mcp.native_mcp_server import NativeMCPServer
server = NativeMCPServer()
print('✅ Native MCP Server 초기화 성공')
"
```

### **2. asyncio 충돌 여부 확인**
```bash
# FastMCP vs Native MCP 비교 테스트
echo "Testing Native MCP (no asyncio)..."
timeout 5 python3 greeum/mcp/native_mcp_server.py < /dev/null
echo "Exit code: $?"
```

### **3. Claude Desktop 연동 테스트**
1. **설정 적용**: claude_desktop_config.json 수정
2. **Claude Desktop 재시작**
3. **연결 확인**: `claude mcp list`
4. **도구 사용**: add_memory, search_memory 테스트

## ✅ **예상 성공 결과**

**WSL에서 성공하면:**
- ✅ `claude mcp list`에서 "greeum_wsl_direct ✓ Connected" 표시
- ✅ Claude Code에서 4개 MCP 도구 사용 가능
- ✅ asyncio 충돌 없이 안정적 연동

**주요 장점:**
- 🔥 **배포 불필요** - 개발 버전 직접 사용
- 🔥 **빠른 테스트** - 즉시 확인 가능
- 🔥 **실제 WSL 환경** - 정확한 호환성 검증

## 🚨 **만약 WSL에서도 문제가 있다면**

**가능한 원인들:**
1. **경로 문제**: Windows-WSL 경로 매핑 이슈
2. **권한 문제**: WSL 파일 권한 설정
3. **환경변수**: PYTHONPATH 설정 문제
4. **의존성**: WSL 내부 Python 패키지 부족

**디버깅 방법:**
```bash
# 1. 경로 확인
ls -la /mnt/c/path/to/Greeum/greeum/mcp/native_mcp_server.py

# 2. Python 경로 확인  
python3 -c "import sys; print('\n'.join(sys.path))"

# 3. 모듈 임포트 테스트
python3 -c "
import sys
sys.path.insert(0, '/path/to/Greeum')
from greeum.mcp.adapters.base_adapter import BaseAdapter
print('✅ Import success')
"
```

---

**이 방법으로 배포 없이도 WSL 환경에서 Native MCP Server를 직접 테스트할 수 있습니다!**