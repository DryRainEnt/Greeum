# Greeum 설치 및 시작하기

Greeum은 LLM 독립적인 기억 관리 시스템으로, 다양한 언어 모델과 통합하여 사용할 수 있습니다. 이 문서에서는 Greeum을 설치하고 기본 설정하는 방법을 설명합니다.

## 필수 요구사항

- Python 3.10 이상 (v0.6.0부터 최소 버전 상향 조정)
- pip (Python 패키지 관리자)
- Git (선택사항, 저장소 복제용)

## 설치 방법

### 1. PyPI에서 직접 설치 (권장)

```bash
# 기본 설치 (v0.6.0)
pip install greeum

# FAISS 벡터 인덱스 기능 포함
pip install greeum[faiss]

# OpenAI 임베딩 모델 지원
pip install greeum[openai]

# Transformers 및 BERT 재랭크 기능
pip install greeum[transformers]

# 모든 기능 포함 설치 (추천)
pip install greeum[all]
```

### 2. 저장소에서 설치

```bash
git clone https://github.com/DryRainEnt/Greeum.git
cd Greeum

# 기본 의존성 설치
pip install -r requirements.txt

# 개발 모드로 설치
pip install -e .

# 모든 기능 포함 개발 모드 설치 (추천)
pip install -e ".[all]"

# 특정 기능만 포함
pip install -e ".[faiss,transformers]"
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
    "format": "json",
    "database_url": "sqlite:///data/greeum.db"
  },
  "ttl": {
    "short": 3600,    // 1시간 (초 단위)
    "medium": 86400,  // 1일 (초 단위)
    "long": 2592000   // 30일 (초 단위)
  },
  "embedding": {
    "model": "default",
    "dimension": 384,
    "faiss_enabled": true
  },
  "search": {
    "use_bert_reranker": true,
    "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "vector_search_top_k": 15
  },
  "working_memory": {
    "capacity": 8,
    "ttl_seconds": 600
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

## v0.6.0 새로운 기능 설정

### FAISS 벡터 인덱스 설정

v0.6.0에서 추가된 FAISS 벡터 인덱스를 사용하려면:

```bash
# FAISS 의존성 설치
pip install greeum[faiss]

# 또는 직접 설치
pip install faiss-cpu>=1.7.4
```

### BERT 재랭크 설정

고도화된 검색 기능을 위한 BERT 재랭크를 사용하려면:

```bash
# Transformers 의존성 설치
pip install greeum[transformers]

# 또는 직접 설치
pip install sentence-transformers>=2.2.0
```

### STMWorkingSet 설정

작업 기억 기능은 별도의 설치 없이 기본 제공됩니다:

```python
from greeum import STMWorkingSet

# 기본 설정으로 사용
working_set = STMWorkingSet(capacity=8, ttl_seconds=600)
```

### OpenAI 임베딩 설정 (선택사항)

OpenAI의 임베딩 모델을 사용하려면:

```bash
# OpenAI 의존성 설치
pip install greeum[openai]

# 환경 변수 설정
export OPENAI_API_KEY="your_openai_api_key"
```

## 설치 검증

Greeum이 올바르게 설치되었는지 확인하려면 다음 명령을 실행하세요:

```bash
# 기본 설치 확인
python -c "from greeum import BlockManager; print('Greeum v0.6.0 설치 성공!')"

# FAISS 기능 확인
python -c "from greeum.vector_index import FaissVectorIndex; print('FAISS 벡터 인덱스 설치 성공!')"

# SearchEngine 기능 확인
python -c "from greeum.search_engine import SearchEngine; print('SearchEngine 설치 성공!')"

# STMWorkingSet 기능 확인
python -c "from greeum import STMWorkingSet; print('STMWorkingSet 설치 성공!')"

# BERT 재랭크 기능 확인 (선택사항)
python -c "from greeum.search_engine import BertReranker; print('BERT 재랭크 설치 성공!')"
```

설치가 성공적이면 각 기능에 대한 성공 메시지가 표시됩니다. FAISS나 BERT 재랭크 기능이 설치되지 않았다면 ImportError가 발생하는데, 이는 해당 선택사항이 설치되지 않았음을 의미합니다.

## 다음 단계

- [API 레퍼런스](api-reference.md)를 참조하여 Greeum v0.6.0의 다양한 기능을 알아보세요.
- [튜토리얼](tutorials.md)을 통해 FaissVectorIndex, SearchEngine, STMWorkingSet 등의 새로운 기능을 배워보세요.
- [examples](../examples/) 디렉토리에서 다양한 사용 예제를 확인하세요.

## 문제 해결

**ImportError: No module named 'greeum'**
- 가상 환경이 활성화되었는지 확인하세요.
- Python 3.10 이상을 사용하고 있는지 확인하세요.
- `pip install -e .` 명령으로 개발 모드로 설치해 보세요.

**FAISS 관련 오류**
- `pip install greeum[faiss]` 또는 `pip install faiss-cpu>=1.7.4` 로 FAISS 의존성을 설치하세요.
- M1/M2 Mac에서는 `conda install faiss-cpu`를 사용하는 것이 안정적입니다.

**BERT 재랭크 오류**
- `pip install greeum[transformers]` 로 sentence-transformers 의존성을 설치하세요.
- GPU 메모리 부족 시 CPU 모드로 대체됩니다.

**성능 이슈**
- 대용량 데이터 사용 시 FAISS 인덱스를 활용하세요.
- STMWorkingSet의 capacity와 ttl_seconds를 사용 패턴에 맞게 조정하세요.

**권한 오류**
- 데이터 디렉토리에 대한 쓰기 권한이 있는지 확인하세요.
- SQLite 데이터베이스 파일 생성 권한을 확인하세요.

## 지원

문제가 계속되면 [이슈 트래커](https://github.com/DryRainEnt/Greeum/issues)에 문제를 보고하거나 이메일(playtart@play-t.art)로 문의하세요. 
