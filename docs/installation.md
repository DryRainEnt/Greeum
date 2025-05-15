# Greeum 설치 및 시작하기

Greeum은 LLM 독립적인 기억 관리 시스템으로, 다양한 언어 모델과 통합하여 사용할 수 있습니다. 이 문서에서는 Greeum을 설치하고 기본 설정하는 방법을 설명합니다.

## 필수 요구사항

- Python 3.8 이상
- pip (Python 패키지 관리자)
- Git (선택사항, 저장소 복제용)

## 설치 방법

### 1. 저장소 복제

```bash
git clone https://github.com/DryRainEnt/Greeum.git
cd Greeum
```

### 2. 가상 환경 설정 (선택사항이지만 권장)

```bash
# 가상 환경 생성
python -m venv venv

# 가상 환경 활성화 (Windows)
venv\Scripts\activate

# 가상 환경 활성화 (macOS/Linux)
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
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
  }
}
```

### 스토리지 디렉토리 준비

메모리 블록이 저장될 디렉토리를 생성합니다:

```bash
mkdir -p data/memory
```

## 설치 검증

Greeum이 올바르게 설치되었는지 확인하려면 다음 명령을 실행하세요:

```bash
python -c "from greeum import BlockManager; print('Greeum 설치 성공!')"
```

설치가 성공적이면 "Greeum 설치 성공!" 메시지가 표시됩니다.

## 다음 단계

- [API 레퍼런스](api-reference.md)를 참조하여 Greeum의 다양한 기능을 알아보세요.
- [튜토리얼](tutorials.md)을 통해 Greeum의 기본 사용법을 배워보세요.
- [사용자 가이드](USER_GUIDE_KO.md)에서 더 자세한 사용법을 확인하세요.

## 문제 해결

**ImportError: No module named 'greeum'**
- 가상 환경이 활성화되었는지 확인하세요.
- `pip install -e .` 명령으로 개발 모드로 설치해 보세요.

**권한 오류**
- 데이터 디렉토리에 대한 쓰기 권한이 있는지 확인하세요.

## 지원

문제가 계속되면 [이슈 트래커](https://github.com/DryRainEnt/Greeum/issues)에 문제를 보고하거나 이메일(playtart@play-t.art)로 문의하세요. 