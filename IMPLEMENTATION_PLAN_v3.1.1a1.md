# v3.1.1a1 구현 계획서

## 🎯 목표
**SimpleEmbeddingModel(랜덤)을 SentenceTransformer(의미)로 교체**

## 📝 구현 작업 목록

### Step 1: SentenceTransformerModel 클래스 구현
**파일**: `greeum/embedding_models.py`

```python
class SentenceTransformerModel(EmbeddingModel):
    """Sentence-Transformers 기반 의미적 임베딩 모델"""

    def __init__(self, model_name: str = None):
        """
        Args:
            model_name: 모델 이름 (기본값: 다국어 모델)
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers가 설치되지 않았습니다.\n"
                "pip install sentence-transformers 또는 "
                "pip install greeum[full]을 실행하세요."
            )

        # 기본 모델: 다국어 지원 (한국어 포함)
        if model_name is None:
            model_name = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'

        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.dimension = self.model.get_sentence_embedding_dimension()

    def encode(self, text: str) -> List[float]:
        """텍스트를 의미적 벡터로 인코딩"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def batch_encode(self, texts: List[str]) -> List[List[float]]:
        """배치 인코딩 (성능 최적화)"""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def get_dimension(self) -> int:
        return self.dimension

    def get_model_name(self) -> str:
        return f"sentence-transformers/{self.model_name}"
```

### Step 2: 초기화 함수 구현
**파일**: `greeum/embedding_models.py` (추가)

```python
def init_sentence_transformer(model_name: str = None, set_as_default: bool = True):
    """Sentence-Transformer 모델 초기화 및 등록"""
    try:
        model = SentenceTransformerModel(model_name)
        embedding_registry.register_model(
            "sentence-transformer",
            model,
            set_as_default=set_as_default
        )

        # 차원 확인 (기존 768과 호환성)
        if model.get_dimension() != 768:
            logger.warning(
                f"모델 차원 {model.get_dimension()}이 기본 768과 다릅니다. "
                "기존 데이터와 호환성 문제가 있을 수 있습니다."
            )

        return model
    except ImportError as e:
        logger.error(f"Sentence-Transformer 초기화 실패: {e}")
        raise
```

### Step 3: 자동 초기화 로직
**파일**: `greeum/embedding_models.py` (수정)

```python
# 전역 레지스트리 인스턴스 생성
embedding_registry = EmbeddingRegistry()

# 자동 초기화: sentence-transformers 있으면 사용, 없으면 simple
def _auto_init_best_model():
    """사용 가능한 최선의 모델 자동 초기화"""
    try:
        # 1순위: Sentence-Transformers
        init_sentence_transformer()
        logger.info("SentenceTransformer 모델 자동 초기화 성공")
    except ImportError:
        # 2순위: Simple (경고 표시)
        logger.warning(
            "⚠️ sentence-transformers가 없어 SimpleEmbeddingModel 사용 중.\n"
            "의미 기반 검색이 작동하지 않습니다!\n"
            "pip install sentence-transformers를 실행하세요."
        )
        embedding_registry.register_model(
            "simple",
            SimpleEmbeddingModel(dimension=768),
            set_as_default=True
        )

# 모듈 로드 시 자동 실행
_auto_init_best_model()
```

### Step 4: 모델 선택 전략

#### 후보 모델 비교
| 모델 | 차원 | 한국어 | 크기 | 속도 | 선택 |
|------|------|--------|------|------|------|
| paraphrase-multilingual-MiniLM-L12-v2 | 384 | ✅ | 118MB | 빠름 | ⭐ |
| xlm-r-100langs-bert-base-nli-stsb-mean-tokens | 768 | ✅ | 1GB | 보통 | |
| distiluse-base-multilingual-cased-v2 | 512 | ✅ | 135MB | 빠름 | |

**선택: paraphrase-multilingual-MiniLM-L12-v2**
- 이유: 한국어 지원, 경량, 빠른 속도
- 문제: 384차원 (기존 768과 불일치)
- 해결: 차원 변환 또는 재인덱싱

