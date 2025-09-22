# Branch-Aware Storage Upgrade Checklist

Branch 기능을 안전하게 활성화하기 위한 단계별 계획입니다. 각 단계는 가능한 한 테스트 주도 개발(TDD) 방식으로 진행하며, 중간 의사결정이 필요한 구간은 별도로 표시했습니다.

## 0. 사전 준비
- [ ] 현재 `~/.greeum/memory.db`와 `data/memory.db` 백업 생성 (`.bak` 부여).
- [ ] 실험용 디렉터리(`sandbox_data/`) 마련 후 환경변수(`GREEUM_DATA_DIR`)로 분리.
- [ ] 기존 테스트 통과 여부 확인 (`python3.11 -m pytest tests/test_embedding_models.py`).

## 1. 스키마 재정의
- [x] 필요한 열 목록 확정 (`blocks.slot TEXT`, `blocks.branch_similarity REAL`, `blocks.branch_created_at REAL`, `blocks.root`는 기존 유지).
- [x] STM 슬롯 테이블(`stm_slots`) / 브랜치 메타(`branch_meta`) 설계 검토.
  ```sql
  CREATE TABLE IF NOT EXISTS stm_slots (
      slot_name TEXT PRIMARY KEY,
      block_hash TEXT,
      branch_root TEXT,
      updated_at REAL
  );

  CREATE TABLE IF NOT EXISTS branch_meta (
      root TEXT PRIMARY KEY,
      title TEXT NOT NULL DEFAULT 'Untitled Branch',
      heads TEXT NOT NULL DEFAULT '{"A": null, "B": null, "C": null}',
      size INTEGER DEFAULT 0,
      depth INTEGER DEFAULT 0,
      created_at REAL NOT NULL,
      last_modified REAL NOT NULL,
      merge_history TEXT DEFAULT '[]',
      checkpoints TEXT DEFAULT '[]',
      total_visits INTEGER DEFAULT 0,
      total_searches INTEGER DEFAULT 0,
      local_hits INTEGER DEFAULT 0
  );
  ```
- [x] Decision: **FAISS 라이브러리**를 필수로 포함할지, `pip install greeum[full]` 옵션으로 둘지 결정. --> 필수 라이브러리로 포함. 벡터 변환은 빈번히 필요.
- [x] 브랜치 관련 SQL 정의 문서화 (`docs/branch_upgrade_checklist.md` 업데이트).

## 2. 마이그레이션 모듈 복구
- [x] AI 파서 계열 모듈 제거 및 `BranchMigrationInterface`로 대체.
- [x] `greeum migrate check/status` 정상 실행되도록 스키마 검사 로직 구현.
- [x] 데이터 이전 루틴 작성: 기존 블록을 새 스키마로 변환, STM 슬롯 초기화.
- [ ] TDD: 마이그레이션 테스트 추가 (`tests/test_branch_migration.py` 등) – 작은 SQLite fixture 사용.
- [x] Decision: **AI 파싱 재사용 여부**(Actant 추출 등)를 그대로 복구할지 단순 이동으로 대체할지 결정. --> Actant 피쳐는 스펙아웃. 추후 다른 기능으로 별도 제공 예정.

## 3. 저장 경로 보강
- [x] `BlockManager.add_block`가 새 컬럼(`slot`, `branch_root`, `before_id`)을 기록하도록 수정.
- [x] `BranchAwareStorage` / `BranchIndexManager` 생성자 시그니처 정리.
- [x] STM 슬롯 업데이트(`stm_slots` 테이블) ↔ 인메모리 구조 동기화.
- [x] 실패 시 graceful fallback 경로 유지 (로그 경고 수준 조정).
- [x] TDD: 신규 저장 테스트 (`tests/test_branch_storage.py`) 작성.
- [x] Decision: **슬롯 배정 전략**(FAISS vs 키워드 fallback)에서 사용할 임계값, 기본 슬롯 정책 확정. --> 어떤 조건에도 맞지 않는다면 가장 최신 노드에 부착.

