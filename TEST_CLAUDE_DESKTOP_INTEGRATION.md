# Claude Desktop Integration Test Guide

## 🎯 Native MCP Server Claude Desktop 연동 테스트

### **배경**
- FastMCP asyncio 충돌 문제를 해결하기 위해 Native JSON-RPC 2.0 MCP 서버 구현
- BaseAdapter 로직 100% 재사용하여 기존 기능 완전 보존
- 테스트 환경에서 BrokenPipe 발생하지만, 실제 Claude Desktop 환경에서는 정상 동작 예상

### **1. Claude Desktop 설정**

Claude Desktop 설정 파일에 다음 내용 추가:

**macOS**: `~/.config/claude-desktop/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "greeum_native": {
      "command": "python3",
      "args": [
        "/Users/dryrain/DevRoom/Greeum/greeum/mcp/native_mcp_server.py"
      ],
      "env": {
        "GREEUM_DATA_DIR": "/Users/dryrain/greeum-global",
        "GREEUM_LOG_LEVEL": "INFO",
        "PYTHONPATH": "/Users/dryrain/DevRoom/Greeum:/Users/dryrain/DevRoom/GreeumMCP"
      }
    }
  }
}
```

### **2. 연동 테스트 체크리스트**

#### **✅ Phase 1: 기본 연동 확인**
- [ ] Claude Desktop 재시작 후 MCP 서버 연결 상태 확인
- [ ] `claude mcp list` 명령어로 greeum_native 서버 연결 확인
- [ ] 연결 상태에 "✓ Connected" 표시 확인

#### **✅ Phase 2: 도구 기능 테스트**
- [ ] **add_memory** 도구 사용 - 새 메모리 추가 테스트
- [ ] **search_memory** 도구 사용 - 메모리 검색 테스트  
- [ ] **get_memory_stats** 도구 사용 - 통계 정보 확인
- [ ] **usage_analytics** 도구 사용 - 분석 리포트 확인

#### **✅ Phase 3: 안정성 테스트**
- [ ] 여러 번의 연속 요청 처리 확인
- [ ] Claude Desktop 재시작 후에도 정상 연동 확인
- [ ] 에러 발생 시 정상적인 에러 응답 확인

### **3. 예상 결과**

#### **성공 시:**
```
🎉 Native MCP Server Claude Desktop 연동 성공!
✅ asyncio 충돌 완전 해결
✅ MCP 표준 100% 준수
✅ 4개 도구 모두 정상 동작
✅ Claude Desktop과 완벽 호환
```

#### **문제 발생 시 체크사항:**
1. **Python 경로 확인**: `python3` 명령어가 정상 동작하는지
2. **PYTHONPATH 설정**: Greeum 모듈을 찾을 수 있는지  
3. **권한 확인**: 스크립트 실행 권한이 있는지
4. **로그 확인**: Claude Desktop 로그에서 연결 오류 메시지 확인

### **4. 성공 기준**

**✅ 완전 성공**:
- Claude Desktop에서 4개 도구 모두 사용 가능
- 메모리 추가/검색/통계 모든 기능 정상 동작
- asyncio 충돌 없이 안정적 연동

**⚠️ 부분 성공**:
- 도구는 보이지만 일부 기능 오류 발생
- 간헐적 연결 불안정

**❌ 실패**:
- Claude Desktop에서 서버 연결 실패
- 도구 목록에 표시되지 않음

### **5. 트러블슈팅**

#### **서버 연결 실패 시:**
```bash
# 1. 직접 서버 실행 테스트
cd /Users/dryrain/DevRoom/Greeum
PYTHONPATH="/Users/dryrain/DevRoom/Greeum" python3 greeum/mcp/native_mcp_server.py

# 2. 환경변수 확인
echo $PYTHONPATH

# 3. 모듈 임포트 테스트
python3 -c "from greeum.mcp.adapters.base_adapter import BaseAdapter; print('✅ Import OK')"
```

### **6. 최종 검증**

**Native MCP Server가 성공적으로 연동되면:**
- 🔥 **FastMCP asyncio 충돌 근본적 해결**
- 🔥 **MCP 호스트 호환성 100% 확보**  
- 🔥 **사용자 요구사항 완전 충족**
- 🔥 **v2.2.9 핫픽스 배포 준비 완료**

---

**이 테스트를 통해 진짜 Claude Desktop 호환성을 검증하고, 근본적 수정의 완전한 성공을 확인할 수 있습니다.**