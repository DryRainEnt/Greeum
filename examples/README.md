# MemoryEngine MCP (Model Control Protocol) 예제

이 디렉토리에는 Cursor 환경에서 MCP를 사용하는 예제가 포함되어 있습니다. MemoryEngine과 MCP를 연동하여 AI 기억 시스템을 다양한 도구와 연결할 수 있습니다.

## MCP란?

MCP(Model Control Protocol)는 AI 모델과 외부 도구(Unity, Discord 등) 간의 통신을 위한 프로토콜입니다. Cursor 환경에서 이 프로토콜을 사용하면 MemoryEngine의 기억 시스템을 다양한 외부 도구와 연동할 수 있습니다.

## 시작하기

### 1. 필요한 패키지 설치

프로젝트 루트 디렉토리에서 필요한 패키지를 설치합니다:

```bash
pip install -r requirements.txt
```

### 2. MCP 서비스 실행

MCP 서비스를 실행하려면 다음 명령을 사용합니다:

```bash
python examples/mcp_example.py --mode server
```

서비스는 기본적으로 http://localhost:8000에서 실행됩니다. 다른 포트를 사용하려면 `--port` 옵션을 추가하세요.

### 3. MCP 클라이언트 테스트

서비스가 실행 중인 상태에서 클라이언트 테스트를 실행합니다:

```bash
python examples/mcp_example.py --mode client
```

처음 실행 시 API 키가 자동으로 생성됩니다. 이후 실행 시에는 생성된 API 키를 사용할 수 있습니다:

```bash
python examples/mcp_example.py --mode client --api-key YOUR_API_KEY
```

## MCP 인터페이스 사용하기

### MemoryEngine과 MCP 연동

`memory_engine/mcp_client.py` 모듈을 사용하여 MCP 클라이언트를 생성하고 MemoryEngine과 연동할 수 있습니다:

```python
from memory_engine.mcp_client import MCPClient

client = MCPClient(api_key="YOUR_API_KEY")

# 기억 추가
result = client.manage_memory(
    action="add",
    memory_content="이것은 MCP를 통해 추가된 새로운 기억입니다."
)

# 기억 검색
search_result = client.manage_memory(
    action="query",
    query="MCP 검색어",
    limit=5
)
```

### Unity와 연동하기

MCP를 통해 Unity와 연동할 수 있습니다:

```python
from memory_engine.mcp_client import MCPClient

client = MCPClient(api_key="YOUR_API_KEY")

# Unity 메뉴 아이템 실행
result = client.execute_menu_item(menu_path="GameObject/Create Empty")

# 게임 오브젝트 선택
result = client.select_gameobject(object_path="Main Camera")

# 콘솔 로그 메시지 전송
result = client.send_console_log(
    message="MCP에서 전송된 로그 메시지", 
    log_type="info"
)
```

### Discord와 연동하기

MCP를 통해 Discord와 연동할 수 있습니다:

```python
from memory_engine.mcp_integrations import MCPIntegrations

integrations = MCPIntegrations()

# Discord 이벤트를 기억으로 저장
memory_id = integrations.store_discord_event(
    event_type="message_sent",
    event_data={
        "channelId": "channel_id",
        "message": "Discord 메시지 내용"
    }
)

# Discord 관련 기억 검색
results = integrations.get_related_discord_memories(
    query="검색어", 
    limit=5
)
```

## 제공되는 기능

- **기억 관리**: 기억 추가, 검색, 업데이트, 삭제
- **Unity 통합**: 메뉴 실행, 게임오브젝트 선택, 컴포넌트 업데이트 등
- **Discord 통합**: 메시지 전송, 반응 추가, 포럼 게시물 생성 등

## 설정 파일

MCP 통합 설정은 `data/mcp_config.json` 파일에 저장됩니다. 이 파일은 자동으로 생성되며 필요에 따라 수정할 수 있습니다:

```json
{
  "unity": {
    "enabled": false,
    "base_url": "http://localhost:8000/api/mcp/unity",
    "api_key": ""
  },
  "discord": {
    "enabled": false,
    "token": "",
    "guild_id": ""
  },
  "memory_tags": {
    "unity": ["unity", "gamedev", "game", "3d"],
    "discord": ["discord", "chat", "message", "communication"]
  }
}
``` 