## 4. FAISS & 인덱스 재구축
- [x] 브랜치별 FAISS 인덱스 생성 및 유지 로직 구현.
- [x] `branch_index`에서 DB 커넥션 사용 방식 정리 (BlockManager vs DatabaseManager).
- [x] CLI/도구 (`greeum memory reindex`, `branch status` 등) 추가 혹은 보완.
- [x] TDD: 검색 결과가 브랜치별로 제대로 구분되는지 통합 테스트 작성.
- [x] Decision: **FAISS가 설치되지 않은 환경**에서의 fallback 전략 확정. --> 기본값은 키워드 점수와 시간 가중치를 0.5:0.5로 합산(환경 변수 `GREEUM_BRANCH_FALLBACK_RATIO`로 조정 가능)하여 폴백.

## 5. 통합 테스트 및 문서화
- [ ] `pytest` 전 범위 실행 (핵심 스위트 기준).
  - note: 현재 유지 테스트는 `test_branch_*`, `test_cli_reindex.py`, `test_branch_manager.py`, `test_branch_integration.py` 등 브랜치/CLI 핵심 경로만 포함합니다.
- [x] 실험용 환경(`sandbox_data`)에서 end-to-end 흐름 검증:
  - `greeum setup`
  - 마이그레이션 (`greeum migrate upgrade` 가정)
  - `greeum memory add/search`
  - `greeum mcp serve` + 클라이언트 RPC 호출
- [x] 사용자 가이드 업데이트 (`docs/greeum-workflow-guide.md`, README 등).
- [x] 업데이트된 스키마/마이그레이션에 대한 “롤백 방법” 안내 추가. (BranchMigrationInterface가 자동 백업 생성. 롤백 시 `GREEUM_DATA_DIR=<dir> python - <<'PY'` 예제로 `AtomicBackupSystem.restore_backup(...)` 사용 가이드 추가.)
- [ ] Decision: **배포 채널**(pre-release → stable) 전환 시점 결정. --> 수평 구조 저장이라도 MCP 연동이 안정적으로 재현되면 우선 stable 배포 후 브랜치 기능 구현 진행.

## 6. 배포 전 최종 확인
- [ ] `CHANGELOG.md` 업데이트 (브랜치 지원 범위 및 마이그레이션 안내).
- [ ] 새 버전 태깅 및 빌드 (`python3.11 -m build`).
- [ ] 최종 로컬 설치 테스트 (`pipx install --pip-args "--pre" dist/...`).
- [ ] PyPI 업로드 (`python3.11 -m twine upload dist/...`).

각 단계가 끝날 때마다 체크박스를 갱신하면서 진행 상황을 추적하세요. 의사결정이 필요한 항목은 별도 코멘트나 회의로 확정한 뒤 문서에 반영하면 됩니다.

### 롤백 빠른 안내
1. 마이그레이션 전 자동 생성된 백업을 확인합니다.
   ```bash
   python - <<'PY'
from greeum.core.migration import AtomicBackupSystem
from pathlib import Path

backup = AtomicBackupSystem(str(Path('~/.greeum').expanduser()))
for meta in backup.list_backups():
    print(meta['backup_id'], meta['backup_path'])
PY
   ```
2. 특정 백업으로 되돌리려면 다음 스니펫을 실행합니다.
   ```bash
   python - <<'PY'
from greeum.core.migration import AtomicBackupSystem
from pathlib import Path

data_dir = Path('~/.greeum').expanduser()
backup = AtomicBackupSystem(str(data_dir))
backup.restore_backup('migration_backup_YYYYMMDD_HHMMSS')
PY
   ```
3. 복구 후 `greeum memory reindex --disable-faiss` 또는 기본 명령으로 브랜치 인덱스를 재생성하여 상태를 맞춥니다.
