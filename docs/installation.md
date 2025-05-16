# Greeum 설치 및 시작하기

Greeum은 LLM 독립적인 기억 관리 시스템으로, 다양한 언어 모델과 통합하여 사용할 수 있습니다. 이 문서에서는 Greeum을 설치하고 기본 설정하는 방법을 설명합니다.

## 필수 요구사항

- Python 3.8 이상
- pip (Python 패키지 관리자)
- Git (선택사항, 저장소 복제용)

## 설치 방법

### 1. PyPI에서 직접 설치 (권장)

```bash
# 기본 설치
pip install greeum

# MCP(Model Control Protocol) 기능 포함 설치
pip install greeum[mcp]

# 모든 기능 포함 설치
pip install greeum[all]
```

### 2. 저장소에서 설치

```bash
git clone https://github.com/DryRainEnt/Greeum.git
cd Greeum

# 기본 설치
pip install -r requirements.txt

# 개발 모드로 설치
pip install -e .

# MCP 기능 포함 개발 모드 설치
pip install -e ".[mcp]"
```

### 3. 가상 환경 설정 (선택사항이지만 권장)

```bash
# 가상 환경 생성
python -m venv venv

# 가상 환경 활성화 (Windows)
venv\Scripts\activate

# 가상 환경 활성화 (macOS/Linux)
source venv/bin/activate
```

## 기본 구성

Greeum은 기본적으로 설정 없이도 바로 사용할 수 있지만, 몇 가지 설정을 통해 사용자 환경에 맞게 최적화할 수 있습니다.

### 기본 설정 파일 생성

프로젝트 루트 디렉토리에 `config.json` 파일을 생성하여 다음과 같이 설정할 수 있습니다:

```json
{
  "storage": {
    "path": "./data/memory",
    "format": "json"
  },
  "ttl": {
    "short": 3600,    // 1시간 (초 단위)
    "medium": 86400,  // 1일 (초 단위)
    "long": 2592000   // 30일 (초 단위)
  },
  "embedding": {
    "model": "default",
    "dimension": 384
  },
  "language": {
    "default": "auto",
    "supported": ["ko", "en", "ja", "zh", "es"]
  },
  "mcp": {
    "enabled": true,
    "port": 8000,
    "host": "0.0.0.0"
  }
}
```

### 스토리지 디렉토리 준비

메모리 블록이 저장될 디렉토리를 생성합니다:

```bash
mkdir -p data/memory
```

## MCP(Model Control Protocol) 설정

### MCP 서비스 실행

Greeum v0.4.0부터는 MCP를 통해 다양한 외부 도구와 연동할 수 있습니다. MCP 서비스를 실행하려면:

```bash
# CLI 명령을 통한 MCP 서비스 실행
greeum-mcp --port 8000 --data-dir ./data

# 또는 Python 모듈로 직접 실행
python -m memory_engine.mcp_service --port 8000 --data-dir ./data
```

### 환경 변수 설정 (선택사항)

MCP 서비스의 보안을 위해 다음 환경 변수를 설정할 수 있습니다:

```bash
# Windows
set ADMIN_KEY=your_secure_admin_key

# macOS/Linux
export ADMIN_KEY=your_secure_admin_key
```

### API 키 생성

MCP 서비스에 접근하려면 API 키가 필요합니다. 다음 방법으로 API 키를 생성할 수 있습니다:

```bash
# MCP 서비스가 실행 중인 상태에서 API 키 생성 요청
curl -X POST "http://localhost:8000/api/mcp/admin/api_key" \
  -H "Content-Type: application/json" \
  -d '{"action": "create", "admin_key": "your_secure_admin_key", "name": "My API Key"}'
```

또는 `examples/mcp_example.py` 스크립트를 사용할 수도 있습니다:

```bash
python examples/mcp_example.py --mode client
```

## 설치 검증

Greeum이 올바르게 설치되었는지 확인하려면 다음 명령을 실행하세요:

```bash
python -c "from greeum import BlockManager; print('Greeum 설치 성공!')"

# MCP 설치 확인
python -c "from memory_engine.mcp_client import MCPClient; print('MCP 설치 성공!')"
```

설치가 성공적이면 "Greeum 설치 성공!" 또는 "MCP 설치 성공!" 메시지가 표시됩니다.

## 다음 단계

- [API 레퍼런스](api-reference.md)를 참조하여 Greeum의 다양한 기능을 알아보세요.
- [튜토리얼](tutorials.md)을 통해 Greeum의 기본 사용법을 배워보세요.
- [MCP 예제](../examples/README.md)에서 MCP 사용 방법을 확인하세요.

## 문제 해결

**ImportError: No module named 'greeum'**
- 가상 환경이 활성화되었는지 확인하세요.
- `pip install -e .` 명령으로 개발 모드로 설치해 보세요.

**MCP 서비스 오류**
- `pip install greeum[mcp]` 명령으로 MCP 관련 의존성이 설치되었는지 확인하세요.
- 포트 충돌이 있는지 확인하고 필요하면 다른 포트를 사용하세요: `greeum-mcp --port 8080`

**권한 오류**
- 데이터 디렉토리에 대한 쓰기 권한이 있는지 확인하세요.

## 지원

문제가 계속되면 [이슈 트래커](https://github.com/DryRainEnt/Greeum/issues)에 문제를 보고하거나 이메일(playtart@play-t.art)로 문의하세요. 