### Step 5: 차원 호환성 처리

```python
class DimensionAdapter:
    """차원 변환 어댑터"""

    @staticmethod
    def adapt_embedding(embedding: List[float], target_dim: int = 768) -> List[float]:
        current_dim = len(embedding)

        if current_dim == target_dim:
            return embedding
        elif current_dim < target_dim:
            # Padding with zeros
            return embedding + [0.0] * (target_dim - current_dim)
        else:
            # Truncation
            return embedding[:target_dim]
```

### Step 6: 마이그레이션 스크립트

```python
# scripts/migrate_embeddings.py
def migrate_to_semantic_embeddings(db_path: str):
    """기존 랜덤 임베딩을 의미적 임베딩으로 변환"""

    # 1. 새 모델 초기화
    from greeum.embedding_models import init_sentence_transformer
    model = init_sentence_transformer()

    # 2. 모든 블록 재인덱싱
    db = DatabaseManager(db_path)
    blocks = db.get_all_blocks()

    for block in blocks:
        # 새 임베딩 생성
        new_embedding = model.encode(block['context'])

        # DB 업데이트
        db.update_embedding(
            block['block_index'],
            new_embedding,
            model_name=model.get_model_name()
        )

    print(f"✅ {len(blocks)}개 블록 마이그레이션 완료")
```

### Step 7: 테스트 계획

#### 7.1 단위 테스트
```python
def test_semantic_similarity():
    """의미적 유사도 테스트"""
    model = SentenceTransformerModel()

    # 유사한 텍스트
    e1 = model.encode("파이썬으로 웹 개발하기")
    e2 = model.encode("Python 웹 프로그래밍")
    sim = cosine_similarity(e1, e2)
    assert sim > 0.6, f"유사 텍스트 유사도 너무 낮음: {sim}"

    # 다른 텍스트
    e3 = model.encode("김치찌개 만드는 법")
    sim2 = cosine_similarity(e1, e3)
    assert sim2 < 0.3, f"다른 텍스트 유사도 너무 높음: {sim2}"
```

#### 7.2 통합 테스트
```python
def test_slot_allocation_with_semantic():
    """의미 기반 슬롯 할당 테스트"""
    # A-B-C 패턴 테스트
    # 프로그래밍 컨텍스트들이 같은 슬롯에
    # 요리 컨텍스트는 다른 슬롯에
```

### Step 8: 의존성 업데이트

**pyproject.toml**:
```toml
[project.optional-dependencies]
semantic = ["sentence-transformers>=2.2.0"]
full = [
    "sentence-transformers>=2.2.0",  # 필수로 변경
    "faiss-cpu>=1.7.4",
    # ...
]
```

## 📅 일정

| 작업 | 예상 시간 | 우선순위 |
|------|-----------|----------|
| Step 1-2: 클래스 구현 | 2시간 | 🔴 최상 |
| Step 3: 자동 초기화 | 1시간 | 🔴 최상 |
| Step 4-5: 차원 처리 | 2시간 | 🟡 높음 |
| Step 6: 마이그레이션 | 3시간 | 🟡 높음 |
| Step 7: 테스트 | 2시간 | 🟢 보통 |
| Step 8: 문서화 | 1시간 | 🟢 보통 |

**총 예상: 11시간**

## ⚠️ 주의사항

1. **하위 호환성**: SimpleEmbeddingModel 유지 (fallback용)
2. **성능**: 첫 로드 시 모델 다운로드 (118MB)
3. **메모리**: 모델 로드 시 ~500MB RAM 사용
4. **차원**: 384 vs 768 불일치 처리 필요

## ✅ 완료 기준

- [ ] 유사 텍스트 유사도 > 0.5
- [ ] 다른 텍스트 유사도 < 0.3
- [ ] 슬롯 할당 정확도 > 80%
- [ ] 기존 DB 마이그레이션 성공
- [ ] CI/CD 통과

---

**작성일**: 2024-12-16
**버전**: v3.1.1a1
**상태**: 구현 대기