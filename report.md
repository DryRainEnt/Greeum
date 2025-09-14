{
  "examples": [
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 46,
      "example_type": "cli",
      "content": "greeum anchors status",
      "expected_output": null
    },
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 76,
      "example_type": "cli",
      "content": "# 특정 블록을 슬롯 A에 앵커로 설정\ngreeum anchors set A 1234\n\n# 사용자 정의 요약과 홉 예산으로 설정\ngreeum anchors set B 5678 --summary \"머신러닝 프로젝트\" --hop-budget 2",
      "expected_output": null
    },
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 86,
      "example_type": "cli",
      "content": "# 앵커 고정 (자동 이동 방지)\ngreeum anchors pin A\n\n# 앵커 고정 해제 (자동 이동 허용)\ngreeum anchors unpin A\n\n# 앵커 삭제\ngreeum anchors clear A",
      "expected_output": null
    },
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 99,
      "example_type": "cli",
      "content": "# 슬롯 A 기반 국소 검색 (반경: 2홉)\ngreeum search \"기계학습 알고리즘\" --slot A --radius 2\n\n# 여러 슬롯에서 검색\ngreeum search \"데이터 분석\" --slot B --radius 1 --fallback\n\n# 기존 검색 (앵커 사용 안함)\ngreeum search \"일반 검색어\"",
      "expected_output": null
    },
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 114,
      "example_type": "cli",
      "content": "curl -X GET \"http://localhost:5000/v1/anchors\"",
      "expected_output": null
    },
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 147,
      "example_type": "cli",
      "content": "# 앵커 블록 변경\ncurl -X PATCH \"http://localhost:5000/v1/anchors/A\" \\\n     -H \"Content-Type: application/json\" \\\n     -d '{\n       \"anchor_block_id\": \"9999\",\n       \"summary\": \"새로운 프로젝트 시작\",\n       \"hop_budget\": 2\n     }'\n\n# 앵커 고정\ncurl -X PATCH \"http://localhost:5000/v1/anchors/B\" \\\n     -H \"Content-Type: application/json\" \\\n     -d '{\"pinned\": true}'",
      "expected_output": null
    },
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 165,
      "example_type": "cli",
      "content": "# 슬롯 A 기반 검색\ncurl -X GET \"http://localhost:5000/api/v1/search?query=머신러닝&slot=A&radius=2&limit=5\"\n\n# 결과 예시\n{\n  \"results\": [\n    {\n      \"block_index\": 1234,\n      \"context\": \"머신러닝 알고리즘 구현 방법...\",\n      \"relevance_score\": 0.95\n    }\n  ],\n  \"metadata\": {\n    \"local_search_used\": true,\n    \"local_results\": 3,\n    \"fallback_used\": false\n  },\n  \"search_type\": \"anchor_based\",\n  \"slot\": \"A\",\n  \"radius\": 2\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 193,
      "example_type": "cli",
      "content": "# 1. 프로젝트 시작 - API 설계 블록을 앵커로 설정\ngreeum anchors set A 1001 --summary \"RESTful API 설계\"\n\n# 2. 관련 검색 - 앵커 주변에서 관련 내용 찾기\ngreeum search \"인증 방법\" --slot A --radius 2\n\n# 3. 보조 맥락 설정 - 데이터베이스 관련\ngreeum anchors set B 2002 --summary \"PostgreSQL 스키마\"\n\n# 4. 다차원 검색\ngreeum search \"사용자 권한\" --slot A  # API 맥락에서\ngreeum search \"사용자 권한\" --slot B  # DB 맥락에서",
      "expected_output": null
    },
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 210,
      "example_type": "cli",
      "content": "# 1. 주요 논문을 앵커로 설정\ngreeum anchors set A 3001 --summary \"Transformer 아키텍처 논문\"\ngreeum anchors pin A  # 고정하여 자동 이동 방지\n\n# 2. 관련 논문들 탐색\ngreeum search \"attention mechanism\" --slot A --radius 3\n\n# 3. 보조 주제 설정\ngreeum anchors set B 3002 --summary \"BERT 모델 구현\"\n\n# 4. 비교 분석\ngreeum search \"self-attention\" --slot A  # Transformer 관점\ngreeum search \"self-attention\" --slot B  # BERT 관점",
      "expected_output": null
    },
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 251,
      "example_type": "cli",
      "content": "# 앵커 사용 통계 확인 (향후 구현 예정)\ngreeum anchors stats\n\n# 검색 성능 비교\ngreeum search \"테스트 쿼리\"           # 전역 검색\ngreeum search \"테스트 쿼리\" --slot A  # 앵커 검색 (더 빠름)",
      "expected_output": null
    },
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 272,
      "example_type": "cli",
      "content": "# A: Bootstrap 스크립트 실행\npython scripts/bootstrap_graphindex.py",
      "expected_output": null
    },
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 278,
      "example_type": "cli",
      "content": "# A: Fallback 옵션 사용 또는 반경 확장\ngreeum search \"쿼리\" --slot A --radius 3 --fallback",
      "expected_output": null
    },
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 284,
      "example_type": "cli",
      "content": "# A: 중요한 앵커는 고정하세요\ngreeum anchors pin A",
      "expected_output": null
    },
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 290,
      "example_type": "cli",
      "content": "# A: 홉 예산을 줄이고 적절한 슬롯 사용\ngreeum search \"쿼리\" --slot A --radius 1  # 더 빠름",
      "expected_output": null
    },
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 298,
      "example_type": "cli",
      "content": "# 백업에서 복원\ncp data/anchors_backup.json data/anchors.json\n\n# 또는 재초기화\nrm data/anchors.json\npython scripts/bootstrap_graphindex.py",
      "expected_output": null
    },
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 308,
      "example_type": "cli",
      "content": "# 그래프 재구성 (시간 소요)\nrm data/graph_snapshot.jsonl\npython scripts/bootstrap_graphindex.py --rebuild-graph",
      "expected_output": null
    },
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 232,
      "example_type": "python",
      "content": "# Python API 예제\nfrom greeum.anchors.auto_movement import AutoAnchorMovement\n\nauto_movement = AutoAnchorMovement(anchor_manager, links_cache, db_manager)\n\n# 주제 변화 감지 및 앵커 이동 평가\nevaluation = auto_movement.evaluate_anchor_movement(\n    slot='A',\n    search_results=recent_search_results,\n    query_topic_vec=new_topic_embedding\n)\n\nif evaluation['should_move']:\n    print(f\"앵커 이동 권장: {evaluation['reason']}\")",
      "expected_output": null
    },
    {
      "file_path": "docs/anchors-guide.md",
      "line_number": 119,
      "example_type": "json",
      "content": "{\n  \"version\": 1,\n  \"slots\": [\n    {\n      \"slot\": \"A\",\n      \"anchor_block_id\": \"1234\",\n      \"hop_budget\": 3,\n      \"pinned\": true,\n      \"last_used_ts\": 1693555200,\n      \"summary\": \"API 개발 관련 메모리\"\n    },\n    {\n      \"slot\": \"B\",\n      \"anchor_block_id\": \"5678\",\n      \"hop_budget\": 2,\n      \"pinned\": false,\n      \"last_used_ts\": 1693555100,\n      \"summary\": \"데이터베이스 설계\"\n    }\n  ],\n  \"updated_at\": 1693555300,\n  \"timestamp\": \"2025-08-28T12:00:00\"\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_migration_safety.md",
      "line_number": 24,
      "example_type": "python",
      "content": "class SchemaVersionManager:\n    \"\"\"스키마 버전 관리 및 호환성 보장\"\"\"\n    \n    # 스키마 버전 상수\n    SCHEMA_V252 = \"2.5.2\"\n    SCHEMA_V253 = \"2.5.3\"\n    SCHEMA_MIGRATION_IN_PROGRESS = \"2.5.3-MIGRATING\"\n    \n    def __init__(self, db_path: str):\n        self.db_path = db_path\n        self._ensure_version_table()\n    \n    def _ensure_version_table(self):\n        \"\"\"버전 관리 테이블 생성 (모든 버전에서 안전)\"\"\"\n        conn = sqlite3.connect(self.db_path)\n        try:\n            conn.execute('''\n                CREATE TABLE IF NOT EXISTS schema_version (\n                    version TEXT PRIMARY KEY,\n                    applied_at TEXT NOT NULL,\n                    status TEXT NOT NULL,  -- 'STABLE', 'MIGRATING', 'FAILED'\n                    backup_path TEXT,\n                    migration_log TEXT\n                )\n            ''')\n            \n            # 기본 버전 설정 (기존 DB라면 2.5.2)\n            cursor = conn.execute(\"SELECT COUNT(*) FROM schema_version\")\n            if cursor.fetchone()[0] == 0:\n                conn.execute('''\n                    INSERT INTO schema_version (version, applied_at, status) \n                    VALUES (?, datetime('now'), 'STABLE')\n                ''', (self.SCHEMA_V252,))\n            \n            conn.commit()\n        finally:\n            conn.close()\n    \n    def get_current_version(self) -> str:\n        \"\"\"현재 스키마 버전 조회\"\"\"\n        conn = sqlite3.connect(self.db_path)\n        try:\n            cursor = conn.execute(\n                \"SELECT version FROM schema_version WHERE status = 'STABLE' ORDER BY applied_at DESC LIMIT 1\"\n            )\n            result = cursor.fetchone()\n            return result[0] if result else self.SCHEMA_V252\n        finally:\n            conn.close()\n    \n    def is_migration_in_progress(self) -> bool:\n        \"\"\"마이그레이션 진행 중인지 확인\"\"\"\n        conn = sqlite3.connect(self.db_path)\n        try:\n            cursor = conn.execute(\n                \"SELECT COUNT(*) FROM schema_version WHERE status = 'MIGRATING'\"\n            )\n            return cursor.fetchone()[0] > 0\n        finally:\n            conn.close()\n    \n    def mark_migration_start(self, target_version: str, backup_path: str) -> None:\n        \"\"\"마이그레이션 시작 표시\"\"\"\n        conn = sqlite3.connect(self.db_path)\n        try:\n            conn.execute('''\n                INSERT INTO schema_version (version, applied_at, status, backup_path) \n                VALUES (?, datetime('now'), 'MIGRATING', ?)\n            ''', (target_version, backup_path))\n            conn.commit()\n        finally:\n            conn.close()\n    \n    def mark_migration_complete(self, version: str) -> None:\n        \"\"\"마이그레이션 완료 표시\"\"\"\n        conn = sqlite3.connect(self.db_path)\n        try:\n            # 마이그레이션 상태를 완료로 변경\n            conn.execute('''\n                UPDATE schema_version \n                SET status = 'STABLE' \n                WHERE version = ? AND status = 'MIGRATING'\n            ''', (version,))\n            conn.commit()\n        finally:\n            conn.close()",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_migration_safety.md",
      "line_number": 115,
      "example_type": "python",
      "content": "class AtomicBackupSystem:\n    \"\"\"원자적 백업 및 복구 시스템\"\"\"\n    \n    def create_pre_migration_backup(self, db_path: str) -> str:\n        \"\"\"마이그레이션 전 완전 백업\"\"\"\n        timestamp = datetime.now().strftime(\"%Y%m%d_%H%M%S\")\n        backup_path = f\"{db_path}.backup_v252_{timestamp}\"\n        \n        try:\n            # SQLite 백업 (온라인 백업)\n            source = sqlite3.connect(db_path)\n            backup = sqlite3.connect(backup_path)\n            \n            source.backup(backup)\n            \n            backup.close()\n            source.close()\n            \n            # 백업 무결성 검증\n            if not self._verify_backup_integrity(backup_path):\n                raise BackupError(\"Backup integrity verification failed\")\n            \n            logger.info(f\"✅ Pre-migration backup created: {backup_path}\")\n            return backup_path\n            \n        except Exception as e:\n            # 백업 실패시 안전하게 정리\n            if os.path.exists(backup_path):\n                os.remove(backup_path)\n            raise BackupError(f\"Failed to create backup: {e}\")\n    \n    def _verify_backup_integrity(self, backup_path: str) -> bool:\n        \"\"\"백업 파일 무결성 검증\"\"\"\n        try:\n            conn = sqlite3.connect(backup_path)\n            conn.execute(\"PRAGMA integrity_check\")\n            result = conn.fetchone()\n            conn.close()\n            return result[0] == \"ok\"\n        except:\n            return False\n    \n    def restore_from_backup(self, db_path: str, backup_path: str) -> bool:\n        \"\"\"백업에서 복구\"\"\"\n        try:\n            if os.path.exists(db_path):\n                # 현재 DB 임시 이동\n                temp_path = f\"{db_path}.corrupted_{int(time.time())}\"\n                os.rename(db_path, temp_path)\n            \n            # 백업에서 복구\n            shutil.copy2(backup_path, db_path)\n            \n            # 복구 검증\n            if self._verify_backup_integrity(db_path):\n                logger.info(f\"✅ Successfully restored from backup: {backup_path}\")\n                return True\n            else:\n                raise RestoreError(\"Restored database failed integrity check\")\n                \n        except Exception as e:\n            logger.error(f\"❌ Restore failed: {e}\")\n            return False",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_migration_safety.md",
      "line_number": 183,
      "example_type": "python",
      "content": "class DefensiveSchemaAccess:\n    \"\"\"방어적 스키마 접근 래퍼\"\"\"\n    \n    def __init__(self, db_path: str):\n        self.db_path = db_path\n        self.version_manager = SchemaVersionManager(db_path)\n        self._cached_columns = {}\n    \n    def safe_select(self, table: str, columns: List[str], where_clause: str = \"\", \n                   params: Tuple = ()) -> List[Dict]:\n        \"\"\"안전한 SELECT 쿼리 (존재하지 않는 컬럼 자동 제외)\"\"\"\n        \n        # 테이블의 실제 컬럼 확인\n        available_columns = self._get_available_columns(table)\n        safe_columns = [col for col in columns if col in available_columns]\n        \n        if len(safe_columns) != len(columns):\n            missing = set(columns) - set(available_columns)\n            logger.warning(f\"⚠️  Missing columns in {table}: {missing}\")\n        \n        if not safe_columns:\n            logger.error(f\"❌ No valid columns for table {table}\")\n            return []\n        \n        # 안전한 쿼리 실행\n        query = f\"SELECT {', '.join(safe_columns)} FROM {table}\"\n        if where_clause:\n            query += f\" WHERE {where_clause}\"\n        \n        conn = sqlite3.connect(self.db_path)\n        conn.row_factory = sqlite3.Row\n        try:\n            cursor = conn.execute(query, params)\n            return [dict(row) for row in cursor.fetchall()]\n        except Exception as e:\n            logger.error(f\"❌ Safe select failed: {e}\")\n            return []\n        finally:\n            conn.close()\n    \n    def safe_insert(self, table: str, data: Dict[str, Any]) -> bool:\n        \"\"\"안전한 INSERT (존재하지 않는 컬럼 자동 제외)\"\"\"\n        available_columns = self._get_available_columns(table)\n        safe_data = {k: v for k, v in data.items() if k in available_columns}\n        \n        if len(safe_data) != len(data):\n            excluded = set(data.keys()) - set(available_columns)\n            logger.warning(f\"⚠️  Excluded unknown columns: {excluded}\")\n        \n        if not safe_data:\n            logger.error(\"❌ No valid data for insert\")\n            return False\n        \n        # 안전한 INSERT 실행\n        columns = list(safe_data.keys())\n        placeholders = ['?' for _ in columns]\n        values = list(safe_data.values())\n        \n        query = f\"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})\"\n        \n        conn = sqlite3.connect(self.db_path)\n        try:\n            conn.execute(query, values)\n            conn.commit()\n            return True\n        except Exception as e:\n            logger.error(f\"❌ Safe insert failed: {e}\")\n            return False\n        finally:\n            conn.close()\n    \n    def _get_available_columns(self, table: str) -> List[str]:\n        \"\"\"테이블의 사용 가능한 컬럼 목록\"\"\"\n        if table in self._cached_columns:\n            return self._cached_columns[table]\n        \n        conn = sqlite3.connect(self.db_path)\n        try:\n            cursor = conn.execute(f\"PRAGMA table_info({table})\")\n            columns = [row[1] for row in cursor.fetchall()]\n            self._cached_columns[table] = columns\n            return columns\n        except Exception as e:\n            logger.error(f\"❌ Failed to get columns for {table}: {e}\")\n            return []\n        finally:\n            conn.close()",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_migration_safety.md",
      "line_number": 275,
      "example_type": "python",
      "content": "class SafeMigrationTransaction:\n    \"\"\"안전한 마이그레이션 트랜잭션\"\"\"\n    \n    def __init__(self, db_path: str):\n        self.db_path = db_path\n        self.conn = None\n        self.backup_system = AtomicBackupSystem()\n        self.version_manager = SchemaVersionManager(db_path)\n    \n    def __enter__(self):\n        \"\"\"트랜잭션 시작\"\"\"\n        try:\n            # 1. 백업 생성\n            self.backup_path = self.backup_system.create_pre_migration_backup(self.db_path)\n            \n            # 2. 마이그레이션 상태 표시\n            self.version_manager.mark_migration_start(\"2.5.3\", self.backup_path)\n            \n            # 3. DB 연결 및 트랜잭션 시작\n            self.conn = sqlite3.connect(self.db_path)\n            self.conn.execute(\"BEGIN IMMEDIATE\")  # 즉시 배타적 락\n            \n            logger.info(\"🔒 Migration transaction started\")\n            return self\n            \n        except Exception as e:\n            logger.error(f\"❌ Failed to start migration transaction: {e}\")\n            self._cleanup()\n            raise\n    \n    def __exit__(self, exc_type, exc_val, exc_tb):\n        \"\"\"트랜잭션 종료\"\"\"\n        try:\n            if exc_type is None:\n                # 성공적 완료\n                self.conn.commit()\n                self.version_manager.mark_migration_complete(\"2.5.3\")\n                logger.info(\"✅ Migration transaction committed\")\n            else:\n                # 오류 발생 - 롤백\n                self.conn.rollback()\n                logger.error(f\"❌ Migration failed, rolling back: {exc_val}\")\n                \n                # 백업에서 복구 시도\n                if hasattr(self, 'backup_path'):\n                    self.backup_system.restore_from_backup(self.db_path, self.backup_path)\n                \n        finally:\n            if self.conn:\n                self.conn.close()\n            self._cleanup()\n    \n    def execute_safe_ddl(self, ddl_statement: str) -> bool:\n        \"\"\"안전한 DDL 실행\"\"\"\n        try:\n            self.conn.execute(ddl_statement)\n            logger.debug(f\"✅ DDL executed: {ddl_statement[:50]}...\")\n            return True\n        except Exception as e:\n            logger.error(f\"❌ DDL failed: {ddl_statement[:50]}... Error: {e}\")\n            raise\n    \n    def _cleanup(self):\n        \"\"\"정리 작업\"\"\"\n        # 임시 파일 정리는 나중에... 백업은 보존\n        pass",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_migration_safety.md",
      "line_number": 346,
      "example_type": "python",
      "content": "class VersionGuard:\n    \"\"\"버전 호환성 보장 시스템\"\"\"\n    \n    SUPPORTED_VERSIONS = [\"2.5.2\", \"2.5.3\"]\n    CURRENT_CODE_VERSION = \"2.5.3\"\n    \n    def __init__(self, db_path: str):\n        self.db_path = db_path\n        self.version_manager = SchemaVersionManager(db_path)\n    \n    def check_compatibility(self) -> CompatibilityResult:\n        \"\"\"현재 코드와 DB 버전 호환성 체크\"\"\"\n        \n        # 마이그레이션 중인지 확인\n        if self.version_manager.is_migration_in_progress():\n            return CompatibilityResult(\n                compatible=False,\n                action_required=\"RESUME_OR_ROLLBACK\",\n                message=\"Migration in progress. Please resume or rollback.\"\n            )\n        \n        db_version = self.version_manager.get_current_version()\n        \n        # 정확한 버전 매칭\n        if db_version == self.CURRENT_CODE_VERSION:\n            return CompatibilityResult(\n                compatible=True,\n                action_required=\"NONE\",\n                message=\"Perfect version match\"\n            )\n        \n        # 하위 호환성 체크\n        if db_version == \"2.5.2\" and self.CURRENT_CODE_VERSION == \"2.5.3\":\n            return CompatibilityResult(\n                compatible=False,\n                action_required=\"MIGRATION_REQUIRED\",\n                message=\"Database upgrade required from 2.5.2 to 2.5.3\"\n            )\n        \n        # 상위 호환성 (다운그레이드) 체크\n        if db_version == \"2.5.3\" and self.CURRENT_CODE_VERSION == \"2.5.2\":\n            return CompatibilityResult(\n                compatible=False,\n                action_required=\"DOWNGRADE_NOT_SUPPORTED\", \n                message=\"Cannot use v2.5.2 code with v2.5.3 database\"\n            )\n        \n        # 알 수 없는 버전\n        return CompatibilityResult(\n            compatible=False,\n            action_required=\"UNKNOWN_VERSION\",\n            message=f\"Unknown database version: {db_version}\"\n        )\n    \n    def enforce_compatibility(self) -> None:\n        \"\"\"호환성 강제 실행\"\"\"\n        result = self.check_compatibility()\n        \n        if result.compatible:\n            return\n        \n        if result.action_required == \"MIGRATION_REQUIRED\":\n            print(f\"🚨 {result.message}\")\n            # 마이그레이션 프로세스 시작...\n            \n        elif result.action_required == \"DOWNGRADE_NOT_SUPPORTED\":\n            print(f\"❌ {result.message}\")\n            print(\"Please use Greeum v2.5.3 or later\")\n            sys.exit(1)\n            \n        elif result.action_required == \"RESUME_OR_ROLLBACK\":\n            print(f\"⚠️  {result.message}\")\n            # 복구 옵션 제공...\n            \n        else:\n            print(f\"💥 {result.message}\")\n            sys.exit(1)",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_migration_safety.md",
      "line_number": 428,
      "example_type": "python",
      "content": "def safe_migration_flow():\n    \"\"\"완전 안전 마이그레이션 실행\"\"\"\n    \n    # 1. 버전 가드 체크\n    guard = VersionGuard(db_path)\n    guard.enforce_compatibility()\n    \n    # 2. 안전 트랜잭션으로 마이그레이션\n    try:\n        with SafeMigrationTransaction(db_path) as migration:\n            # 스키마 업그레이드\n            migration.execute_safe_ddl(\"ALTER TABLE blocks ADD COLUMN actant_subject TEXT DEFAULT NULL\")\n            migration.execute_safe_ddl(\"ALTER TABLE blocks ADD COLUMN actant_action TEXT DEFAULT NULL\") \n            migration.execute_safe_ddl(\"ALTER TABLE blocks ADD COLUMN actant_object TEXT DEFAULT NULL\")\n            \n            # 데이터 마이그레이션 (방어적 접근)\n            defensive_db = DefensiveSchemaAccess(db_path)\n            blocks = defensive_db.safe_select(\"blocks\", [\"block_index\", \"context\"])\n            \n            for block in blocks:\n                try:\n                    # AI 파싱\n                    result = ai_parser.parse_legacy_memory(block['context'])\n                    \n                    # 안전한 업데이트\n                    if result.success:\n                        defensive_db.safe_insert(\"temp_updates\", {\n                            \"block_index\": block['block_index'],\n                            \"actant_subject\": result.subject,\n                            \"actant_action\": result.action,\n                            \"actant_object\": result.object_target\n                        })\n                        \n                except Exception as e:\n                    logger.warning(f\"Block {block['block_index']} migration failed: {e}\")\n                    continue\n        \n        print(\"✅ Migration completed successfully!\")\n        \n    except Exception as e:\n        print(f\"❌ Migration failed: {e}\")\n        print(\"🔄 Database restored from backup\")",
      "expected_output": null
    },
    {
      "file_path": "docs/troubleshooting.md",
      "line_number": 6,
      "example_type": "cli",
      "content": "# Check if Greeum is installed\ngreeum --version\n\n# Test basic functionality\ngreeum memory add \"test message\"\n\n# Test MCP server (should start and stop after 5 seconds)\ntimeout 5s greeum mcp serve -t stdio",
      "expected_output": null
    },
    {
      "file_path": "docs/troubleshooting.md",
      "line_number": 24,
      "example_type": "cli",
      "content": "# Check if installed\npip show greeum\n\n# Install if missing\npip install greeum\n\n# Check PATH (should show greeum location)\nwhich greeum\n\n# If using virtual environment, activate it first\nsource venv/bin/activate  # Linux/macOS\n# or\nvenv\\Scripts\\activate     # Windows",
      "expected_output": null
    },
    {
      "file_path": "docs/troubleshooting.md",
      "line_number": 47,
      "example_type": "cli",
      "content": "   # Validate JSON (should not show errors)\n   python -c \"import json; print('✅ Valid JSON' if json.load(open('claude_desktop_config.json')) else '❌ Invalid JSON')\"\n   ```\n\n2. **Verify configuration file location**:\n   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`\n   - **Windows**: `%APPDATA%\\Claude\\claude_desktop_config.json`  \n   - **Linux**: `~/.config/claude-desktop/claude_desktop_config.json`\n\n3. **Test server manually**:\n   ```bash\n   # Should start without immediate errors\n   greeum mcp serve -t stdio\n   \n   # Press Ctrl+C to stop\n   ```\n\n4. **Check Claude Desktop logs**:\n   ```bash\n   # macOS\n   tail -f ~/Library/Logs/Claude/mcp*.log\n   \n   # Windows\n   # Check %APPDATA%\\Claude\\Logs\\\n   \n   # Linux  \n   tail -f ~/.local/share/Claude/logs/mcp*.log\n   ```\n\n### ❌ \"Permission denied\" errors\n\n**Problem**: Greeum cannot write to data directory\n\n**Solutions**:",
      "expected_output": null
    },
    {
      "file_path": "docs/troubleshooting.md",
      "line_number": 102,
      "example_type": "cli",
      "content": "# Reinstall with all dependencies\npip install --upgrade greeum\n\n# Check required dependencies\npip install numpy>=1.24.0 sqlalchemy>=2.0.0 click>=8.1.0\n\n# For MCP functionality specifically\npip install mcp>=1.0.0",
      "expected_output": null
    },
    {
      "file_path": "docs/troubleshooting.md",
      "line_number": 137,
      "example_type": "cli",
      "content": "   # Enable debug logging\n   GREEUM_LOG_LEVEL=DEBUG greeum mcp serve -t stdio\n   ```\n\n## Environment-Specific Issues\n\n### WSL (Windows Subsystem for Linux)\n",
      "expected_output": null
    },
    {
      "file_path": "docs/troubleshooting.md",
      "line_number": 190,
      "example_type": "cli",
      "content": "# Set debug level\nexport GREEUM_LOG_LEVEL=DEBUG\n\n# Run with debug output\nGREEUM_LOG_LEVEL=DEBUG greeum mcp serve -t stdio\n\n# Check log files\nls ~/.greeum/\ncat ~/.greeum/debug.log",
      "expected_output": null
    },
    {
      "file_path": "docs/troubleshooting.md",
      "line_number": 204,
      "example_type": "cli",
      "content": "# Test memory functions directly\ngreeum memory add \"debug test message\"\ngreeum memory search \"debug test\"\n\n# Test MCP server startup\ngreeum mcp serve --help\n\n# Check system status\ngreeum memory stats",
      "expected_output": null
    },
    {
      "file_path": "docs/troubleshooting.md",
      "line_number": 125,
      "example_type": "json",
      "content": "   {\n     \"mcpServers\": {\n       \"greeum\": {\n         \"command\": \"greeum\",\n         \"args\": [\"mcp\", \"serve\", \"-t\", \"stdio\"]\n       }\n     }\n   }\n   ```\n\n3. **Verify tools are working**:\n   ```bash\n   # Enable debug logging\n   GREEUM_LOG_LEVEL=DEBUG greeum mcp serve -t stdio\n   ```\n\n## Environment-Specific Issues\n\n### WSL (Windows Subsystem for Linux)\n",
      "expected_output": null
    },
    {
      "file_path": "docs/troubleshooting.md",
      "line_number": 167,
      "example_type": "json",
      "content": "{\n  \"mcpServers\": {\n    \"greeum\": {\n      \"command\": \"powershell\",\n      \"args\": [\"-Command\", \"greeum mcp serve -t stdio\"],\n      \"env\": {\n        \"GREEUM_DATA_DIR\": \"C:\\\\Users\\\\YourName\\\\greeum-data\"\n      }\n    }\n  }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/v2.3-roadmap.md",
      "line_number": 359,
      "example_type": "cli",
      "content": "# 성능 벤치마크 자동 실행\npython scripts/quality_benchmark.py --full\npython scripts/performance_benchmark.py --stress --duration 3600",
      "expected_output": null
    },
    {
      "file_path": "docs/v2.3-roadmap.md",
      "line_number": 118,
      "example_type": "python",
      "content": "# 예시: 분산 검색 아키텍처\nclass DistributedSearchEngine:\n    def __init__(self, shard_managers: List[ShardManager]):\n        self.shards = shard_managers\n    \n    async def search(self, query: str, top_k: int) -> SearchResult:\n        # 모든 샤드에서 병렬 검색\n        shard_results = await asyncio.gather(*[\n            shard.search(query, top_k // len(self.shards))\n            for shard in self.shards\n        ])\n        # 결과 병합 및 재정렬\n        return self.merge_results(shard_results, top_k)",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_migration_complete.md",
      "line_number": 39,
      "example_type": "cli",
      "content": "$ greeum memory search \"프로젝트\"\n\n🚨 Greeum v2.5.3 Schema Migration Required\n📊 Legacy database detected with 150 memories\n⚡ AI will enhance your memories with structured actant format\n🤖 This enables powerful relationship and causality analysis\n\nProceed with AI migration? [Y/n]: y\n\n🤖 Starting AI-powered migration...\n📊 Found 150 memories to migrate\n✅ Migrating: 100.0% (150/150)\n\n🎉 Migration completed in 12.3 seconds!\n✅ Successfully migrated: 142\n⚠️  Preserved as-is: 8\n📈 Migration success rate: 94.7%\n\n🔍 Discovering relationships in migrated data...\n🔗 Discovered 89 relationships:\n   👥 Subject collaborations: 34\n   ⚡ Action causalities: 28\n   🔗 Object dependencies: 27\n\n✨ Your memory system is now enhanced with actant structure!\n🔍 Search results: Found 12 project-related memories",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_migration_complete.md",
      "line_number": 69,
      "example_type": "cli",
      "content": "# 마이그레이션 상태 확인\n$ greeum migrate status\n📊 Greeum Database Migration Status\n📋 Schema Version: 2.5.2\n💾 Total Memories: 150\n⚠️  Migration Required: Legacy v2.5.2 database detected\n\n# 마이그레이션 실행\n$ greeum migrate check\n🔍 Checking Greeum database schema version...\n[AI 마이그레이션 프로세스 실행]\n✨ Database is ready for use!\n\n# 마이그레이션 검증\n$ greeum migrate validate\n🔍 Validating Database Migration Health\n✅ Overall Status: VALIDATION_PASSED\n✅ Database Integrity: PASS\n✅ Schema Validation: PASS\n✅ Data Preservation: PASS\n\n# 비상 롤백 (필요시)\n$ greeum migrate rollback\n📋 Available rollback options:\n1. migration_backup_20250908_143022\n   Created: 2025-09-08 14:30\n   Status: ✅ Verified",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_migration_complete.md",
      "line_number": 129,
      "example_type": "python",
      "content": "# AI가 이 텍스트를:\n\"사용자가 새로운 기능을 요청했고 정말 흥미로워요\"\n\n# 이렇게 구조화:\n{\n    \"subject\": \"사용자\",\n    \"action\": \"요청\", \n    \"object\": \"기능\",\n    \"confidence\": 0.85,\n    \"reasoning\": \"명확한 주체-행동-대상 구조 감지\"\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 27,
      "example_type": "cli",
      "content": "# Install with pipx (recommended)\npipx install greeum\n\n# Or install with pip\npip install greeum\n\n# Verify installation\ngreeum --version  # Should show v2.0.5 or higher",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 42,
      "example_type": "cli",
      "content": "# Step 1: Add your first memory\npython3 -m greeum.cli memory add \"Started learning Greeum v2.0.5 - it has amazing quality validation features!\"\n\n# Step 2: Search memories\npython3 -m greeum.cli memory search \"learning Greeum\" --limit 5\n\n# Step 3: Analyze your memory patterns\npython3 -m greeum.cli ltm analyze --period 7d",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 290,
      "example_type": "cli",
      "content": "# Analyze long-term memory patterns\npython3 -m greeum.cli ltm analyze --period 30d --trends\n\n# Manage short-term memory\npython3 -m greeum.cli stm cleanup --expired\npython3 -m greeum.cli stm promote --threshold 0.8\n\n# Export memory data\npython3 -m greeum.cli ltm export --format json --limit 1000",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 304,
      "example_type": "cli",
      "content": "# Basic memory search\npython3 -m greeum.cli memory search \"machine learning project\" --limit 10\n\n# Search in long-term memory with analysis\npython3 -m greeum.cli ltm analyze --period 1d\n\n# Add specific search terms to short-term memory\npython3 -m greeum.cli stm add \"Searching for ML project info\" --ttl 30m",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 322,
      "example_type": "cli",
      "content": "   # Install GreeumMCP package\n   pip install greeummcp\n   \n   # Verify installation\n   python -m greeum.mcp.claude_code_mcp_server --help\n   ```\n\n2. **Configure Claude Desktop**:\n   \n   Edit your Claude Desktop configuration (`~/.config/claude-desktop/claude_desktop_config.json`):\n   \n   ```json\n   {\n     \"mcpServers\": {\n       \"greeum\": {\n         \"command\": \"python3\",\n         \"args\": [\"-m\", \"greeum.mcp.claude_code_mcp_server\"],\n         \"env\": {\n           \"GREEUM_DATA_DIR\": \"/path/to/your/data\",\n           \"GREEUM_LOG_LEVEL\": \"INFO\"\n         }\n       }\n     }\n   }\n   ```\n\n3. **Verify Connection**:\n   ```bash\n   claude mcp list\n   # Should show: greeum - ✓ Connected\n   ```\n\n### Using MCP Tools in Claude Code\n\nOnce configured, you can use these 12 MCP tools in Claude Code:\n\n#### Memory Management Tools",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 1203,
      "example_type": "cli",
      "content": "# Start the REST API server\npython -m greeum.api.memory_api\n\n# Server runs on http://localhost:5000\n# Swagger documentation available at http://localhost:5000/api/v1/docs",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 1214,
      "example_type": "cli",
      "content": "# Health check\ncurl http://localhost:5000/api/v1/health\n\n# System statistics\ncurl http://localhost:5000/api/v1/stats",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 1223,
      "example_type": "cli",
      "content": "# Add memory with quality validation\ncurl -X POST http://localhost:5000/api/v1/memories \\\n  -H \"Content-Type: application/json\" \\\n  -d '{\n    \"content\": \"Implemented new caching system that improved API response time by 40%\",\n    \"keywords\": [\"caching\", \"performance\", \"api\"],\n    \"importance\": 0.8,\n    \"validate_quality\": true\n  }'\n\n# Search memories (hybrid approach)\ncurl \"http://localhost:5000/api/v1/memories/search?q=caching%20performance&method=hybrid&limit=5\"\n\n# Get memory by ID\ncurl http://localhost:5000/api/v1/memories/123",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 1242,
      "example_type": "cli",
      "content": "# Validate content quality\ncurl -X POST http://localhost:5000/api/v1/quality/validate \\\n  -H \"Content-Type: application/json\" \\\n  -d '{\"content\": \"Content to validate\", \"importance\": 0.7}'\n\n# Check for duplicates\ncurl -X POST http://localhost:5000/api/v1/quality/duplicates \\\n  -H \"Content-Type: application/json\" \\\n  -d '{\"content\": \"Content to check for duplicates\"}'\n\n# Get usage analytics\ncurl \"http://localhost:5000/api/v1/analytics?days=30&detailed=true\"",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 55,
      "example_type": "python",
      "content": "from greeum import BlockManager, STMManager, PromptWrapper\nfrom greeum.core.quality_validator import QualityValidator\nfrom greeum.core.duplicate_detector import DuplicateDetector\n\n# Initialize core memory components\nblock_manager = BlockManager()\nstm_manager = STMManager(default_ttl=3600)  # 1 hour TTL\nprompt_wrapper = PromptWrapper()\n\n# Initialize v2.0.5 quality features\nquality_validator = QualityValidator()\nduplicate_detector = DuplicateDetector(similarity_threshold=0.85)\n\nprint(\"Greeum v2.0.5 initialized with quality validation!\")",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 78,
      "example_type": "python",
      "content": "from greeum import BlockManager\nfrom greeum.core.quality_validator import QualityValidator\nfrom greeum.core.duplicate_detector import DuplicateDetector\nfrom greeum.text_utils import process_user_input\n\n# Initialize components\nblock_manager = BlockManager()\nquality_validator = QualityValidator()\nduplicate_detector = DuplicateDetector()\n\n# Memory content\ncontent = \"Started a new machine learning project focused on developing an image recognition system using deep learning algorithms. The goal is to achieve 95% accuracy for medical diagnosis applications.\"\n\n# Step 1: Validate quality before storing\nquality_result = quality_validator.validate_memory_quality(content, importance=0.8)\n\nprint(f\"Quality Score: {quality_result['quality_score']:.3f}\")\nprint(f\"Quality Level: {quality_result['quality_level']}\")\nprint(f\"Suggestions: {quality_result['suggestions']}\")\n\n# Step 2: Check for duplicates\nduplicate_result = duplicate_detector.check_duplicates(content)\n\nif duplicate_result['is_duplicate']:\n    print(f\"⚠️ Similar memory found with {duplicate_result['max_similarity']:.3f} similarity\")\nelse:\n    print(\"✅ No duplicates found\")\n\n# Step 3: Store memory if quality is acceptable\nif quality_result['quality_score'] >= 0.6 and not duplicate_result['is_duplicate']:\n    processed = process_user_input(content)\n    \n    block = block_manager.add_block(\n        context=processed[\"context\"],\n        keywords=processed[\"keywords\"],\n        tags=processed[\"tags\"],\n        embedding=processed[\"embedding\"],\n        importance=0.8\n    )\n    \n    print(f\"✅ Memory stored successfully! Block index: {block['block_index']}\")\nelse:\n    print(\"❌ Memory not stored due to quality/duplicate issues\")",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 126,
      "example_type": "python",
      "content": "# Keyword search\nkeyword_results = block_manager.search_by_keywords(\n    keywords=[\"machine learning\", \"project\", \"image\"],\n    limit=5\n)\n\nprint(f\"Keyword search results: {len(keyword_results)}\")\nfor result in keyword_results:\n    print(f\"Block {result['block_index']}: {result['context'][:60]}...\")\n\n# Vector similarity search\nfrom greeum.embedding_models import get_embedding\n\nquery = \"Tell me about AI projects for medical applications\"\nquery_embedding = get_embedding(query)\n\nsimilarity_results = block_manager.search_by_embedding(\n    query_embedding, \n    top_k=5\n)\n\nprint(f\"\\nSimilarity search results: {len(similarity_results)}\")\nfor result in similarity_results:\n    print(f\"Score: {result.get('similarity', 'N/A'):.3f} - {result['context'][:60]}...\")",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 159,
      "example_type": "python",
      "content": "from greeum.core.quality_validator import QualityValidator\n\nvalidator = QualityValidator()\n\n# Test different content quality levels\ntest_contents = [\n    \"Good\",  # Too short\n    \"Attended team meeting about Q4 roadmap, resource allocation, and timeline adjustments. Discussed budget constraints and identified key milestones for product launch.\",  # High quality\n    \"meeting stuff happened\",  # Low quality\n    \"Today I successfully implemented the new authentication system using JWT tokens, integrated it with the existing user database, tested all edge cases, and documented the API endpoints for the development team.\"  # Very high quality\n]\n\nfor i, content in enumerate(test_contents, 1):\n    print(f\"\\n--- Test Content {i} ---\")\n    print(f\"Content: {content}\")\n    \n    result = validator.validate_memory_quality(content)\n    \n    print(f\"Quality Score: {result['quality_score']:.3f}\")\n    print(f\"Quality Level: {result['quality_level']}\")\n    print(f\"Quality Factors:\")\n    \n    for factor, score in result['quality_factors'].items():\n        print(f\"  {factor}: {score:.2f}\")\n    \n    if result['suggestions']:\n        print(f\"Suggestions: {', '.join(result['suggestions'])}\")",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 191,
      "example_type": "python",
      "content": "from greeum.core.duplicate_detector import DuplicateDetector\n\ndetector = DuplicateDetector(similarity_threshold=0.85)\n\n# Add initial memory\ninitial_content = \"Working on machine learning project for image classification\"\nblock_manager.add_block(\n    context=initial_content,\n    keywords=[\"machine\", \"learning\", \"image\", \"classification\"]\n)\n\n# Test for duplicates\nsimilar_contents = [\n    \"Working on ML project for image classification\",  # Very similar\n    \"Developing image classification using machine learning\",  # Similar concept\n    \"Started a cooking tutorial project\",  # Different topic\n]\n\nfor content in similar_contents:\n    result = detector.check_duplicates(content)\n    \n    print(f\"\\nContent: {content}\")\n    print(f\"Is duplicate: {result['is_duplicate']}\")\n    print(f\"Max similarity: {result['max_similarity']:.3f}\")\n    \n    if result['similar_memories']:\n        print(f\"Found {len(result['similar_memories'])} similar memories\")",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 223,
      "example_type": "python",
      "content": "from greeum import STMManager\n\n# Initialize STM with custom TTL\nstm_manager = STMManager(default_ttl=3600)  # 1 hour\n\n# Add short-term memories with different TTLs\nmemories = [\n    {\"content\": \"Meeting scheduled for 3 PM today\", \"ttl\": 3600},      # 1 hour\n    {\"content\": \"Project deadline is next Friday\", \"ttl\": 86400},     # 1 day  \n    {\"content\": \"New ML algorithm achieved 98.5% accuracy\", \"ttl\": 604800}  # 1 week\n]\n\nfor memory in memories:\n    memory_data = {\n        \"id\": f\"stm_{hash(memory['content']) % 10000}\",\n        \"content\": memory[\"content\"],\n        \"importance\": 0.7\n    }\n    \n    stm_manager.add_memory(memory_data, ttl=memory[\"ttl\"])\n    print(f\"Added STM: {memory['content']} (TTL: {memory['ttl']}s)\")\n\n# Retrieve recent memories\nrecent = stm_manager.get_recent_memories(count=5)\nprint(f\"\\nRecent STM entries: {len(recent)}\")\n\nfor mem in recent:\n    print(f\"- {mem['content']} (importance: {mem.get('importance', 'N/A')})\")",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 260,
      "example_type": "python",
      "content": "from greeum.core.quality_validator import QualityValidator\n\nvalidator = QualityValidator()\nresult = validator.validate_memory_quality(\n    \"Comprehensive project analysis completed with detailed findings and recommendations\"\n)\n\nprint(f\"Quality Score: {result['quality_score']:.3f}\")\nprint(f\"Quality Level: {result['quality_level']}\")\n# Output:\n# Quality Score: 0.847\n# Quality Level: good",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 277,
      "example_type": "python",
      "content": "from greeum.core.usage_analytics import UsageAnalytics\n\nanalytics = UsageAnalytics()\nstats = analytics.get_usage_statistics(days=30)\n\nprint(f\"Total Events: {stats['total_events']}\")\nprint(f\"Success Rate: {stats['success_rate']:.1%}\")\n# Access via Python API for detailed analytics",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 360,
      "example_type": "python",
      "content": "# In Claude Code, these tools are available directly:\n\n# Add new memory\nadd_memory(\n    content=\"Completed implementation of user authentication system\",\n    keywords=[\"authentication\", \"implementation\", \"completed\"],\n    importance=0.9\n)\n\n# Search memories  \nsearch_memory(\n    query=\"authentication system\",\n    search_type=\"hybrid\",  # keyword, embedding, or hybrid\n    limit=10\n)\n\n# Get system statistics\nget_memory_stats(\n    include_quality=True,\n    include_performance=True\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 385,
      "example_type": "python",
      "content": "# Validate memory quality\nquality_check(\n    content=\"Memory content to validate for quality assessment\",\n    importance=0.7\n)\n\n# Check for duplicates\ncheck_duplicates(\n    content=\"Content to check for similar existing memories\",\n    threshold=0.85\n)\n\n# Get usage analytics\nusage_analytics(\n    days=30,\n    detailed=True,\n    include_trends=True\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 407,
      "example_type": "python",
      "content": "# Analyze LTM patterns\nltm_analyze(\n    period=\"30d\",\n    trends=True,\n    output=\"text\"  # or \"json\"\n)\n\n# Verify LTM integrity\nltm_verify(\n    repair=False  # Set to True to attempt repairs\n)\n\n# Export LTM data\nltm_export(\n    format=\"json\",  # \"json\", \"csv\", or \"blockchain\"\n    limit=1000\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 428,
      "example_type": "python",
      "content": "# Add STM entry\nstm_add(\n    content=\"Temporary information for current session\",\n    ttl=\"2h\",\n    importance=0.6\n)\n\n# Promote STM to LTM\nstm_promote(\n    threshold=0.8,\n    dry_run=False\n)\n\n# Clean up STM\nstm_cleanup(\n    expired=True,\n    smart=True,\n    threshold=0.3\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 457,
      "example_type": "python",
      "content": "from greeum import TemporalReasoner\n\n# Initialize temporal reasoner\ntemporal_reasoner = TemporalReasoner()\n\n# Test various time expressions\ntime_queries = [\n    \"What did I work on yesterday?\",\n    \"Show me tasks from last week\",\n    \"Find memories from 3 days ago\",\n    \"어제 회의에서 뭘 결정했지?\",  # Korean\n    \"昨日の作業内容を教えて\",        # Japanese\n    \"上周的项目进展如何？\"         # Chinese\n]\n\nfor query in time_queries:\n    print(f\"\\nQuery: {query}\")\n    \n    # Search with temporal reasoning\n    results = temporal_reasoner.search_by_time(query, top_k=5)\n    \n    print(f\"Language detected: {results.get('language', 'auto')}\")\n    print(f\"Time expression found: {results.get('time_reference', 'none')}\")\n    print(f\"Results: {len(results.get('blocks', []))} memories found\")\n    \n    # Display results\n    for block in results.get('blocks', [])[:2]:  # Show first 2\n        timestamp = block.get('timestamp', 'Unknown')\n        content = block.get('context', '')[:50] + '...'\n        print(f\"  [{timestamp}] {content}\")",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 492,
      "example_type": "python",
      "content": "from datetime import datetime, timedelta\n\n# Search within specific time range\nend_date = datetime.now()\nstart_date = end_date - timedelta(days=7)  # Last 7 days\n\nrange_results = block_manager.get_blocks_by_time_range(\n    start_date=start_date,\n    end_date=end_date,\n    limit=20\n)\n\nprint(f\"Memories from last 7 days: {len(range_results)}\")\n\n# Group by day\nfrom collections import defaultdict\n\nmemories_by_day = defaultdict(list)\nfor block in range_results:\n    day = block['timestamp'][:10]  # YYYY-MM-DD\n    memories_by_day[day].append(block)\n\nfor day, day_memories in sorted(memories_by_day.items()):\n    print(f\"\\n{day}: {len(day_memories)} memories\")\n    for memory in day_memories[:2]:  # Show first 2 per day\n        print(f\"  - {memory['context'][:40]}...\")",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 527,
      "example_type": "python",
      "content": "from greeum.text_utils import detect_language, extract_keywords\nfrom greeum import BlockManager\n\nblock_manager = BlockManager()\n\n# Multi-language content examples\nmultilingual_content = [\n    {\"text\": \"오늘 머신러닝 프로젝트 회의를 했습니다.\", \"expected\": \"ko\"},\n    {\"text\": \"We had a machine learning project meeting today.\", \"expected\": \"en\"},\n    {\"text\": \"今日は機械学習プロジェクトの会議をしました。\", \"expected\": \"ja\"},\n    {\"text\": \"今天我们开了机器学习项目会议。\", \"expected\": \"zh\"},\n    {\"text\": \"프로젝트 meeting was very productive today.\", \"expected\": \"mixed\"}\n]\n\nfor item in multilingual_content:\n    text = item[\"text\"]\n    \n    # Detect language\n    detected_lang = detect_language(text)\n    \n    # Extract keywords with auto-detection\n    keywords = extract_keywords(text, language=\"auto\")\n    \n    print(f\"\\nText: {text}\")\n    print(f\"Expected: {item['expected']}, Detected: {detected_lang}\")\n    print(f\"Keywords: {keywords}\")\n    \n    # Store memory with detected language metadata\n    block_manager.add_block(\n        context=text,\n        keywords=keywords,\n        tags=[\"multilingual\", \"meeting\"],\n        importance=0.7,\n        metadata={\"language\": detected_lang}\n    )",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 567,
      "example_type": "python",
      "content": "# Search across different languages\nsearch_queries = [\n    \"machine learning meeting\",  # English\n    \"머신러닝 회의\",              # Korean\n    \"機械学習 会議\",              # Japanese\n    \"机器学习 会议\"               # Chinese\n]\n\nfor query in search_queries:\n    print(f\"\\nSearching for: {query}\")\n    \n    # Perform semantic search (works across languages)\n    from greeum.embedding_models import get_embedding\n    \n    query_embedding = get_embedding(query)\n    results = block_manager.search_by_embedding(query_embedding, top_k=3)\n    \n    print(f\"Found {len(results)} results:\")\n    for result in results:\n        lang = result.get('metadata', {}).get('language', 'unknown')\n        print(f\"  [{lang}] {result['context'][:50]}...\")",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 593,
      "example_type": "python",
      "content": "# Multi-language temporal expression examples\ntime_expressions = {\n    \"Korean\": [\n        \"어제 회의에서 결정한 사항\",\n        \"3일 전에 작성한 문서\", \n        \"지난주 프로젝트 진행상황\",\n        \"이번 달 목표 설정\"\n    ],\n    \"English\": [\n        \"yesterday's meeting decisions\",\n        \"document written 3 days ago\",\n        \"last week's project progress\", \n        \"this month's goal setting\"\n    ],\n    \"Japanese\": [\n        \"昨日の会議での決定事項\",\n        \"3日前に作成した文書\",\n        \"先週のプロジェクト進捗\",\n        \"今月の目標設定\"\n    ],\n    \"Chinese\": [\n        \"昨天会议的决定\",\n        \"3天前写的文档\", \n        \"上周的项目进展\",\n        \"本月的目标设定\"\n    ]\n}\n\nfor language, expressions in time_expressions.items():\n    print(f\"\\n{language} temporal expressions:\")\n    for expr in expressions:\n        # Search using temporal reasoning\n        results = temporal_reasoner.search_by_time(expr, top_k=3)\n        \n        print(f\"  Query: '{expr}'\")\n        print(f\"  Time reference detected: {results.get('time_reference', 'none')}\")\n        print(f\"  Results found: {len(results.get('blocks', []))}\")\n    print(\"-\" * 60)",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 640,
      "example_type": "python",
      "content": "from greeum import BlockManager, STMManager, CacheManager, PromptWrapper\nfrom greeum.core.quality_validator import QualityValidator\nfrom greeum.embedding_models import get_embedding\n\n# Initialize system with quality validation\nblock_manager = BlockManager()\nstm_manager = STMManager()\ncache_manager = CacheManager(block_manager=block_manager)\nquality_validator = QualityValidator()\nprompt_wrapper = PromptWrapper(cache_manager=cache_manager, stm_manager=stm_manager)\n\n# Add some high-quality memories\nmemories = [\n    {\n        \"context\": \"Successfully implemented authentication system using JWT tokens with refresh mechanism. Integrated with existing user database, added rate limiting, and comprehensive error handling.\",\n        \"keywords\": [\"authentication\", \"JWT\", \"security\", \"implementation\"],\n        \"importance\": 0.9\n    },\n    {\n        \"context\": \"Client requested prototype delivery by next Friday. Scope includes user login, dashboard, and basic CRUD operations. Team allocated: 2 developers, 1 designer.\",\n        \"keywords\": [\"client\", \"prototype\", \"deadline\", \"scope\"],\n        \"importance\": 0.8\n    }\n]\n\nfor memory in memories:\n    # Validate quality before storing\n    quality_result = quality_validator.validate_memory_quality(\n        memory[\"context\"], \n        importance=memory[\"importance\"]\n    )\n    \n    if quality_result[\"quality_score\"] >= 0.7:\n        block_manager.add_block(\n            context=memory[\"context\"],\n            keywords=memory[\"keywords\"],\n            tags=[\"work\", \"development\"],\n            embedding=get_embedding(memory[\"context\"]),\n            importance=memory[\"importance\"]\n        )\n        print(f\"✅ Added memory (quality: {quality_result['quality_score']:.3f})\")\n\n# Add short-term context\nstm_memory = {\n    \"id\": \"current_session\",\n    \"content\": \"User is asking about project status. Show recent developments and upcoming deadlines.\",\n    \"importance\": 0.7\n}\nstm_manager.add_memory(stm_memory)\n\n# Generate enhanced prompt\nuser_question = \"What's the current status of our development project?\"\n\n# Update cache with current context\nquestion_embedding = get_embedding(user_question)\ncache_manager.update_cache(\n    query_text=user_question,\n    query_embedding=question_embedding,\n    query_keywords=[\"project\", \"status\", \"development\"]\n)\n\n# Compose prompt with memory context\nenhanced_prompt = prompt_wrapper.compose_prompt(\n    user_input=user_question,\n    include_stm=True,\n    max_context_length=2000\n)\n\nprint(\"\\n=== Enhanced Prompt with Memory Context ===\")\nprint(enhanced_prompt)\nprint(\"\\n\" + \"=\" * 50)\n\n# Simulate LLM response processing\nllm_response = \"Based on the current project status, we have successfully implemented the authentication system and are on track for the prototype delivery by next Friday.\"\n\n# Store the interaction as a new memory\ninteraction_context = f\"User asked: {user_question}\\nResponse: {llm_response}\"\ninteraction_quality = quality_validator.validate_memory_quality(interaction_context)\n\nif interaction_quality[\"quality_score\"] >= 0.6:\n    block_manager.add_block(\n        context=interaction_context,\n        keywords=[\"interaction\", \"status\", \"update\"],\n        tags=[\"conversation\", \"project\"],\n        embedding=get_embedding(interaction_context),\n        importance=0.7\n    )\n    print(f\"💾 Stored interaction (quality: {interaction_quality['quality_score']:.3f})\")",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 733,
      "example_type": "python",
      "content": "class IntelligentAgent:\n    \"\"\"An AI agent with persistent memory using Greeum\"\"\"\n    \n    def __init__(self, agent_name: str):\n        self.name = agent_name\n        self.block_manager = BlockManager()\n        self.stm_manager = STMManager()\n        self.cache_manager = CacheManager(self.block_manager)\n        self.prompt_wrapper = PromptWrapper(self.cache_manager, self.stm_manager)\n        self.quality_validator = QualityValidator()\n    \n    def learn(self, information: str, importance: float = 0.7, tags: list = None):\n        \"\"\"Learn new information with quality validation\"\"\"\n        quality_result = self.quality_validator.validate_memory_quality(\n            information, importance=importance\n        )\n        \n        if quality_result[\"quality_score\"] >= 0.5:\n            from greeum.text_utils import process_user_input\n            processed = process_user_input(information)\n            \n            self.block_manager.add_block(\n                context=processed[\"context\"],\n                keywords=processed[\"keywords\"],\n                tags=tags or processed[\"tags\"],\n                embedding=processed[\"embedding\"],\n                importance=importance\n            )\n            \n            return f\"✅ Learned: {information[:50]}... (Quality: {quality_result['quality_score']:.3f})\"\n        else:\n            return f\"❌ Information quality too low ({quality_result['quality_score']:.3f})\"\n    \n    def remember(self, query: str, max_memories: int = 5):\n        \"\"\"Remember relevant information based on query\"\"\"\n        query_embedding = get_embedding(query)\n        \n        # Update cache with current query context\n        from greeum.text_utils import extract_keywords\n        keywords = extract_keywords(query)\n        \n        self.cache_manager.update_cache(\n            query_text=query,\n            query_embedding=query_embedding,\n            query_keywords=keywords\n        )\n        \n        # Get relevant memories\n        relevant_memories = self.cache_manager.get_relevant_memories(limit=max_memories)\n        \n        return relevant_memories\n    \n    def think(self, user_input: str):\n        \"\"\"Generate contextual response using memory\"\"\"\n        # Remember relevant information\n        memories = self.remember(user_input)\n        \n        # Add current input to short-term memory\n        stm_entry = {\n            \"id\": f\"input_{hash(user_input) % 10000}\",\n            \"content\": user_input,\n            \"importance\": 0.6\n        }\n        self.stm_manager.add_memory(stm_entry)\n        \n        # Generate enhanced prompt\n        prompt = self.prompt_wrapper.compose_prompt(\n            user_input=user_input,\n            include_stm=True,\n            max_context_length=1500\n        )\n        \n        return {\n            \"prompt\": prompt,\n            \"relevant_memories\": len(memories),\n            \"memory_context\": [mem[\"context\"][:100] + \"...\" for mem in memories[:3]]\n        }\n\n# Example usage\nagent = IntelligentAgent(\"DevAssistant\")\n\n# Teach the agent\nlearning_results = [\n    agent.learn(\"Python FastAPI framework is excellent for building REST APIs with automatic OpenAPI documentation.\", importance=0.8, tags=[\"python\", \"api\", \"documentation\"]),\n    agent.learn(\"JWT tokens should be stored securely and have reasonable expiration times for security.\", importance=0.9, tags=[\"security\", \"jwt\", \"best-practices\"]),\n    agent.learn(\"Code reviews improve code quality and help knowledge sharing among team members.\", importance=0.7, tags=[\"development\", \"quality\", \"teamwork\"])\n]\n\nfor result in learning_results:\n    print(result)\n\n# Ask the agent something\nuser_question = \"How should I implement secure API authentication?\"\nthought_process = agent.think(user_question)\n\nprint(f\"\\n🤔 Thinking about: {user_question}\")\nprint(f\"📚 Relevant memories found: {thought_process['relevant_memories']}\")\nprint(f\"🧠 Memory context preview:\")\nfor i, context in enumerate(thought_process['memory_context'], 1):\n    print(f\"  {i}. {context}\")\n\nprint(f\"\\n📝 Generated prompt:\")\nprint(thought_process['prompt'])",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 841,
      "example_type": "python",
      "content": "# Define custom prompt templates for different use cases\n\n# Technical Assistant Template\ntech_template = \"\"\"\nYou are an expert technical assistant with persistent memory.\n\nRELEVANT TECHNICAL KNOWLEDGE:\n{memory_blocks}\n\nRECENT CONTEXT:\n{short_term_memories}\n\nUSER QUERY: {user_input}\n\nProvide a detailed technical response based on your knowledge and context. Include:\n1. Direct answer to the question\n2. Relevant technical details\n3. Best practices or recommendations\n4. Related concepts from your memory\n\"\"\"\n\n# Creative Assistant Template  \ncreative_template = \"\"\"\nYou are a creative assistant with rich experiential memory.\n\nINSPIRATIONAL MEMORIES:\n{memory_blocks}\n\nCURRENT SESSION CONTEXT:\n{short_term_memories}\n\nCREATIVE REQUEST: {user_input}\n\nDraw upon your memories to provide a creative, innovative response. Consider:\n- Past successful approaches\n- Creative patterns and techniques\n- Unexpected connections between ideas\n- Lessons learned from previous projects\n\"\"\"\n\n# Project Manager Template\nproject_template = \"\"\"\nYou are an experienced project manager with comprehensive project memory.\n\nPROJECT HISTORY & DECISIONS:\n{memory_blocks}\n\nCURRENT PROJECT STATUS:\n{short_term_memories}\n\nPROJECT QUERY: {user_input}\n\nProvide strategic project guidance considering:\n- Historical project data and outcomes\n- Previous decisions and their results\n- Team capabilities and constraints\n- Risk factors and mitigation strategies\n- Timeline and resource implications\n\"\"\"\n\n# Example: Using different templates\ntemplates = {\n    \"technical\": tech_template,\n    \"creative\": creative_template,\n    \"project\": project_template\n}\n\ndef get_contextual_response(query: str, template_type: str = \"technical\"):\n    \"\"\"Generate response using specific template type\"\"\"\n    \n    # Set the appropriate template\n    template = templates.get(template_type, tech_template) \n    prompt_wrapper.set_template(template)\n    \n    # Generate prompt with memory context\n    enhanced_prompt = prompt_wrapper.compose_prompt(\n        user_input=query,\n        include_stm=True,\n        max_context_length=2000\n    )\n    \n    return enhanced_prompt\n\n# Test different templates\ntest_queries = [\n    {\"query\": \"How can I optimize database queries?\", \"type\": \"technical\"},\n    {\"query\": \"I need creative ideas for user engagement\", \"type\": \"creative\"},\n    {\"query\": \"What's our project timeline looking like?\", \"type\": \"project\"}\n]\n\nfor test in test_queries:\n    print(f\"\\n=== {test['type'].upper()} TEMPLATE ===\")\n    print(f\"Query: {test['query']}\")\n    prompt = get_contextual_response(test[\"query\"], test[\"type\"])\n    print(f\"Generated prompt: {len(prompt)} characters\")\n    print(f\"Preview: {prompt[:200]}...\")",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 947,
      "example_type": "python",
      "content": "from greeum.core.search_engine import SearchEngine, BertReranker\n\n# Initialize advanced search with BERT reranking\ntry:\n    # Optional: Use BERT cross-encoder for better relevance\n    reranker = BertReranker(\"cross-encoder/ms-marco-MiniLM-L-6-v2\")\n    search_engine = SearchEngine(block_manager=block_manager, reranker=reranker)\n    print(\"🚀 Advanced search engine with BERT reranking enabled\")\nexcept ImportError:\n    # Fallback to standard search\n    search_engine = SearchEngine(block_manager=block_manager)\n    print(\"📊 Standard search engine enabled\")\n\n# Perform advanced search\ncomplex_queries = [\n    \"machine learning algorithms for natural language processing\",\n    \"database optimization techniques for large datasets\",\n    \"user authentication security best practices\"\n]\n\nfor query in complex_queries:\n    print(f\"\\n🔍 Searching: {query}\")\n    \n    # Advanced search with timing\n    results = search_engine.search(query, top_k=5)\n    \n    print(f\"📈 Performance metrics:\")\n    print(f\"  - Total time: {results['timing']['total_time']:.0f}ms\")\n    print(f\"  - Vector search: {results['timing']['vector_search']:.0f}ms\")\n    print(f\"  - Reranking: {results['timing'].get('reranking', 0):.0f}ms\")\n    \n    print(f\"📚 Results ({len(results['blocks'])}):\") \n    for i, block in enumerate(results[\"blocks\"][:3], 1):\n        relevance = block.get(\"relevance_score\", \"N/A\")\n        print(f\"  {i}. [Score: {relevance}] {block['context'][:80]}...\")",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 987,
      "example_type": "python",
      "content": "from greeum.core.usage_analytics import UsageAnalytics\nimport time\n\n# Initialize analytics system\nanalytics = UsageAnalytics()\n\n# Simulate various operations with logging\noperations = [\n    {\"type\": \"tool_usage\", \"tool\": \"add_memory\", \"duration\": 120, \"success\": True},\n    {\"type\": \"tool_usage\", \"tool\": \"search_memory\", \"duration\": 85, \"success\": True},\n    {\"type\": \"tool_usage\", \"tool\": \"quality_check\", \"duration\": 45, \"success\": True},\n    {\"type\": \"tool_usage\", \"tool\": \"search_memory\", \"duration\": 95, \"success\": False},\n    {\"type\": \"system_event\", \"tool\": \"optimization\", \"duration\": 300, \"success\": True},\n]\n\nfor op in operations:\n    analytics.log_event(\n        event_type=op[\"type\"],\n        tool_name=op[\"tool\"],\n        duration_ms=op[\"duration\"],\n        success=op[\"success\"],\n        metadata={\"simulated\": True}\n    )\n    time.sleep(0.1)  # Small delay between operations\n\n# Get comprehensive usage statistics\nstats = analytics.get_usage_statistics(days=7)\n\nprint(\"📊 Usage Analytics Report:\")\nprint(f\"  Total Events: {stats['total_events']}\")\nprint(f\"  Unique Sessions: {stats['unique_sessions']}\")\nprint(f\"  Success Rate: {stats['success_rate']*100:.1f}%\")\nprint(f\"  Avg Response Time: {stats['avg_response_time']:.0f}ms\")\n\nif 'tool_usage' in stats:\n    print(f\"\\n🔧 Most Used Tools:\")\n    for tool, count in stats['tool_usage'].items():\n        print(f\"    {tool}: {count} uses\")\n\n# Get quality trends\nquality_trends = analytics.get_quality_trends(days=7)\nif quality_trends:\n    print(f\"\\n📈 Quality Trends:\")\n    print(f\"  Average Quality: {quality_trends['avg_quality_score']:.3f}\")\n    print(f\"  High Quality Ratio: {quality_trends['high_quality_ratio']*100:.1f}%\")",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 1037,
      "example_type": "python",
      "content": "from greeum.core.duplicate_detector import DuplicateDetector\nfrom greeum.core.quality_validator import QualityValidator\n\nclass MemoryOptimizer:\n    \"\"\"Advanced memory system optimization\"\"\"\n    \n    def __init__(self, block_manager, stm_manager):\n        self.block_manager = block_manager\n        self.stm_manager = stm_manager\n        self.duplicate_detector = DuplicateDetector(similarity_threshold=0.85)\n        self.quality_validator = QualityValidator()\n    \n    def optimize_long_term_memory(self, min_quality=0.5):\n        \"\"\"Optimize LTM by removing low-quality and duplicate memories\"\"\"\n        all_blocks = self.block_manager.get_blocks(limit=1000)\n        \n        removed_count = 0\n        duplicate_count = 0\n        low_quality_count = 0\n        \n        print(f\"🔧 Optimizing {len(all_blocks)} memories...\")\n        \n        for block in all_blocks:\n            block_id = block['block_index']\n            content = block['context']\n            \n            # Check quality\n            quality_result = self.quality_validator.validate_memory_quality(content)\n            quality_score = quality_result['quality_score']\n            \n            # Check for duplicates\n            duplicate_result = self.duplicate_detector.check_duplicates(content)\n            \n            should_remove = False\n            reason = \"\"\n            \n            if quality_score < min_quality:\n                should_remove = True\n                reason = f\"low quality ({quality_score:.3f})\"\n                low_quality_count += 1\n            elif duplicate_result['is_duplicate'] and duplicate_result['max_similarity'] > 0.90:\n                should_remove = True\n                reason = f\"duplicate ({duplicate_result['max_similarity']:.3f} similarity)\"\n                duplicate_count += 1\n            \n            if should_remove:\n                # In a real implementation, you'd have a method to remove blocks\n                print(f\"  ❌ Would remove block {block_id}: {reason}\")\n                removed_count += 1\n        \n        print(f\"\\n✅ Optimization complete:\")\n        print(f\"  - Low quality removed: {low_quality_count}\")\n        print(f\"  - Duplicates removed: {duplicate_count}\")\n        print(f\"  - Total removed: {removed_count}\")\n        print(f\"  - Remaining: {len(all_blocks) - removed_count}\")\n        \n        return {\n            \"total_processed\": len(all_blocks),\n            \"removed\": removed_count,\n            \"low_quality\": low_quality_count,\n            \"duplicates\": duplicate_count\n        }\n    \n    def optimize_short_term_memory(self, importance_threshold=0.8):\n        \"\"\"Promote important STM entries to LTM\"\"\"\n        stm_memories = self.stm_manager.get_recent_memories(count=100)\n        \n        promoted_count = 0\n        \n        for memory in stm_memories:\n            importance = memory.get('importance', 0.5)\n            \n            if importance >= importance_threshold:\n                # Convert STM to LTM format\n                from greeum.text_utils import process_user_input\n                processed = process_user_input(memory['content'])\n                \n                self.block_manager.add_block(\n                    context=processed[\"context\"],\n                    keywords=processed[\"keywords\"],\n                    tags=processed[\"tags\"] + [\"promoted_from_stm\"],\n                    embedding=processed[\"embedding\"],\n                    importance=importance\n                )\n                \n                promoted_count += 1\n                print(f\"⬆️ Promoted to LTM: {memory['content'][:50]}... (importance: {importance:.2f})\")\n        \n        print(f\"\\n📈 STM Optimization: {promoted_count} memories promoted to LTM\")\n        return promoted_count\n\n# Example usage\noptimizer = MemoryOptimizer(block_manager, stm_manager)\n\nprint(\"=== Memory System Optimization ===\")\nltm_results = optimizer.optimize_long_term_memory(min_quality=0.6)\nstm_results = optimizer.optimize_short_term_memory(importance_threshold=0.7)\n\nprint(f\"\\n📊 Optimization Summary:\")\nprint(f\"  LTM processed: {ltm_results['total_processed']} memories\")\nprint(f\"  LTM optimized: {ltm_results['removed']} removed\")\nprint(f\"  STM promoted: {stm_results} memories\")",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 1145,
      "example_type": "python",
      "content": "# Production-ready configuration example\nimport os\nfrom greeum import BlockManager, STMManager\nfrom greeum.core import DatabaseManager\n\n# Environment-based configuration\nclass ProductionGreeumConfig:\n    def __init__(self):\n        self.data_dir = os.getenv('GREEUM_DATA_DIR', '/opt/greeum/data')\n        self.db_type = os.getenv('GREEUM_DB_TYPE', 'sqlite')\n        self.log_level = os.getenv('GREEUM_LOG_LEVEL', 'INFO')\n        self.quality_threshold = float(os.getenv('GREEUM_QUALITY_THRESHOLD', '0.7'))\n        self.duplicate_threshold = float(os.getenv('GREEUM_DUPLICATE_THRESHOLD', '0.85'))\n        \n        # Database configuration\n        if self.db_type == 'postgresql':\n            self.connection_string = os.getenv('GREEUM_CONNECTION_STRING')\n        else:\n            self.connection_string = os.path.join(self.data_dir, 'memory.db')\n    \n    def initialize_system(self):\n        \"\"\"Initialize production Greeum system\"\"\"\n        # Ensure data directory exists\n        os.makedirs(self.data_dir, exist_ok=True)\n        \n        # Initialize database manager\n        db_manager = DatabaseManager(\n            connection_string=self.connection_string,\n            db_type=self.db_type\n        )\n        \n        # Initialize components with production settings\n        block_manager = BlockManager(db_manager=db_manager)\n        stm_manager = STMManager(\n            db_manager=db_manager,\n            default_ttl=3600  # 1 hour default\n        )\n        \n        print(f\"✅ Greeum production system initialized\")\n        print(f\"   Data directory: {self.data_dir}\")\n        print(f\"   Database type: {self.db_type}\")\n        print(f\"   Quality threshold: {self.quality_threshold}\")\n        \n        return block_manager, stm_manager\n\n# Usage\nconfig = ProductionGreeumConfig()\nblock_manager, stm_manager = config.initialize_system()",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 1260,
      "example_type": "python",
      "content": "import requests\nimport json\nfrom typing import List, Dict, Optional\n\nclass GreeumAPIClient:\n    \"\"\"Professional Python client for Greeum v2.0.5 API\"\"\"\n    \n    def __init__(self, base_url: str = \"http://localhost:5000/api/v1\", api_key: Optional[str] = None):\n        self.base_url = base_url\n        self.session = requests.Session()\n        \n        if api_key:\n            self.session.headers.update({\"Authorization\": f\"Bearer {api_key}\"})\n    \n    def add_memory(self, content: str, keywords: List[str] = None, \n                   importance: float = 0.7, validate_quality: bool = True) -> Dict:\n        \"\"\"Add new memory with optional quality validation\"\"\"\n        data = {\n            \"content\": content,\n            \"keywords\": keywords or [],\n            \"importance\": importance,\n            \"validate_quality\": validate_quality\n        }\n        \n        response = self.session.post(f\"{self.base_url}/memories\", json=data)\n        response.raise_for_status()\n        return response.json()\n    \n    def search_memories(self, query: str, method: str = \"hybrid\", \n                       limit: int = 10, min_quality: float = None) -> Dict:\n        \"\"\"Search memories using various methods\"\"\"\n        params = {\n            \"q\": query,\n            \"method\": method,  # keyword, embedding, hybrid\n            \"limit\": limit\n        }\n        \n        if min_quality:\n            params[\"min_quality\"] = min_quality\n        \n        response = self.session.get(f\"{self.base_url}/memories/search\", params=params)\n        response.raise_for_status()\n        return response.json()\n    \n    def validate_quality(self, content: str, importance: float = 0.7) -> Dict:\n        \"\"\"Validate content quality\"\"\"\n        data = {\"content\": content, \"importance\": importance}\n        response = self.session.post(f\"{self.base_url}/quality/validate\", json=data)\n        response.raise_for_status()\n        return response.json()\n    \n    def check_duplicates(self, content: str, threshold: float = 0.85) -> Dict:\n        \"\"\"Check for duplicate content\"\"\"\n        data = {\"content\": content, \"threshold\": threshold}\n        response = self.session.post(f\"{self.base_url}/quality/duplicates\", json=data)\n        response.raise_for_status()\n        return response.json()\n    \n    def get_analytics(self, days: int = 7, detailed: bool = False) -> Dict:\n        \"\"\"Get usage analytics\"\"\"\n        params = {\"days\": days, \"detailed\": detailed}\n        response = self.session.get(f\"{self.base_url}/analytics\", params=params)\n        response.raise_for_status()\n        return response.json()\n    \n    def get_system_stats(self) -> Dict:\n        \"\"\"Get system statistics\"\"\"\n        response = self.session.get(f\"{self.base_url}/stats\")\n        response.raise_for_status()\n        return response.json()\n\n# Example usage\nclient = GreeumAPIClient()\n\n# Add high-quality memory\nprint(\"Adding memory...\")\nmemory_result = client.add_memory(\n    content=\"Successfully implemented distributed caching system using Redis cluster. Achieved 40% performance improvement in API response times and 60% reduction in database load.\",\n    keywords=[\"redis\", \"caching\", \"performance\", \"distributed\"],\n    importance=0.9,\n    validate_quality=True\n)\n\nprint(f\"✅ Memory added: {memory_result['success']}\")\nif 'quality_score' in memory_result:\n    print(f\"📊 Quality score: {memory_result['quality_score']:.3f}\")\n\n# Search with different methods\nprint(\"\\n🔍 Searching memories...\")\nsearch_methods = [\"keyword\", \"embedding\", \"hybrid\"]\n\nfor method in search_methods:\n    results = client.search_memories(\n        query=\"caching performance optimization\",\n        method=method,\n        limit=3\n    )\n    \n    print(f\"\\n{method.upper()} search: {len(results.get('memories', []))} results\")\n    for i, memory in enumerate(results.get('memories', [])[:2], 1):\n        score = memory.get('relevance_score', 'N/A')\n        print(f\"  {i}. [Score: {score}] {memory['content'][:60]}...\")\n\n# Get analytics\nprint(\"\\n📈 System Analytics:\")\nanalytics = client.get_analytics(days=30, detailed=True)\nprint(f\"Total memories: {analytics.get('total_memories', 'N/A')}\")\nprint(f\"Average quality: {analytics.get('avg_quality_score', 'N/A')}\")\nprint(f\"Search performance: {analytics.get('avg_search_time', 'N/A')}ms\")\n\n# Validate content quality\nprint(\"\\n🔍 Quality validation:\")\ntest_content = \"This is a very short text.\"\nquality_result = client.validate_quality(test_content)\nprint(f\"Quality score: {quality_result['quality_score']:.3f}\")\nprint(f\"Suggestions: {', '.join(quality_result.get('suggestions', []))}\")",
      "expected_output": null
    },
    {
      "file_path": "docs/tutorials.md",
      "line_number": 334,
      "example_type": "json",
      "content": "   {\n     \"mcpServers\": {\n       \"greeum\": {\n         \"command\": \"python3\",\n         \"args\": [\"-m\", \"greeum.mcp.claude_code_mcp_server\"],\n         \"env\": {\n           \"GREEUM_DATA_DIR\": \"/path/to/your/data\",\n           \"GREEUM_LOG_LEVEL\": \"INFO\"\n         }\n       }\n     }\n   }\n   ```\n\n3. **Verify Connection**:\n   ```bash\n   claude mcp list\n   # Should show: greeum - ✓ Connected\n   ```\n\n### Using MCP Tools in Claude Code\n\nOnce configured, you can use these 12 MCP tools in Claude Code:\n\n#### Memory Management Tools",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_actant_design.md",
      "line_number": 11,
      "example_type": "python",
      "content": "{\n    \"name\": \"add_memory\", \n    \"description\": \"Add important permanent memories to long-term storage.\",\n    \"parameters\": {\n        \"content\": {\"description\": \"Content to store in memory\"},\n        \"importance\": {\"description\": \"Importance score (0.0-1.0)\"}\n    }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_actant_design.md",
      "line_number": 23,
      "example_type": "python",
      "content": "{\n    \"name\": \"add_memory\",\n    \"description\": \"Record [SUBJECT-ACTION-OBJECT] structured memory. MANDATORY format: '[주체-행동-객체] 구체적 내용'. Examples: '[사용자-요청-기능개선]', '[Claude-발견-버그]', '[팀-결정-아키텍처]'\",\n    \"parameters\": {\n        \"content\": {\n            \"description\": \"MUST start with '[Subject-Action-Object]' pattern. Subject: who performed action (사용자/Claude/팀/시스템). Action: specific verb (요청/발견/결정/구현/테스트). Object: target of action. Required format: '[주체-행동-객체] detailed description 1-2 sentences'\",\n            \"pattern\": \"^\\\\[\\\\w+-\\\\w+-\\\\w+\\\\].*\"\n        },\n        \"importance\": {\"description\": \"Importance score (0.0-1.0)\"}\n    }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_actant_design.md",
      "line_number": 48,
      "example_type": "python",
      "content": "def validate_actant_format(content: str) -> ActantValidation:\n    \"\"\"Validate and extract actant components\"\"\"\n    pattern = r'^\\[(\\w+)-(\\w+)-(\\w+)\\]\\s*(.+)$'\n    match = re.match(pattern, content)\n    \n    if not match:\n        raise ValueError(\"Content must start with [Subject-Action-Object] format\")\n    \n    subject, action, object_target, description = match.groups()\n    \n    return ActantValidation(\n        subject=subject,\n        action=action, \n        object_target=object_target,\n        description=description,\n        is_valid=True\n    )",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_actant_design.md",
      "line_number": 69,
      "example_type": "python",
      "content": "class RelationshipExtractor:\n    \"\"\"Extract relationships and causality from actant-structured memories\"\"\"\n    \n    def extract_relationships(self, memories: List[ActantMemory]) -> RelationshipGraph:\n        \"\"\"Build relationship graph from actant patterns\"\"\"\n        graph = RelationshipGraph()\n        \n        for memory in memories:\n            # Subject-Subject relationships (who works with whom)\n            subject_relations = self._find_subject_relationships(memory, memories)\n            \n            # Action-Action causality (what actions lead to other actions)  \n            action_causality = self._find_action_causality(memory, memories)\n            \n            # Object-Object dependencies (what objects are related)\n            object_dependencies = self._find_object_dependencies(memory, memories)\n            \n            graph.add_relationships(subject_relations, action_causality, object_dependencies)\n            \n        return graph",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_compatible_design.md",
      "line_number": 34,
      "example_type": "python",
      "content": "# 기존 방식 (그대로 동작)\nblock_manager.add_block(\n    context=\"사용자가 새로운 기능을 요청했습니다\",  # 자유형 텍스트 그대로\n    keywords=[\"사용자\", \"요청\", \"기능\"],\n    importance=0.8\n)\n\n# v2.5.3 새로운 방식 (기존과 완전 호환)\nblock_manager.add_block(\n    context=\"[사용자-요청-기능개선] 새로운 기능을 요청했습니다\",  # 액탄트 패턴 포함\n    keywords=[\"사용자\", \"요청\", \"기능\"],\n    importance=0.8\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_compatible_design.md",
      "line_number": 52,
      "example_type": "python",
      "content": "class ActantEnhancer:\n    \"\"\"기존 메모리에 액탄트 정보를 비파괴적으로 추가\"\"\"\n    \n    def detect_actant_pattern(self, content: str) -> Optional[ActantInfo]:\n        \"\"\"액탄트 패턴 감지 (기존 데이터에 영향 없음)\"\"\"\n        pattern = r'^\\[(\\w+)-(\\w+)-(\\w+)\\]\\s*(.+)$'\n        match = re.match(pattern, content)\n        \n        if match:\n            subject, action, object_target, description = match.groups()\n            return ActantInfo(\n                subject=subject,\n                action=action,\n                object_target=object_target,\n                description=description,\n                is_structured=True\n            )\n        else:\n            # 기존 자유형 텍스트도 그대로 지원\n            return ActantInfo(\n                subject=None,\n                action=None, \n                object_target=None,\n                description=content,\n                is_structured=False\n            )\n    \n    def enhance_existing_memories(self) -> None:\n        \"\"\"기존 메모리를 손상 없이 액탄트 정보로 보강 (선택적)\"\"\"\n        # 기존 블록은 그대로 두고, metadata에만 분석 결과 추가\n        pass",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_compatible_design.md",
      "line_number": 88,
      "example_type": "python",
      "content": "# MCP 도구 - 완전 호환성 보장\n{\n    \"name\": \"add_memory\",\n    \"description\": \"Add permanent memories. RECOMMENDED format for better organization: '[Subject-Action-Object] description'. Examples: '[사용자-요청-기능개선] 새 기능 요청', '[Claude-발견-버그] 오류 발견'. Traditional free-text format also fully supported.\",\n    \"parameters\": {\n        \"content\": {\n            \"description\": \"Memory content. Recommended: start with '[Subject-Action-Object]' for structured recording. Free-text format also supported for backward compatibility.\"\n        }\n    }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_compatible_design.md",
      "line_number": 103,
      "example_type": "python",
      "content": "class CompatibleRelationshipAnalyzer:\n    \"\"\"기존 데이터를 손상시키지 않는 관계 분석\"\"\"\n    \n    def analyze_relationships(self, memories: List[MemoryBlock]) -> RelationshipGraph:\n        \"\"\"기존 + 새로운 메모리 모두 분석\"\"\"\n        graph = RelationshipGraph()\n        \n        for memory in memories:\n            # 액탄트 패턴이 있으면 정밀 분석\n            actant_info = self.detect_actant_pattern(memory.context)\n            if actant_info.is_structured:\n                relationships = self._extract_structured_relationships(actant_info)\n            else:\n                # 기존 자유형 텍스트도 키워드 기반으로 분석\n                relationships = self._extract_keyword_relationships(memory)\n            \n            graph.add_relationships(relationships)\n        \n        return graph",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_compatible_design.md",
      "line_number": 146,
      "example_type": "python",
      "content": "# 기존 코드는 전혀 변경하지 않음\n# 새로운 기능만 추가\n\ndef add_block_enhanced(self, context: str, **kwargs):\n    \"\"\"기존 add_block과 100% 호환, 액탄트 분석만 추가\"\"\"\n    \n    # 기존 방식 그대로 실행 (위험 0%)\n    result = self.add_block_original(context, **kwargs)\n    \n    # 추가 분석만 수행 (기존 데이터에 영향 없음)\n    try:\n        actant_info = self._analyze_actant_pattern(context)\n        if actant_info.is_structured:\n            # metadata 테이블에 액탄트 정보 선택적 저장\n            self._store_actant_metadata(result['block_index'], actant_info)\n    except Exception as e:\n        # 분석 실패해도 기존 기능에 영향 없음\n        logger.debug(f\"Actant analysis failed (non-critical): {e}\")\n    \n    return result",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_compatible_design.md",
      "line_number": 170,
      "example_type": "python",
      "content": "def validate_compatibility():\n    \"\"\"기존 데이터베이스와 100% 호환성 검증\"\"\"\n    \n    # 기존 데이터 읽기 테스트\n    old_memories = db.get_all_blocks()  # 기존 방식으로 읽기\n    assert len(old_memories) > 0\n    \n    # 새로운 기능으로 기존 데이터 처리 테스트\n    for memory in old_memories:\n        enhanced_analysis = analyze_with_actant(memory.context)\n        # 기존 데이터가 정상적으로 처리되는지 확인\n    \n    # 기존 API 호환성 테스트\n    result = add_memory(\"기존 방식 자유 텍스트\")\n    assert result is not None\n    \n    print(\"✅ 100% 호환성 검증 완료\")",
      "expected_output": null
    },
    {
      "file_path": "docs/developer_guide.md",
      "line_number": 20,
      "example_type": "python",
      "content": "from greeum.block_manager import BlockManager\n\n# 초기화\nblock_manager = BlockManager(data_dir=\"./data\")\n\n# 기억 추가\nmemory_id = block_manager.add_memory(\"이것은 장기 기억에 저장될 내용입니다.\")\n# 또는 상세 정보와 함께 추가\nmemory_id = block_manager.add_block(\n    context=\"상세한 기억 내용\",\n    keywords=[\"키워드1\", \"키워드2\"],\n    tags=[\"태그1\", \"태그2\"],\n    importance=0.8  # 0.0~1.0\n)\n\n# 기억 조회\nmemory = block_manager.get_memory(memory_id)\n# 또는\nblock = block_manager.get_block(block_index)\n\n# 기억 검색\nblocks = block_manager.search_blocks_by_keyword([\"키워드1\", \"키워드2\"], limit=5)\n# 임베딩 기반 검색\nsimilar_blocks = block_manager.search_blocks_by_embedding(embedding_vector, top_k=5)\n# 날짜 범위 검색\ndate_blocks = block_manager.search_blocks_by_date_range(\"2023-01-01\", \"2023-01-31\")\n\n# 기억 업데이트\nblock_manager.update_memory(memory_id, \"업데이트된 내용\")\n\n# 기억 삭제\nblock_manager.delete_memory(memory_id)\n\n# 블록체인 무결성 검증\nis_valid = block_manager.verify_chain()",
      "expected_output": null
    },
    {
      "file_path": "docs/developer_guide.md",
      "line_number": 67,
      "example_type": "python",
      "content": "from greeum.stm_manager import STMManager\n\n# 초기화\nstm_manager = STMManager(data_dir=\"./data\")\n\n# 단기 기억 추가\nmemory_id = stm_manager.add_memory(\n    \"이것은 단기 기억입니다.\",\n    ttl=3600,  # 초 단위 (1시간)\n    importance=0.7  # 0.0~1.0\n)\n# 또는 사전 정의된 TTL 유형 사용\nmemory_id = stm_manager.add_memory(\n    \"이것은 중기 기억입니다.\",\n    ttl_type=\"medium\"  # \"short\", \"medium\", \"long\" 중 하나\n)\n\n# 단기 기억 조회\nmemories = stm_manager.get_memories(limit=10)\n# 만료된 기억 포함\nall_memories = stm_manager.get_memories(include_expired=True)\n\n# 단기 기억 검색\nresults = stm_manager.search(\"검색어\", limit=5)\n\n# 특정 단기 기억 삭제\nstm_manager.forget(memory_id)\n\n# 만료된 모든 기억 정리\ncleaned_count = stm_manager.cleanup_expired()",
      "expected_output": null
    },
    {
      "file_path": "docs/developer_guide.md",
      "line_number": 109,
      "example_type": "python",
      "content": "from greeum.block_manager import BlockManager\nfrom greeum.cache_manager import CacheManager\n\n# 블록 관리자 초기화\nblock_manager = BlockManager(data_dir=\"./data\")\n\n# 캐시 관리자 초기화\ncache_manager = CacheManager(block_manager=block_manager, capacity=10)\n\n# 캐시 업데이트\ncache_manager.update_cache(\n    query_embedding=[0.1, 0.2, ...],  # 쿼리 임베딩 벡터\n    query_keywords=[\"키워드1\", \"키워드2\"]  # 쿼리 키워드\n)\n\n# 관련 블록 검색\nrelevant_blocks = cache_manager.get_relevant_blocks(\n    query_embedding=[0.1, 0.2, ...],\n    query_keywords=[\"키워드1\", \"키워드2\"],\n    limit=5\n)\n\n# 키워드만으로 검색\nkeyword_blocks = cache_manager.search(\"키워드\", limit=5)\n\n# 캐시 비우기\ncache_manager.clear_cache()",
      "expected_output": null
    },
    {
      "file_path": "docs/developer_guide.md",
      "line_number": 147,
      "example_type": "python",
      "content": "from greeum.block_manager import BlockManager\nfrom greeum.cache_manager import CacheManager\nfrom greeum.stm_manager import STMManager\nfrom greeum.prompt_wrapper import PromptWrapper\n\n# 관리자 초기화\nblock_manager = BlockManager(data_dir=\"./data\")\ncache_manager = CacheManager(block_manager=block_manager)\nstm_manager = STMManager(data_dir=\"./data\")\n\n# 프롬프트 래퍼 초기화\nprompt_wrapper = PromptWrapper(\n    cache_manager=cache_manager,\n    stm_manager=stm_manager\n)\n\n# 기본 프롬프트 생성\nprompt = prompt_wrapper.compose_prompt(\n    user_input=\"프로젝트 진행 상황은 어때?\",\n    include_stm=True,  # 단기 기억 포함 여부\n    max_blocks=3,  # 최대 블록 수\n    max_stm=5  # 최대 단기 기억 수\n)\n\n# 사용자 정의 템플릿 설정\ncustom_template = \"\"\"\n너는 기억을 가진 AI 비서야. 다음 정보를 기반으로 질문에 답변해줘:\n\n<장기 기억>\n{long_term_memories}\n</장기 기억>\n\n<단기 기억>\n{short_term_memories}\n</단기 기억>\n\n유저: {user_input}\nAI: \n\"\"\"\nprompt_wrapper.set_template(custom_template)\n\n# 새 템플릿으로 프롬프트 생성\nprompt = prompt_wrapper.compose_prompt(\"새 프로젝트는 어떻게 진행되고 있어?\")\n\n# LLM에 전달\n# llm_response = call_your_llm(prompt)",
      "expected_output": null
    },
    {
      "file_path": "docs/developer_guide.md",
      "line_number": 205,
      "example_type": "python",
      "content": "from greeum.block_manager import BlockManager\nfrom greeum.temporal_reasoner import TemporalReasoner\n\n# 블록 관리자 초기화\nblock_manager = BlockManager(data_dir=\"./data\")\n\n# 시간 추론기 초기화\ntemporal_reasoner = TemporalReasoner(\n    db_manager=block_manager,\n    default_language=\"auto\"  # \"ko\", \"en\", \"auto\" 중 하나\n)\n\n# 시간 참조 추출\ntime_refs = temporal_reasoner.extract_time_references(\"3일 전에 뭐 했어?\")\n\n# 시간 기반 검색\nresults = temporal_reasoner.search_by_time_reference(\n    \"어제 먹은 저녁 메뉴가 뭐였지?\",\n    margin_hours=12  # 시간 경계 확장\n)\n\n# 하이브리드 검색 (시간 + 임베딩 + 키워드)\nhybrid_results = temporal_reasoner.hybrid_search(\n    query=\"어제 읽은 책 제목이 뭐였지?\",\n    embedding=[0.1, 0.2, ...],\n    keywords=[\"책\", \"제목\"],\n    time_weight=0.3,\n    embedding_weight=0.5,\n    keyword_weight=0.2,\n    top_k=5\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/developer_guide.md",
      "line_number": 247,
      "example_type": "python",
      "content": "from greeum.text_utils import (\n    process_user_input,\n    extract_keywords,\n    extract_tags,\n    compute_embedding,\n    estimate_importance\n)\n\n# 사용자 입력 처리\nprocessed = process_user_input(\n    \"이것은 처리할 텍스트입니다.\",\n    extract_keywords=True,\n    extract_tags=True,\n    compute_embedding=True\n)\n# 결과: {\"context\": \"...\", \"keywords\": [...], \"tags\": [...], \"embedding\": [...], \"importance\": 0.x}\n\n# 키워드 추출\nkeywords = extract_keywords(\n    \"키워드를 추출할 텍스트입니다.\",\n    language=\"ko\",  # \"ko\", \"en\", \"auto\" 중 하나\n    max_keywords=5\n)\n\n# 태그 추출\ntags = extract_tags(\n    \"태그를 추출할 텍스트입니다.\",\n    language=\"auto\"\n)\n\n# 임베딩 계산\nembedding = compute_embedding(\"임베딩을 계산할 텍스트입니다.\")\n\n# 중요도 추정\nimportance = estimate_importance(\"중요도를 계산할 텍스트입니다.\")  # 0.0~1.0 사이 값",
      "expected_output": null
    },
    {
      "file_path": "docs/developer_guide.md",
      "line_number": 289,
      "example_type": "python",
      "content": "from greeum.block_manager import BlockManager\nfrom greeum.stm_manager import STMManager\nfrom greeum.cache_manager import CacheManager\nfrom greeum.prompt_wrapper import PromptWrapper\nfrom greeum.temporal_reasoner import TemporalReasoner\nfrom greeum.text_utils import process_user_input\n\n# 기본 경로 설정\ndata_dir = \"./data\"\n\n# 컴포넌트 초기화\nblock_manager = BlockManager(data_dir=data_dir)\nstm_manager = STMManager(data_dir=data_dir)\ncache_manager = CacheManager(block_manager=block_manager)\nprompt_wrapper = PromptWrapper(cache_manager=cache_manager, stm_manager=stm_manager)\ntemporal_reasoner = TemporalReasoner(db_manager=block_manager, default_language=\"auto\")\n\n# 사용자 입력 처리\nuser_input = \"프로젝트를 시작했는데 정말 흥미진진해!\"\nprocessed = process_user_input(user_input)\n\n# 장기 기억 추가\nmemory_id = block_manager.add_block(\n    context=processed[\"context\"],\n    keywords=processed[\"keywords\"],\n    tags=processed[\"tags\"],\n    embedding=processed[\"embedding\"],\n    importance=processed[\"importance\"]\n)\n\n# 단기 기억에도 추가\nstm_id = stm_manager.add_memory(processed[\"context\"], ttl_type=\"medium\")\n\n# 캐시 업데이트\ncache_manager.update_cache(\n    query_embedding=processed[\"embedding\"],\n    query_keywords=processed[\"keywords\"]\n)\n\n# 시간 기반 검색 질의\ntime_query = \"어제 무슨 일이 있었지?\"\ntime_results = temporal_reasoner.search_by_time_reference(time_query)\n\n# 프롬프트 생성\nuser_question = \"그 프로젝트 진행 상황은 어때?\"\nprompt = prompt_wrapper.compose_prompt(user_question)\n\n# LLM에 전달하여 응답 생성\n# llm_response = call_your_llm(prompt)",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 24,
      "example_type": "cli",
      "content": "python3 --version\n# Should output: Python 3.10.x or higher",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 31,
      "example_type": "cli",
      "content": "# macOS (using Homebrew)\nbrew install pipx\npipx ensurepath\n\n# Linux (Ubuntu/Debian)\nsudo apt install pipx\npipx ensurepath\n\n# Windows\npip install --user pipx\npipx ensurepath",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 49,
      "example_type": "cli",
      "content": "# Install latest Greeum with anchor system\npipx install \"greeum>=2.2.5\"\n\n# Verify installation\npython3 -m greeum.cli --version",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 59,
      "example_type": "cli",
      "content": "# Install Greeum\npip install greeum\n\n# Verify installation\ngreeum --version",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 71,
      "example_type": "cli",
      "content": "# Install with all optional dependencies\npipx install \"greeum[all]\"\n\n# Or with pip\npip install \"greeum[all]\"",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 85,
      "example_type": "cli",
      "content": "# Set custom data directory (optional)\nexport GREEUM_DATA_DIR=\"/path/to/your/data\"\n\n# Or use default location (~/.greeum/)",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 94,
      "example_type": "cli",
      "content": "# Add your first memory (v2.2.5+ syntax)\ngreeum memory add \"I'm starting to use Greeum for memory management. This is my first memory entry.\"\n\n# Verify it was created\ngreeum memory search \"Greeum\" --count 5",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 104,
      "example_type": "cli",
      "content": "# Add a few more memories\ngreeum memory add \"Working on a Python project with FastAPI\"\ngreeum memory add \"Meeting with team about Q4 goals\"\n\n# Search memories\ngreeum memory search \"python\" --count 3\ngreeum memory search \"meeting\" --count 3\n\n# View recent memories\ngreeum recent-memories --count 10",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 121,
      "example_type": "cli",
      "content": "# Add memory with content (v2.2.5+ syntax)\ngreeum memory add \"Your memory content here\"\n\n# Add short-term memory with TTL\ngreeum stm add \"Working on login page today\" --ttl 24h\n\n# Add memory with importance (via Python API)\n# CLI focuses on simplicity, use Python API for advanced options",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 134,
      "example_type": "cli",
      "content": "# Search memories with query\ngreeum memory search \"project python\" --count 5\n\n# Recent memories\ngreeum recent-memories --count 10\n\n# Anchor-based search (v2.2.5+ NEW!)\ngreeum memory search \"meeting\" --slot A --radius 2",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 153,
      "example_type": "cli",
      "content": "# Check current anchor status\ngreeum anchors status\n\n# Set anchors to important memories\ngreeum anchors set A 1     # Pin memory block #1 to slot A\ngreeum anchors set B 2     # Pin memory block #2 to slot B\n\n# Pin anchors to prevent auto-movement\ngreeum anchors pin A       # Anchor A won't move automatically\n\n# Search near anchors (faster than global search)\ngreeum memory search \"python\" --slot A --radius 3\n\n# Clear all anchors\ngreeum anchors clear",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 173,
      "example_type": "cli",
      "content": "# Check system statistics\ngreeum recent-memories --count 5\n\n# Check quality of file\ngreeum quality -f \"/path/to/file.txt\"\n\n# Specify importance level for quality check\ngreeum quality -c \"Important content\" -i 0.8",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 186,
      "example_type": "cli",
      "content": "# View usage analytics (last 7 days)\ngreeum analytics\n\n# View analytics for specific period\ngreeum analytics -d 30\n\n# Detailed analytics report\ngreeum analytics -d 30 --detailed",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 199,
      "example_type": "cli",
      "content": "# Run memory optimization analysis\ngreeum optimize\n\n# Run with automatic optimization\ngreeum optimize --auto-optimize",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 209,
      "example_type": "cli",
      "content": "# Add to short-term memory\ngreeum stm \"Temporary note for current session\"\n\n# View short-term memories\ngreeum get-stm\n\n# View specific number of STM entries\ngreeum get-stm -c 10",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 222,
      "example_type": "cli",
      "content": "# Generate enhanced prompt\ngreeum prompt -i \"What did we discuss in yesterday's meeting?\"\n\n# Clear different types of memory\ngreeum clear stm        # Clear short-term memory\ngreeum clear cache      # Clear waypoint cache\ngreeum clear blocks     # Clear all blocks (with backup)\ngreeum clear all        # Clear everything\n\n# Verify blockchain integrity\ngreeum verify",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 242,
      "example_type": "cli",
      "content": "# Check version (should be v2.0.5 or higher)\ngreeum --version\n\n# Test MCP server\npython3 -m greeum.mcp.claude_code_mcp_server --help",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 281,
      "example_type": "cli",
      "content": "claude mcp list",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 308,
      "example_type": "cli",
      "content": "# Minimal MCP server (lightweight)\npython3 -m greeum.mcp.minimal_mcp_server\n\n# Universal MCP server (compatible with multiple MCP hosts)\npython3 -m greeum.mcp.universal_mcp_server\n\n# Working MCP server (development/testing)\npython3 -m greeum.mcp.working_mcp_server",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 325,
      "example_type": "cli",
      "content": "# If pipx installation fails\npip install --user pipx\npython3 -m pipx install greeum\n\n# If Python version issues\npyenv install 3.12.0\npyenv global 3.12.0\npipx install greeum",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 338,
      "example_type": "cli",
      "content": "# Fix data directory permissions\nchmod 755 ~/.greeum\nchmod 644 ~/.greeum/*\n\n# Or use custom directory\nexport GREEUM_DATA_DIR=\"/path/with/write/access\"",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 349,
      "example_type": "cli",
      "content": "# Check MCP server directly\npython3 -m greeum.mcp.claude_code_mcp_server --test\n\n# Verify configuration path\necho $HOME/Library/Application\\ Support/Claude/claude_desktop_config.json\n\n# Check logs\ntail -f ~/.greeum/logs/mcp.log",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 362,
      "example_type": "cli",
      "content": "# Verify memory integrity\ngreeum verify\n\n# Reset if corrupted\ngreeum clear all\n\n# Restore from backup\ncp ~/.greeum/backup/block_memory_*.jsonl ~/.greeum/block_memory.jsonl",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 386,
      "example_type": "cli",
      "content": "# Install with all dependencies for vector search\npipx install \"greeum[all]\"\n\n# Optimize memory usage\ngreeum optimize --auto-optimize\n\n# Clean up old data\ngreeum clear cache",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 407,
      "example_type": "cli",
      "content": "# Data directory location\nexport GREEUM_DATA_DIR=\"/custom/path\"\n\n# Log level\nexport GREEUM_LOG_LEVEL=\"DEBUG\"\n\n# Database type (sqlite/postgresql)\nexport GREEUM_DB_TYPE=\"sqlite\"\n\n# OpenAI API key (for embeddings)\nexport OPENAI_API_KEY=\"your-key-here\"",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 257,
      "example_type": "json",
      "content": "{\n  \"mcpServers\": {\n    \"greeum\": {\n      \"command\": \"python3\",\n      \"args\": [\n        \"-m\", \"greeum.mcp.claude_code_mcp_server\"\n      ],\n      \"env\": {\n        \"GREEUM_DATA_DIR\": \"/your/preferred/data/path\"\n      }\n    }\n  }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/get-started.md",
      "line_number": 425,
      "example_type": "json",
      "content": "{\n  \"database\": {\n    \"type\": \"sqlite\",\n    \"path\": \"memory.db\"\n  },\n  \"embeddings\": {\n    \"model\": \"sentence-transformers\",\n    \"cache\": true\n  },\n  \"quality\": {\n    \"auto_validate\": true,\n    \"threshold\": 0.7\n  },\n  \"analytics\": {\n    \"enabled\": true,\n    \"retention_days\": 90\n  }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/installation.md",
      "line_number": 16,
      "example_type": "cli",
      "content": "# 기본 설치 (v2.2.5 - 앵커 시스템 포함)\npip install \"greeum>=2.2.5\"\n\n# FAISS 벡터 인덱스 기능 포함\npip install \"greeum[faiss]>=2.2.5\"\n\n# OpenAI 임베딩 모델 지원\npip install \"greeum[openai]>=2.2.5\"\n\n# Transformers 및 BERT 재랭크 기능\npip install \"greeum[transformers]>=2.2.5\"\n\n# 모든 기능 포함 설치 (추천)\npip install \"greeum[all]>=2.2.5\"",
      "expected_output": null
    },
    {
      "file_path": "docs/installation.md",
      "line_number": 35,
      "example_type": "cli",
      "content": "git clone https://github.com/DryRainEnt/Greeum.git\ncd Greeum\n\n# 기본 의존성 설치\npip install -r requirements.txt\n\n# 개발 모드로 설치\npip install -e .\n\n# 모든 기능 포함 개발 모드 설치 (추천)\npip install -e \".[all]\"\n\n# 특정 기능만 포함\npip install -e \".[faiss,transformers]\"",
      "expected_output": null
    },
    {
      "file_path": "docs/installation.md",
      "line_number": 54,
      "example_type": "cli",
      "content": "# 가상 환경 생성\npython -m venv venv\n\n# 가상 환경 활성화 (Windows)\nvenv\\Scripts\\activate\n\n# 가상 환경 활성화 (macOS/Linux)\nsource venv/bin/activate",
      "expected_output": null
    },
    {
      "file_path": "docs/installation.md",
      "line_number": 110,
      "example_type": "cli",
      "content": "mkdir -p data/memory",
      "expected_output": null
    },
    {
      "file_path": "docs/installation.md",
      "line_number": 120,
      "example_type": "cli",
      "content": "# FAISS 의존성 설치\npip install greeum[faiss]\n\n# 또는 직접 설치\npip install faiss-cpu>=1.7.4",
      "expected_output": null
    },
    {
      "file_path": "docs/installation.md",
      "line_number": 132,
      "example_type": "cli",
      "content": "# Transformers 의존성 설치\npip install greeum[transformers]\n\n# 또는 직접 설치\npip install sentence-transformers>=2.2.0",
      "expected_output": null
    },
    {
      "file_path": "docs/installation.md",
      "line_number": 155,
      "example_type": "cli",
      "content": "# OpenAI 의존성 설치\npip install greeum[openai]\n\n# 환경 변수 설정\nexport OPENAI_API_KEY=\"your_openai_api_key\"",
      "expected_output": null
    },
    {
      "file_path": "docs/installation.md",
      "line_number": 167,
      "example_type": "cli",
      "content": "# 기본 설치 확인\npython -c \"from greeum import BlockManager; print('Greeum v0.6.0 설치 성공!')\"\n\n# FAISS 기능 확인\npython -c \"from greeum.vector_index import FaissVectorIndex; print('FAISS 벡터 인덱스 설치 성공!')\"\n\n# SearchEngine 기능 확인\npython -c \"from greeum.search_engine import SearchEngine; print('SearchEngine 설치 성공!')\"\n\n# STMWorkingSet 기능 확인\npython -c \"from greeum import STMWorkingSet; print('STMWorkingSet 설치 성공!')\"\n\n# BERT 재랭크 기능 확인 (선택사항)\npython -c \"from greeum.search_engine import BertReranker; print('BERT 재랭크 설치 성공!')\"",
      "expected_output": null
    },
    {
      "file_path": "docs/installation.md",
      "line_number": 144,
      "example_type": "python",
      "content": "from greeum import STMWorkingSet\n\n# 기본 설정으로 사용\nworking_set = STMWorkingSet(capacity=8, ttl_seconds=600)",
      "expected_output": null
    },
    {
      "file_path": "docs/installation.md",
      "line_number": 73,
      "example_type": "json",
      "content": "{\n  \"storage\": {\n    \"path\": \"./data/memory\",\n    \"format\": \"json\",\n    \"database_url\": \"sqlite:///data/greeum.db\"\n  },\n  \"ttl\": {\n    \"short\": 3600,    // 1시간 (초 단위)\n    \"medium\": 86400,  // 1일 (초 단위)\n    \"long\": 2592000   // 30일 (초 단위)\n  },\n  \"embedding\": {\n    \"model\": \"default\",\n    \"dimension\": 384,\n    \"faiss_enabled\": true\n  },\n  \"search\": {\n    \"use_bert_reranker\": true,\n    \"reranker_model\": \"cross-encoder/ms-marco-MiniLM-L-6-v2\",\n    \"vector_search_top_k\": 15\n  },\n  \"working_memory\": {\n    \"capacity\": 8,\n    \"ttl_seconds\": 600\n  },\n  \"language\": {\n    \"default\": \"auto\",\n    \"supported\": [\"ko\", \"en\", \"ja\", \"zh\", \"es\"]\n  }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_ai_migration_design.md",
      "line_number": 263,
      "example_type": "cli",
      "content": "$ greeum memory search \"프로젝트\"\n\n🚨 Greeum v2.5.3 Schema Migration Required\n📊 Legacy database detected with 150 memories\n⚡ AI will enhance your memories with structured actant format\n🤖 This enables powerful relationship and causality analysis\n\nProceed with AI migration? [Y/n]: y\n\n🤖 Starting AI-powered migration...\n📊 Found 150 memories to migrate\n\n✅ Migrating: 100.0% (150/150)\n🎉 Migration completed!\n✅ Successfully migrated: 142\n⚠️  Preserved as-is: 8\n📈 Migration success rate: 94.7%\n\n🔍 Discovering relationships in migrated data...\n🔗 Discovered 89 relationships\n\n✨ Your memory system is now enhanced with actant structure!\n🔍 Search results: Found 12 project-related memories",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_ai_migration_design.md",
      "line_number": 44,
      "example_type": "python",
      "content": "class SchemaVersionDetector:\n    \"\"\"스키마 버전 감지 및 마이그레이션 필요성 판단\"\"\"\n    \n    def detect_schema_version(self) -> SchemaVersion:\n        \"\"\"현재 데이터베이스 스키마 버전 확인\"\"\"\n        cursor = self.conn.cursor()\n        \n        # actant 필드 존재 여부 확인\n        cursor.execute(\"PRAGMA table_info(blocks)\")\n        columns = [col[1] for col in cursor.fetchall()]\n        \n        if 'actant_subject' in columns:\n            return SchemaVersion.V253_ACTANT\n        else:\n            return SchemaVersion.V252_LEGACY\n    \n    def needs_migration(self) -> bool:\n        \"\"\"마이그레이션 필요 여부 확인\"\"\"\n        version = self.detect_schema_version()\n        if version == SchemaVersion.V252_LEGACY:\n            # 구형 데이터 존재하면 마이그레이션 필요\n            cursor = self.conn.cursor()\n            cursor.execute(\"SELECT COUNT(*) FROM blocks\")\n            return cursor.fetchone()[0] > 0\n        return False",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_ai_migration_design.md",
      "line_number": 73,
      "example_type": "python",
      "content": "class ForcedMigrationInterface:\n    \"\"\"사용자에게 마이그레이션을 강제하는 인터페이스\"\"\"\n    \n    def check_and_force_migration(self):\n        \"\"\"시작시 마이그레이션 필수 체크\"\"\"\n        if self.detector.needs_migration():\n            print(\"🚨 Greeum v2.5.3 Schema Migration Required\")\n            print(\"📊 Legacy database detected. AI-powered migration needed.\")\n            print(\"⚡ This will enhance your memories with actant structure.\")\n            print()\n            \n            while True:\n                choice = input(\"Proceed with AI migration? [Y/n]: \").lower()\n                if choice in ['y', 'yes', '']:\n                    return self.perform_ai_migration()\n                elif choice in ['n', 'no']:\n                    print(\"❌ Migration required to use v2.5.3. Exiting...\")\n                    exit(1)\n                else:\n                    print(\"Please enter Y or N\")",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_ai_migration_design.md",
      "line_number": 97,
      "example_type": "python",
      "content": "class AIActantParser:\n    \"\"\"AI 기반 액탄트 패턴 파싱\"\"\"\n    \n    def parse_legacy_memory(self, context: str) -> ActantParseResult:\n        \"\"\"\n        AI가 기존 메모리를 액탄트 구조로 해석\n        \n        사용 방법:\n        1. Claude/GPT API 호출\n        2. 프롬프트: \"다음 텍스트를 [주체-행동-대상] 형식으로 분석해줘\"\n        3. 결과 파싱 및 검증\n        \"\"\"\n        \n        prompt = f'''\n다음 메모리 텍스트를 그레마스 액탄트 모델의 [주체-행동-대상] 구조로 분석해주세요:\n\n원본: \"{context}\"\n\n분석 결과를 다음 JSON 형식으로 제공해주세요:\n{{\n    \"subject\": \"행동을 수행한 주체 (사용자/Claude/팀/시스템)\",\n    \"action\": \"구체적인 행동 (요청/발견/결정/구현/완료 등)\", \n    \"object\": \"행동의 대상\",\n    \"confidence\": 0.0-1.0,\n    \"original_preserved\": true\n}}\n\n주의사항:\n- 원본 의미를 정확히 보존해야 합니다\n- 애매한 경우 confidence를 낮게 설정하세요\n- subject는 반드시 명확한 행위자여야 합니다\n'''\n\n        try:\n            # AI API 호출 (Claude/OpenAI)\n            response = self.ai_client.complete(prompt)\n            parsed = json.loads(response)\n            \n            return ActantParseResult(\n                subject=parsed['subject'],\n                action=parsed['action'],\n                object_target=parsed['object'],\n                confidence=parsed['confidence'],\n                original_context=context,\n                success=True\n            )\n            \n        except Exception as e:\n            # AI 파싱 실패시 안전한 폴백\n            return ActantParseResult(\n                subject=None,\n                action=None, \n                object_target=None,\n                confidence=0.0,\n                original_context=context,\n                success=False,\n                error=str(e)\n            )",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_ai_migration_design.md",
      "line_number": 159,
      "example_type": "python",
      "content": "class ProgressiveMigrator:\n    \"\"\"점진적 AI 마이그레이션 실행\"\"\"\n    \n    def perform_full_migration(self) -> MigrationResult:\n        \"\"\"전체 데이터베이스 AI 마이그레이션\"\"\"\n        \n        print(\"🤖 Starting AI-powered migration...\")\n        \n        # 1. 스키마 업그레이드 (안전한 ALTER TABLE)\n        self._upgrade_schema()\n        \n        # 2. 모든 기존 블록 조회\n        legacy_blocks = self._get_legacy_blocks()\n        print(f\"📊 Found {len(legacy_blocks)} memories to migrate\")\n        \n        # 3. 진행률 표시와 함께 순차 마이그레이션\n        migrated = 0\n        failed = 0\n        \n        for i, block in enumerate(legacy_blocks):\n            try:\n                # AI 파싱\n                parse_result = self.ai_parser.parse_legacy_memory(block['context'])\n                \n                if parse_result.success and parse_result.confidence >= 0.5:\n                    # 성공적 파싱 → DB 업데이트\n                    self._update_block_with_actant(block['block_index'], parse_result)\n                    migrated += 1\n                    status = \"✅\"\n                else:\n                    # 파싱 실패 → 원본 유지 (actant 필드 NULL)\n                    failed += 1\n                    status = \"⚠️\"\n                \n                # 진행률 표시\n                progress = (i + 1) / len(legacy_blocks) * 100\n                print(f\"\\r{status} Migrating: {progress:.1f}% ({i+1}/{len(legacy_blocks)})\", end=\"\")\n                \n            except Exception as e:\n                failed += 1\n                print(f\"\\n❌ Migration error for block {block['block_index']}: {e}\")\n        \n        print(f\"\\n🎉 Migration completed!\")\n        print(f\"✅ Successfully migrated: {migrated}\")\n        print(f\"⚠️  Preserved as-is: {failed}\")\n        print(f\"📈 Migration success rate: {migrated/(migrated+failed)*100:.1f}%\")\n        \n        return MigrationResult(\n            migrated_count=migrated,\n            failed_count=failed,\n            success_rate=migrated/(migrated+failed) if (migrated+failed) > 0 else 0\n        )",
      "expected_output": null
    },
    {
      "file_path": "docs/v253_ai_migration_design.md",
      "line_number": 215,
      "example_type": "python",
      "content": "class PostMigrationRelationshipDiscovery:\n    \"\"\"마이그레이션 완료 후 자동 관계 발견\"\"\"\n    \n    def discover_relationships(self) -> None:\n        \"\"\"마이그레이션된 액탄트 데이터에서 관계 추론\"\"\"\n        \n        print(\"🔍 Discovering relationships in migrated data...\")\n        \n        # 액탄트가 성공적으로 파싱된 블록들만 대상\n        migrated_blocks = self._get_migrated_blocks()\n        \n        relationships = []\n        \n        for source_block in migrated_blocks:\n            for target_block in migrated_blocks:\n                if source_block['block_index'] == target_block['block_index']:\n                    continue\n                \n                # 주체 협업 관계 발견\n                if (source_block['actant_subject'] == target_block['actant_subject'] and\n                    source_block['actant_subject'] is not None):\n                    relationships.append({\n                        'source': source_block['block_index'],\n                        'target': target_block['block_index'],\n                        'type': 'subject_collaboration',\n                        'confidence': 0.8\n                    })\n                \n                # 행동 인과관계 발견 \n                if self._is_causal_action_pair(source_block['actant_action'], \n                                                target_block['actant_action']):\n                    relationships.append({\n                        'source': source_block['block_index'],\n                        'target': target_block['block_index'],\n                        'type': 'action_causality',\n                        'confidence': 0.7\n                    })\n        \n        # 관계 데이터베이스 저장\n        self._store_relationships(relationships)\n        print(f\"🔗 Discovered {len(relationships)} relationships\")",
      "expected_output": null
    },
    {
      "file_path": "docs/claude-setup.md",
      "line_number": 12,
      "example_type": "cli",
      "content": "# 1. Install Greeum\npip install greeum\n\n# 2. Test installation\ngreeum --version\n\n# 3. Add to Claude Desktop config\n# See \"Claude Desktop Setup\" below for your platform",
      "expected_output": null
    },
    {
      "file_path": "docs/claude-setup.md",
      "line_number": 133,
      "example_type": "cli",
      "content": "   # Ensure only your user can access the data\n   chmod 700 /path/to/your/greeum-data\n   ```\n\n2. **Environment Variables**\n   - Never commit API keys to version control\n   - Use absolute paths for data directories\n   - Regularly backup your memory data\n\n3. **Network Security**\n   - Greeum operates locally by default\n   - No network access required for basic functionality\n   - Memory data stays on your machine\n\n### 📁 Recommended Data Directory Structure",
      "expected_output": null
    },
    {
      "file_path": "docs/claude-setup.md",
      "line_number": 177,
      "example_type": "cli",
      "content": "# Check if greeum is installed\npip show greeum\n\n# If not installed\npip install greeum\n\n# Check PATH\nwhich greeum",
      "expected_output": null
    },
    {
      "file_path": "docs/claude-setup.md",
      "line_number": 190,
      "example_type": "cli",
      "content": "   # Validate JSON\n   python -c \"import json; json.load(open('claude_desktop_config.json'))\"\n   ```\n\n2. **Check logs** (macOS):\n   ```bash\n   tail -f ~/Library/Logs/Claude/mcp*.log\n   ```\n\n3. **Test server manually**:\n   ```bash\n   greeum mcp serve -t stdio\n   # Should start without errors\n   ```\n\n#### ❌ \"Permission denied\" errors",
      "expected_output": null
    },
    {
      "file_path": "docs/claude-setup.md",
      "line_number": 218,
      "example_type": "cli",
      "content": "# Force environment check\ngreeum mcp serve -t stdio --debug\n\n# Check environment variables\necho $OS\necho $TERM\nuname -a",
      "expected_output": null
    },
    {
      "file_path": "docs/claude-setup.md",
      "line_number": 229,
      "example_type": "cli",
      "content": "# Enable detailed logging\nGREEUM_LOG_LEVEL=DEBUG greeum mcp serve -t stdio",
      "expected_output": null
    },
    {
      "file_path": "docs/claude-setup.md",
      "line_number": 45,
      "example_type": "json",
      "content": "{\n  \"mcpServers\": {\n    \"greeum\": {\n      \"command\": \"greeum\",\n      \"args\": [\"mcp\", \"serve\", \"-t\", \"stdio\"],\n      \"env\": {\n        \"GREEUM_DATA_DIR\": \"/path/to/your/data\"\n      }\n    }\n  }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/claude-setup.md",
      "line_number": 61,
      "example_type": "json",
      "content": "{\n  \"mcpServers\": {\n    \"greeum\": {\n      \"command\": \"/usr/local/bin/greeum\",\n      \"args\": [\"mcp\", \"serve\", \"-t\", \"stdio\"],\n      \"env\": {\n        \"GREEUM_DATA_DIR\": \"/Users/yourname/greeum-data\",\n        \"GREEUM_LOG_LEVEL\": \"INFO\",\n        \"PYTHONPATH\": \"/path/to/greeum/if/needed\"\n      }\n    }\n  }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/claude-setup.md",
      "line_number": 82,
      "example_type": "json",
      "content": "{\n  \"mcpServers\": {\n    \"greeum\": {\n      \"command\": \"wsl\",\n      \"args\": [\"greeum\", \"mcp\", \"serve\", \"-t\", \"stdio\"],\n      \"env\": {\n        \"GREEUM_DATA_DIR\": \"/mnt/c/Users/YourName/greeum-data\"\n      }\n    }\n  }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/claude-setup.md",
      "line_number": 97,
      "example_type": "json",
      "content": "{\n  \"mcpServers\": {\n    \"greeum\": {\n      \"command\": \"powershell\",\n      \"args\": [\"-Command\", \"greeum mcp serve -t stdio\"],\n      \"env\": {\n        \"GREEUM_DATA_DIR\": \"C:\\\\Users\\\\YourName\\\\greeum-data\"\n      }\n    }\n  }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/claude-setup.md",
      "line_number": 112,
      "example_type": "json",
      "content": "{\n  \"mcpServers\": {\n    \"greeum\": {\n      \"command\": \"greeum\",\n      \"args\": [\"mcp\", \"serve\", \"-t\", \"stdio\"],\n      \"env\": {\n        \"GREEUM_DATA_DIR\": \"/Users/yourname/greeum-data\"\n      }\n    }\n  }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 645,
      "example_type": "cli",
      "content": "greeum anchors status\n# Shows Rich-formatted table with anchor details\n\ngreeum anchors status --verbose\n# Include additional metadata",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 657,
      "example_type": "cli",
      "content": "# Set anchor for slot A\ngreeum anchors set A 1234\n\n# With custom summary and hop budget  \ngreeum anchors set B 5678 --summary \"Machine learning project\" --hop-budget 2",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 669,
      "example_type": "cli",
      "content": "# Pin anchor (prevent auto-movement)\ngreeum anchors pin A\n\n# Unpin anchor (allow auto-movement)\ngreeum anchors unpin A",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 683,
      "example_type": "cli",
      "content": "# Basic search (no anchors)\ngreeum search \"machine learning algorithms\"\n\n# Anchor-based localized search\ngreeum search \"neural networks\" --slot A --radius 2\n\n# Multiple search parameters\ngreeum search \"data analysis\" --slot B --radius 1 --fallback --limit 10",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 710,
      "example_type": "cli",
      "content": "curl -X GET \"http://localhost:5000/v1/anchors\"",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 736,
      "example_type": "cli",
      "content": "curl -X PATCH \"http://localhost:5000/v1/anchors/A\" \\\n     -H \"Content-Type: application/json\" \\\n     -d '{\n       \"anchor_block_id\": \"9999\",\n       \"summary\": \"New project context\",\n       \"hop_budget\": 2,\n       \"pinned\": true\n     }'",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 753,
      "example_type": "cli",
      "content": "# Basic search\ncurl -X GET \"http://localhost:5000/api/v1/search?query=machine+learning\"\n\n# Anchor-based search\ncurl -X GET \"http://localhost:5000/api/v1/search?query=neural+networks&slot=A&radius=2&limit=5\"",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 1054,
      "example_type": "cli",
      "content": "# Data directory\nexport GREEUM_DATA_DIR=\"/path/to/data\"\n\n# Database configuration  \nexport GREEUM_DB_TYPE=\"sqlite\"  # or \"postgres\"\nexport GREEUM_CONNECTION_STRING=\"path/to/db.sqlite\"\n\n# Logging\nexport GREEUM_LOG_LEVEL=\"INFO\"  # DEBUG, INFO, WARNING, ERROR\n\n# Quality settings\nexport GREEUM_QUALITY_THRESHOLD=\"0.7\"\nexport GREEUM_DUPLICATE_THRESHOLD=\"0.85\"\n\n# External API keys\nexport OPENAI_API_KEY=\"your-key-here\"",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 53,
      "example_type": "python",
      "content": "from greeum import BlockManager, DatabaseManager\n\n# Use default SQLite database\nbm = BlockManager()\n\n# Use custom database manager\ndb_manager = DatabaseManager(\"custom_path/memory.db\")\nbm = BlockManager(db_manager)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 78,
      "example_type": "python",
      "content": "block = bm.add_block(\n    context=\"Attended team meeting about Q4 goals\",\n    keywords=[\"meeting\", \"goals\", \"team\"],\n    tags=[\"work\", \"planning\"],\n    embedding=get_embedding(\"meeting content\"),\n    importance=0.8,\n    metadata={\"meeting_id\": \"mt_001\", \"participants\": 5}\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 93,
      "example_type": "python",
      "content": "results = bm.search_by_keywords([\"python\", \"project\"], limit=5)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 101,
      "example_type": "python",
      "content": "from greeum.embedding_models import get_embedding\n\nquery_emb = get_embedding(\"What did we discuss about the project?\")\nsimilar_blocks = bm.search_by_embedding(query_emb, top_k=10)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 112,
      "example_type": "python",
      "content": "# Get recent blocks\nrecent = bm.get_blocks(limit=10)\n\n# Get by importance\nimportant = bm.get_blocks(limit=20, sort_by='importance', order='desc')",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 124,
      "example_type": "python",
      "content": "is_valid = bm.verify_blocks()\nif not is_valid:\n    print(\"Blockchain integrity compromised!\")",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 138,
      "example_type": "python",
      "content": "from greeum import STMManager\n\n# 1-hour default TTL\nstm = STMManager(default_ttl=3600)\n\n# 30-minute TTL\nstm = STMManager(default_ttl=1800)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 152,
      "example_type": "python",
      "content": "memory = {\n    \"id\": \"stm_001\",\n    \"content\": \"User is working on Python FastAPI project\",\n    \"speaker\": \"user\",\n    \"importance\": 0.7\n}\n\nstm.add_memory(memory, ttl=7200)  # 2-hour TTL",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 167,
      "example_type": "python",
      "content": "recent_memories = stm.get_recent_memories(count=10)\nall_memories = stm.get_recent_memories(count=20, include_expired=True)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 176,
      "example_type": "python",
      "content": "removed_count = stm.cleanup_expired()\nprint(f\"Removed {removed_count} expired memories\")",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 189,
      "example_type": "python",
      "content": "from greeum import CacheManager, BlockManager, STMManager\n\nbm = BlockManager()\nstm = STMManager()\ncache = CacheManager(bm, stm, max_cache_size=100)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 201,
      "example_type": "python",
      "content": "from greeum.embedding_models import get_embedding\nfrom greeum.text_utils import extract_keywords\n\nquery = \"What did we decide about the new features?\"\nembedding = get_embedding(query)\nkeywords = extract_keywords(query)\n\ncache.update_cache(query, embedding, keywords)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 216,
      "example_type": "python",
      "content": "relevant = cache.get_relevant_memories(limit=15)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 228,
      "example_type": "python",
      "content": "from greeum import PromptWrapper, CacheManager, STMManager\n\ncache = CacheManager()\nstm = STMManager()\nwrapper = PromptWrapper(cache, stm)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 240,
      "example_type": "python",
      "content": "user_query = \"How should we approach the database design?\"\nenhanced_prompt = wrapper.compose_prompt(\n    user_query, \n    include_stm=True,\n    max_context_length=3000\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 257,
      "example_type": "python",
      "content": "from greeum.core import DatabaseManager\n\n# SQLite (default)\ndb = DatabaseManager(\"data/custom.db\")\n\n# PostgreSQL\ndb = DatabaseManager(\n    \"postgresql://user:pass@localhost/greeum\",\n    db_type='postgres'\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 272,
      "example_type": "python",
      "content": "# Store block\nblock_data = {...}\ndb.store_block(block_data)\n\n# Get block\nblock = db.get_block(42)\n\n# Search operations\nresults = db.search_blocks_by_keyword([\"python\", \"api\"])\nsimilar = db.search_blocks_by_embedding(embedding_vector)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 297,
      "example_type": "python",
      "content": "from greeum.core.quality_validator import QualityValidator\n\nvalidator = QualityValidator()",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 307,
      "example_type": "python",
      "content": "result = validator.validate_memory_quality(\n    content=\"Attended team meeting about Q4 roadmap and resource allocation\",\n    importance=0.8\n)\n\nprint(f\"Quality Score: {result['quality_score']:.3f}\")\nprint(f\"Quality Level: {result['quality_level']}\")\nprint(f\"Factors: {result['quality_factors']}\")\nprint(f\"Suggestions: {result['suggestions']}\")",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 336,
      "example_type": "python",
      "content": "from greeum.core.duplicate_detector import DuplicateDetector\n\ndetector = DuplicateDetector(similarity_threshold=0.90)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 346,
      "example_type": "python",
      "content": "result = detector.check_duplicates(\n    content=\"Meeting about project timeline\",\n    embedding=content_embedding\n)\n\nif result['is_duplicate']:\n    print(f\"Found {len(result['similar_memories'])} similar memories\")\n    print(f\"Highest similarity: {result['max_similarity']:.3f}\")",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 365,
      "example_type": "python",
      "content": "from greeum.core.usage_analytics import UsageAnalytics\n\nanalytics = UsageAnalytics()",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 375,
      "example_type": "python",
      "content": "analytics.log_event(\n    event_type=\"tool_usage\",\n    tool_name=\"add_memory\",\n    metadata={\"quality_score\": 0.85, \"importance\": 0.7},\n    duration_ms=150,\n    success=True\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 389,
      "example_type": "python",
      "content": "stats = analytics.get_usage_statistics(days=30)\n\nprint(f\"Total events: {stats['total_events']}\")\nprint(f\"Unique sessions: {stats['unique_sessions']}\")\nprint(f\"Average response time: {stats['avg_response_time']:.0f}ms\")\nprint(f\"Success rate: {stats['success_rate']*100:.1f}%\")",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 402,
      "example_type": "python",
      "content": "trends = analytics.get_quality_trends(days=30)\n\nprint(f\"Average quality: {trends['avg_quality_score']:.3f}\")\nprint(f\"High quality ratio: {trends['high_quality_ratio']*100:.1f}%\")",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 417,
      "example_type": "python",
      "content": "from greeum import TemporalReasoner\n\nreasoner = TemporalReasoner()",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 427,
      "example_type": "python",
      "content": "# English\nresults = reasoner.search_by_time(\"What did I do 3 days ago?\", language='en')\n\n# Korean  \nresults = reasoner.search_by_time(\"지난 주에 무엇을 했지?\", language='ko')\n\n# Auto-detect\nresults = reasoner.search_by_time(\"昨日何をしましたか？\")",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 446,
      "example_type": "python",
      "content": "from greeum.core.search_engine import SearchEngine, BertReranker\n\n# Basic search\nengine = SearchEngine()\n\n# With BERT reranking\nreranker = BertReranker(\"cross-encoder/ms-marco-MiniLM-L-6-v2\")\nengine = SearchEngine(reranker=reranker)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 461,
      "example_type": "python",
      "content": "# Basic search (no anchors)\nresults = engine.search(\"project planning meeting\", top_k=10)\n\n# Anchor-based localized search\nresults = engine.search(\n    query=\"API authentication\",\n    top_k=5,\n    slot='A',           # Use anchor slot A\n    radius=2,           # Search within 2-hop radius\n    fallback=True       # Fall back to global search if needed\n)\n\nprint(f\"Found {len(results['blocks'])} results\")\nprint(f\"Search time: {results['metadata']['search_time_ms']:.0f}ms\")\nprint(f\"Used local search: {results['metadata'].get('local_search_used', False)}\")",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 498,
      "example_type": "python",
      "content": "from greeum.anchors.manager import AnchorManager\nfrom pathlib import Path\n\nanchor_manager = AnchorManager(Path(\"data/anchors.json\"))",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 509,
      "example_type": "python",
      "content": "slot_info = anchor_manager.get_slot_info('A')\nif slot_info:\n    print(f\"Anchor block: {slot_info['anchor_block_id']}\")\n    print(f\"Summary: {slot_info['summary']}\")\n    print(f\"Hop budget: {slot_info.get('hop_budget', 3)}\")\n    print(f\"Pinned: {slot_info.get('pinned', False)}\")",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 522,
      "example_type": "python",
      "content": "success = anchor_manager.move_anchor(\n    slot='A',\n    new_block_id='12345',\n    topic_vec=[0.1, 0.2, ...],  # 128-dim embedding\n    summary=\"API development discussion\",\n    hop_budget=2\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 536,
      "example_type": "python",
      "content": "# Prevent automatic movement\nanchor_manager.pin_anchor('A')\n\n# Allow automatic movement\nanchor_manager.unpin_anchor('A')",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 552,
      "example_type": "python",
      "content": "from greeum.graph.index import GraphIndex\n\ngraph = GraphIndex(theta=0.4, kmax=16)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 562,
      "example_type": "python",
      "content": "# Add edges with weights\nneighbors = [(\"block_123\", 0.8), (\"block_456\", 0.6)]\ngraph.upsert_edges(\"block_789\", neighbors)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 572,
      "example_type": "python",
      "content": "neighbors = graph.neighbors(\"block_789\", k=3)\nfor neighbor_id, weight in neighbors:\n    print(f\"Neighbor: {neighbor_id}, weight: {weight:.3f}\")",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 586,
      "example_type": "python",
      "content": "from greeum.api.write import AnchorBasedWriter\n\nwriter = AnchorBasedWriter(\n    db_manager=db_manager,\n    anchor_path=Path(\"data/anchors.json\"),\n    graph_path=Path(\"data/graph_snapshot.jsonl\")\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 600,
      "example_type": "python",
      "content": "# Write near anchor slot A\nblock_id = writer.write(\n    text=\"New API endpoint implemented\",\n    slot='A',\n    keywords=[\"api\", \"endpoint\"],\n    tags=[\"development\"],\n    importance=0.7\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 619,
      "example_type": "python",
      "content": "from greeum.anchors.auto_movement import AutoAnchorMovement\n\nauto_movement = AutoAnchorMovement(anchor_manager, links_cache, db_manager)\n\nevaluation = auto_movement.evaluate_anchor_movement(\n    slot='A',\n    search_results=recent_results,\n    query_topic_vec=topic_embedding\n)\n\nif evaluation['should_move']:\n    print(f\"Recommended move: {evaluation['reason']}\")\n    print(f\"Target block: {evaluation['target_block_id']}\")",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 788,
      "example_type": "python",
      "content": "# Available in Claude Code\nadd_memory(\n    content=\"Project milestone reached - API v2.0 deployed\",\n    keywords=[\"project\", \"milestone\", \"api\"],\n    importance=0.9\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 798,
      "example_type": "python",
      "content": "# Search with multiple methods\nsearch_memory(\n    query=\"project status\",\n    search_type=\"hybrid\",  # keyword, embedding, hybrid\n    limit=10\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 810,
      "example_type": "python",
      "content": "# Get usage insights\nusage_analytics(\n    days=30,\n    detailed=True,\n    include_trends=True\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 820,
      "example_type": "python",
      "content": "# System statistics\nget_memory_stats(\n    include_quality=True,\n    include_performance=True\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 831,
      "example_type": "python",
      "content": "# Validate memory quality\nquality_check(\n    content=\"Memory content to validate\",\n    importance=0.7\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 840,
      "example_type": "python",
      "content": "# Check for duplicates\ncheck_duplicates(\n    content=\"Content to check\",\n    threshold=0.85\n)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 898,
      "example_type": "python",
      "content": "from greeum.embedding_models import SimpleEmbeddingModel\n\nmodel = SimpleEmbeddingModel(dimension=128)\nembedding = model.encode(\"text to embed\")",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 909,
      "example_type": "python",
      "content": "from greeum.embedding_models import EmbeddingRegistry\n\nregistry = EmbeddingRegistry()\nregistry.register_model(\"custom\", custom_model, set_as_default=True)\n\n# Use registered model\nembedding = registry.get_embedding(\"text\", model_name=\"custom\")",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 923,
      "example_type": "python",
      "content": "# Requires: pip install sentence-transformers\nfrom sentence_transformers import SentenceTransformer\n\nmodel = SentenceTransformer('all-MiniLM-L6-v2')\nembeddings = model.encode([\"text1\", \"text2\"])",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 933,
      "example_type": "python",
      "content": "# Requires: pip install openai\nimport openai\n\nresponse = openai.embeddings.create(\n    model=\"text-embedding-3-small\",\n    input=\"text to embed\"\n)\nembedding = response.data[0].embedding",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 954,
      "example_type": "python",
      "content": "from greeum.text_utils import extract_keywords\n\nkeywords = extract_keywords(\"Machine learning project with Python and TensorFlow\")\n# Returns: [\"machine\", \"learning\", \"project\", \"python\", \"tensorflow\"]",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 965,
      "example_type": "python",
      "content": "from greeum.text_utils import process_user_input\n\nresult = process_user_input(\"Started working on the new API endpoints\")\n# Returns: {\n#   \"context\": \"Started working on the new API endpoints\",\n#   \"keywords\": [\"started\", \"working\", \"api\", \"endpoints\"],\n#   \"tags\": [\"work\", \"development\"],\n#   \"embedding\": [...],\n#   \"importance\": 0.6\n# }",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 982,
      "example_type": "python",
      "content": "from greeum.text_utils import detect_language\n\nlang = detect_language(\"안녕하세요 반갑습니다\")  # Returns: \"ko\"\nlang = detect_language(\"Hello, how are you?\")   # Returns: \"en\"",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 995,
      "example_type": "python",
      "content": "from greeum.exceptions import (\n    GreeumError,\n    DatabaseError, \n    EmbeddingError,\n    ValidationError\n)\n\ntry:\n    bm.add_block(context, keywords, tags, embedding, importance)\nexcept ValidationError as e:\n    print(f\"Invalid input: {e}\")\nexcept DatabaseError as e:\n    print(f\"Database error: {e}\")\nexcept GreeumError as e:\n    print(f\"General Greeum error: {e}\")",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 1017,
      "example_type": "python",
      "content": "# Always validate inputs\nif not context or len(context.strip()) < 10:\n    raise ValidationError(\"Context too short\")\n\n# Handle embedding failures gracefully\ntry:\n    embedding = get_embedding(context)\nexcept EmbeddingError:\n    embedding = simple_embedding_fallback(context)\n\n# Check for duplicates before adding\nif not detector.check_duplicates(context)['is_duplicate']:\n    bm.add_block(context, keywords, tags, embedding, importance)",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 1035,
      "example_type": "python",
      "content": "# Batch operations when possible\ncontexts = [\"text1\", \"text2\", \"text3\"]\nembeddings = embedding_model.batch_encode(contexts)\n\nfor context, embedding in zip(contexts, embeddings):\n    bm.add_block(context, keywords, tags, embedding, importance)\n\n# Use appropriate limits\nresults = bm.search_by_embedding(query_emb, top_k=20)  # Not too high\nrecent = stm.get_recent_memories(count=10)  # Reasonable count",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 715,
      "example_type": "json",
      "content": "{\n  \"version\": 1,\n  \"slots\": [\n    {\n      \"slot\": \"A\",\n      \"anchor_block_id\": \"1234\",\n      \"hop_budget\": 3,\n      \"pinned\": false,\n      \"last_used_ts\": 1693555200,\n      \"summary\": \"API development\"\n    }\n  ],\n  \"updated_at\": 1693555300\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 762,
      "example_type": "json",
      "content": "{\n  \"results\": [...],\n  \"metadata\": {\n    \"local_search_used\": true,\n    \"local_results\": 3,\n    \"fallback_used\": false,\n    \"search_time_ms\": 12.5\n  },\n  \"search_type\": \"anchor_based\",\n  \"slot\": \"A\",\n  \"radius\": 2\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 852,
      "example_type": "json",
      "content": "{\n  \"mcpServers\": {\n    \"greeum\": {\n      \"command\": \"python3\",\n      \"args\": [\"-m\", \"greeum.mcp.claude_code_mcp_server\"],\n      \"env\": {\n        \"GREEUM_DATA_DIR\": \"/path/to/data\",\n        \"GREEUM_LOG_LEVEL\": \"INFO\"\n      }\n    }\n  }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 869,
      "example_type": "json",
      "content": "{\n  \"mcpServers\": {\n    \"greeum\": {\n      \"command\": \"python3\",\n      \"args\": [\"-m\", \"greeum.mcp.claude_code_mcp_server\"],\n      \"env\": {\n        \"GREEUM_DATA_DIR\": \"/custom/data/path\",\n        \"GREEUM_LOG_LEVEL\": \"DEBUG\",\n        \"GREEUM_DB_TYPE\": \"postgresql\",\n        \"GREEUM_CONNECTION_STRING\": \"postgresql://user:pass@localhost/greeum\",\n        \"GREEUM_QUALITY_THRESHOLD\": \"0.7\",\n        \"GREEUM_DUPLICATE_THRESHOLD\": \"0.85\"\n      }\n    }\n  }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/api-reference.md",
      "line_number": 1077,
      "example_type": "json",
      "content": "{\n  \"database\": {\n    \"type\": \"sqlite\",\n    \"connection_string\": \"data/memory.db\"\n  },\n  \"embeddings\": {\n    \"default_model\": \"simple\",\n    \"cache_embeddings\": true\n  },\n  \"quality\": {\n    \"auto_validate\": true,\n    \"threshold\": 0.7,\n    \"factors\": {\n      \"length\": {\"weight\": 0.1, \"min_score\": 0.3},\n      \"richness\": {\"weight\": 0.2, \"min_score\": 0.4},\n      \"structure\": {\"weight\": 0.15, \"min_score\": 0.3}\n    }\n  },\n  \"analytics\": {\n    \"enabled\": true,\n    \"retention_days\": 90,\n    \"session_timeout\": 1800\n  },\n  \"cache\": {\n    \"max_size\": 100,\n    \"ttl\": 3600\n  }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_AI_MIGRATION_STRATEGY.md",
      "line_number": 68,
      "example_type": "python",
      "content": "class HybridMemorySystem:\n    \"\"\"v2.6.4와 v3.0.0 동시 운영\"\"\"\n    \n    def __init__(self):\n        self.legacy_db = \"data/memory.db\"      # 원본 보존\n        self.new_db = \"data/memory_v3.db\"      # 새 구조\n        self.cache_db = \"data/memory_cache.db\" # 파싱 캐시\n    \n    async def get_memory(self, memory_id: int):\n        # 1. v3.0.0에서 먼저 조회\n        v3_memory = self.get_from_v3(memory_id)\n        if v3_memory:\n            return v3_memory\n        \n        # 2. 없으면 v2.6.4에서 조회\n        v2_memory = self.get_from_legacy(memory_id)\n        if not v2_memory:\n            return None\n        \n        # 3. AI 파싱 (캐시 확인)\n        if cached := self.get_from_cache(memory_id):\n            return cached\n        \n        # 4. 새로 파싱하고 캐시\n        parsed = await self.ai_parse(v2_memory)\n        self.save_to_cache(memory_id, parsed)\n        \n        return parsed",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_AI_MIGRATION_STRATEGY.md",
      "line_number": 101,
      "example_type": "python",
      "content": "class ProgressiveMigration:\n    \"\"\"우선순위 기반 단계적 마이그레이션\"\"\"\n    \n    phases = [\n        # Phase 1: 최근 30일 메모리\n        {\"filter\": \"recent_days\", \"value\": 30},\n        \n        # Phase 2: 중요도 0.7 이상\n        {\"filter\": \"importance\", \"value\": 0.7},\n        \n        # Phase 3: 자주 접근하는 메모리\n        {\"filter\": \"access_count\", \"value\": 5},\n        \n        # Phase 4: 나머지\n        {\"filter\": \"remaining\", \"value\": None}\n    ]",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_AI_MIGRATION_STRATEGY.md",
      "line_number": 122,
      "example_type": "python",
      "content": "class FallbackSystem:\n    \"\"\"AI 실패시 대체 방안\"\"\"\n    \n    async def parse_memory(self, text: str):\n        try:\n            # 1차: AI 파싱\n            return await self.ai_parse(text)\n        except AIUnavailable:\n            # 2차: 로컬 개선 파서\n            return self.local_parse_v2(text)\n        except:\n            # 3차: 기본 구조만\n            return {\n                \"subject\": None,\n                \"action\": None,\n                \"object\": text,  # 전체를 object로\n                \"confidence\": 0.1\n            }",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_AI_MIGRATION_STRATEGY.md",
      "line_number": 145,
      "example_type": "python",
      "content": "class QualityValidator:\n    \"\"\"AI 파싱 결과 검증\"\"\"\n    \n    def validate_parsing(self, original: str, parsed: Dict) -> bool:\n        # 1. 정보 손실 체크\n        if not self.contains_key_info(original, parsed):\n            return False\n        \n        # 2. 논리적 일관성\n        if not self.is_logically_consistent(parsed):\n            return False\n        \n        # 3. 신뢰도 임계값\n        if parsed.get('confidence', 0) < 0.5:\n            return False\n        \n        return True\n    \n    def human_review_needed(self, parsed: Dict) -> bool:\n        \"\"\"인간 검토 필요 여부\"\"\"\n        return (\n            parsed['confidence'] < 0.7 or\n            parsed['subject'] is None or\n            'ambiguous' in parsed.get('metadata', {})\n        )",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line_number": 33,
      "example_type": "python",
      "content": "# greeum/mcp/tools/llm_parsing_tools.py\n\nclass LLMParsingTools:\n    \"\"\"LLM을 활용한 액탄트 파싱 도구\"\"\"\n    \n    @tool(\n        name=\"parse_memory_to_actant\",\n        description=\"Parse memory text into structured actant format\"\n    )\n    async def parse_to_actant(self, text: str) -> Dict:\n        \"\"\"\n        메모리 텍스트를 액탄트 구조로 파싱 요청\n        \n        LLM이 이 도구를 호출받으면:\n        1. 텍스트 분석\n        2. [주체-행동-객체] 추출\n        3. 신뢰도 평가\n        4. 구조화된 결과 반환\n        \"\"\"\n        \n        # LLM에게 전달될 프롬프트\n        prompt = f\"\"\"\n        다음 텍스트를 액탄트 모델로 분석해주세요:\n        \n        텍스트: \"{text}\"\n        \n        다음 형식으로 응답:\n        {{\n            \"subject\": \"주체 (누가/무엇이)\",\n            \"action\": \"행동 (무엇을 했는지)\",\n            \"object\": \"객체 (대상/목적)\",\n            \"confidence\": 0.0-1.0,\n            \"reasoning\": \"판단 근거\"\n        }}\n        \n        예시:\n        텍스트: \"사용자가 새로운 기능을 요청했다\"\n        응답: {{\n            \"subject\": \"사용자\",\n            \"action\": \"요청\",\n            \"object\": \"새로운 기능\",\n            \"confidence\": 0.95,\n            \"reasoning\": \"명시적 주체-행동-객체 구조\"\n        }}\n        \"\"\"\n        \n        # 이 부분이 핵심: LLM이 직접 파싱 수행\n        return await self.llm_request(prompt)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line_number": 86,
      "example_type": "python",
      "content": "class MemoryProcessor:\n    \"\"\"메모리 처리 파이프라인\"\"\"\n    \n    async def process_new_memory(self, text: str):\n        # Step 1: LLM 파싱 (MCP를 통해)\n        actant_data = await self.mcp_client.call_tool(\n            \"parse_memory_to_actant\",\n            {\"text\": text}\n        )\n        \n        # Step 2: 동일성 확인\n        subject_hash = await self.mcp_client.call_tool(\n            \"get_actant_hash\",\n            {\"actant\": actant_data[\"subject\"], \"type\": \"subject\"}\n        )\n        \n        # Step 3: DB 저장\n        block = self.save_to_database({\n            \"context\": text,\n            \"actant_subject\": actant_data[\"subject\"],\n            \"actant_action\": actant_data[\"action\"],\n            \"actant_object\": actant_data[\"object\"],\n            \"subject_hash\": subject_hash,\n            \"parsing_confidence\": actant_data[\"confidence\"]\n        })\n        \n        # Step 4: 관계 분석 (역시 LLM 활용)\n        relationships = await self.analyze_relationships(block)\n        \n        return block, relationships",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line_number": 121,
      "example_type": "python",
      "content": "# Claude가 실제로 수행할 작업\n\n@when_memory_added\nasync def on_memory_added(memory_text: str):\n    \"\"\"새 메모리 추가시 자동 파싱\"\"\"\n    \n    # Claude에게 파싱 요청\n    result = await claude.parse(memory_text)\n    \n    # 예시 응답\n    if memory_text == \"프로젝트가 성공해서 팀이 보너스를 받았다\":\n        return {\n            \"actants\": [\n                {\n                    \"subject\": \"프로젝트\",\n                    \"action\": \"성공\",\n                    \"object\": None,\n                    \"confidence\": 0.90\n                },\n                {\n                    \"subject\": \"팀\", \n                    \"action\": \"받다\",\n                    \"object\": \"보너스\",\n                    \"confidence\": 0.95\n                }\n            ],\n            \"causal_relation\": {\n                \"cause\": \"프로젝트 성공\",\n                \"effect\": \"팀 보너스\",\n                \"confidence\": 0.85\n            }\n        }",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line_number": 162,
      "example_type": "python",
      "content": "async def migrate_existing_memories():\n    \"\"\"기존 메모리 LLM 파싱 마이그레이션\"\"\"\n    \n    memories = get_all_memories()  # 247개\n    batch_size = 10  # API 제한 고려\n    \n    for batch in chunks(memories, batch_size):\n        # 배치 파싱 요청\n        parsing_prompt = f\"\"\"\n        다음 {len(batch)}개 메모리를 액탄트 구조로 파싱:\n        \n        {format_batch(batch)}\n        \n        각각에 대해 [주체-행동-객체] 추출\n        \"\"\"\n        \n        results = await llm_batch_parse(parsing_prompt)\n        \n        # DB 업데이트\n        for memory, result in zip(batch, results):\n            update_memory_actants(memory.id, result)\n        \n        # Rate limiting\n        await asyncio.sleep(1)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line_number": 195,
      "example_type": "python",
      "content": "async def are_same_entity(text1: str, text2: str) -> bool:\n    \"\"\"LLM에게 동일 개체 여부 판단 요청\"\"\"\n    \n    prompt = f\"\"\"\n    다음 두 표현이 같은 대상을 가리키는지 판단:\n    \n    1. \"{text1}\"\n    2. \"{text2}\"\n    \n    맥락:\n    - 개발 프로젝트 환경\n    - 한국어/영어 혼용 가능\n    - 대명사 치환 고려\n    \n    응답: {{\"same\": true/false, \"confidence\": 0.0-1.0}}\n    \"\"\"\n    \n    result = await llm_request(prompt)\n    return result[\"same\"] and result[\"confidence\"] > 0.7",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line_number": 219,
      "example_type": "python",
      "content": "async def analyze_causality(memory1: Dict, memory2: Dict) -> Dict:\n    \"\"\"LLM 기반 인과관계 분석\"\"\"\n    \n    prompt = f\"\"\"\n    두 사건의 인과관계 분석:\n    \n    사건 1: {memory1[\"actant_subject\"]}가 {memory1[\"actant_action\"]}\n    시간: {memory1[\"timestamp\"]}\n    \n    사건 2: {memory2[\"actant_subject\"]}가 {memory2[\"actant_action\"]}  \n    시간: {memory2[\"timestamp\"]}\n    \n    분석 관점:\n    1. 시간적 순서\n    2. 논리적 연결성\n    3. 주체/객체 연관성\n    \n    응답 형식:\n    {{\n        \"has_causal_relation\": true/false,\n        \"direction\": \"1→2\" or \"2→1\" or \"bidirectional\",\n        \"confidence\": 0.0-1.0,\n        \"reasoning\": \"판단 근거\"\n    }}\n    \"\"\"\n    \n    return await llm_request(prompt)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line_number": 251,
      "example_type": "python",
      "content": "async def discover_patterns(memories: List[Dict]) -> List[Pattern]:\n    \"\"\"LLM이 메모리 패턴 발견\"\"\"\n    \n    prompt = f\"\"\"\n    다음 메모리들에서 반복되는 패턴을 찾아주세요:\n    \n    {format_memories(memories)}\n    \n    찾을 패턴:\n    - 반복되는 행동 시퀀스\n    - 주기적 이벤트\n    - 인과관계 체인\n    - 협업 패턴\n    \"\"\"\n    \n    patterns = await llm_request(prompt)\n    return patterns",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line_number": 284,
      "example_type": "python",
      "content": "# Claude API 기준 (예상)\n- 파싱: $0.01 per 1K tokens\n- 247개 메모리: ~$2-3\n- 일일 신규 50개: ~$0.5/day\n- 월 비용: ~$15-20\n\n# 비용 최적화\n1. 배치 처리로 API 호출 최소화\n2. 캐싱으로 중복 파싱 방지\n3. 신뢰도 높은 결과만 재파싱",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line_number": 347,
      "example_type": "python",
      "content": "# 사용자가 메모리 추가\nUser: greeum memory add \"버그 수정 후 배포 완료\"\n\n# Claude가 자동으로 파싱\nClaude (내부):\n- 텍스트 분석 중...\n- 액탄트 추출: \n  * 주체: (암묵적 - 개발자/나)\n  * 행동: \"수정\" → \"배포\"\n  * 객체: \"버그\" → \"시스템\"\n- 인과관계: 수정 → 배포 (순차적)\n\n# 저장 결과\nMemory #251:\n- Context: \"버그 수정 후 배포 완료\"\n- Subject: \"개발자\" (inferred)\n- Actions: [\"수정\", \"배포\"]  \n- Objects: [\"버그\", \"시스템\"]\n- Causality: fix→deploy (0.9)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_CONTEXT_DEPENDENT_MEMORY.md",
      "line_number": 44,
      "example_type": "python",
      "content": "class ContextDependentMemory:\n    \"\"\"인간 기억처럼 작동하는 시스템\"\"\"\n    \n    def __init__(self):\n        # 현재 활성 컨텍스트 (STM 역할)\n        self.active_context = None\n        self.context_nodes = {}  # 활성화된 노드들\n        \n        # 전체 메모리 네트워크 (LTM)\n        self.memory_network = {}\n        self.connections = {}\n    \n    def new_context(self, trigger: str):\n        \"\"\"새로운 컨텍스트 시작 (장소 이동, 주제 변경)\"\"\"\n        \n        # 새 컨텍스트 허브 생성\n        context_id = generate_id()\n        self.active_context = {\n            'id': context_id,\n            'trigger': trigger,\n            'time': now(),\n            'active_nodes': set()\n        }\n        \n        # 이전 컨텍스트와 약한 연결\n        if self.previous_context:\n            self.connect(context_id, self.previous_context['id'], \n                        weight=0.3, type='temporal')\n    \n    def encode_memory(self, content: str):\n        \"\"\"현재 활성 컨텍스트에 메모리 기록\"\"\"\n        \n        memory_id = generate_id()\n        \n        # 1. 현재 컨텍스트에 강하게 연결\n        self.connect(memory_id, self.active_context['id'], \n                    weight=0.9, type='context')\n        \n        # 2. 현재 활성화된 다른 노드들과도 연결\n        for active_node in self.context_nodes:\n            if self.is_related(content, active_node):\n                self.connect(memory_id, active_node, \n                           weight=0.5, type='associative')\n        \n        # 3. Spreading Activation\n        self.spread_activation(memory_id)\n        \n        return memory_id\n    \n    def recall(self, cue: str):\n        \"\"\"연상 기반 회상\"\"\"\n        \n        # 1. Cue와 관련된 노드 찾기\n        activated = self.find_related_nodes(cue)\n        \n        # 2. Spreading Activation\n        for node in activated:\n            self.spread_activation(node)\n        \n        # 3. 컨텍스트도 함께 활성화\n        # \"그때 그 장소에서...\" 효과\n        contexts = self.get_node_contexts(activated)\n        for context in contexts:\n            self.activate_context(context)\n        \n        return self.get_highly_activated()",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_CONTEXT_DEPENDENT_MEMORY.md",
      "line_number": 125,
      "example_type": "python",
      "content": "class BiasAwareMemory:\n    def __init__(self):\n        self.recency_bias = 0.7  # 최근 기억 선호\n        self.frequency_bias = 0.5  # 자주 접근한 기억 선호\n        self.emotion_bias = 0.8  # 감정적 기억 선호\n    \n    def weighted_recall(self, cue: str):\n        \"\"\"편향을 고려한 회상\"\"\"\n        \n        candidates = self.find_candidates(cue)\n        \n        for memory in candidates:\n            # 기본 관련성\n            score = memory.relevance\n            \n            # Recency bias (최근일수록 강화)\n            age = now() - memory.timestamp\n            score *= (1 + self.recency_bias * exp(-age))\n            \n            # Frequency bias (자주 접근할수록 강화)\n            score *= (1 + self.frequency_bias * memory.access_count)\n            \n            # Context bias (같은 맥락일수록 강화)\n            if memory.context == self.active_context:\n                score *= 2.0\n            \n            memory.final_score = score\n        \n        return sorted(candidates, key=lambda m: m.final_score)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_CONTEXT_DEPENDENT_MEMORY.md",
      "line_number": 163,
      "example_type": "python",
      "content": "@dataclass\nclass ContextualMemory:\n    # 최소 필드\n    memory_id: str\n    content: str\n    context_id: str  # 어느 컨텍스트에서 생성됐나\n    timestamp: float\n    \n    # 동적 필드\n    activation: float = 0.0\n    access_count: int = 0\n\nclass MemorySystem:\n    def __init__(self):\n        # 활성 컨텍스트 (STM 역할)\n        self.active_context = None\n        self.activation_buffer = {}  # 현재 활성화된 노드들\n        \n        # 메모리 저장소 (LTM)\n        self.memories = {}\n        self.contexts = {}\n        self.edges = {}  # (from, to) -> weight\n    \n    def process_input(self, text: str):\n        \"\"\"새 입력 처리\"\"\"\n        \n        # 1. 컨텍스트 전환 감지\n        if self.should_switch_context(text):\n            self.create_new_context(text)\n        \n        # 2. 현재 컨텍스트에 메모리 추가\n        mem = ContextualMemory(\n            memory_id=generate_id(),\n            content=text,\n            context_id=self.active_context,\n            timestamp=now()\n        )\n        \n        # 3. 자동 연결 (현재 활성화된 것들과)\n        for active_id in self.activation_buffer:\n            if self.activation_buffer[active_id] > 0.3:\n                weight = self.compute_relevance(text, self.memories[active_id].content)\n                self.edges[(mem.memory_id, active_id)] = weight\n        \n        # 4. 활성화 전파\n        self.spread_activation(mem.memory_id)\n        \n        return mem",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_CONTEXT_DEPENDENT_MEMORY.md",
      "line_number": 216,
      "example_type": "python",
      "content": "def compute_relevance(self, text1: str, text2: str) -> float:\n    \"\"\"AI가 관련성 판단, 구조는 우리가 관리\"\"\"\n    \n    # MCP를 통해 Claude/GPT에게\n    relevance = ai.evaluate_relevance(text1, text2)\n    \n    # 하지만 구조적 요인도 고려\n    if same_context:\n        relevance *= 1.5\n    if temporal_proximity:\n        relevance *= 1.2\n    \n    return min(1.0, relevance)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_CLEAN_SLATE_DESIGN.md",
      "line_number": 22,
      "example_type": "python",
      "content": "@dataclass\nclass V3Memory:\n    \"\"\"AI가 직접 작성하는 메모리 구조\"\"\"\n    \n    # Core Identity\n    memory_id: str\n    timestamp: datetime\n    \n    # Actant Structure (AI가 직접 파싱)\n    subject: str          # 누가\n    action: str           # 무엇을\n    object: str           # 누구에게/무엇에\n    \n    # Extended Actants (AI가 추론)\n    sender: Optional[str]     # 요청자\n    receiver: Optional[str]   # 수혜자\n    context: Optional[str]    # 상황/배경\n    \n    # AI Analysis\n    intent: str              # AI가 파악한 의도\n    emotion: str             # AI가 감지한 감정\n    importance: float        # AI가 판단한 중요도\n    \n    # Relations (AI가 발견)\n    causes: List[str]        # 원인이 되는 메모리들\n    effects: List[str]       # 결과가 되는 메모리들\n    related: List[str]       # 연관된 메모리들\n    \n    # Raw\n    original_text: str       # 원본 보존",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_CLEAN_SLATE_DESIGN.md",
      "line_number": 57,
      "example_type": "python",
      "content": "# greeum/mcp/v3_tools.py\n\nclass V3MemoryTools:\n    \"\"\"v3.0.0 전용 MCP 도구\"\"\"\n    \n    @tool(name=\"v3_add_memory\")\n    async def add_structured_memory(\n        self,\n        text: str,\n        context: Optional[str] = None\n    ) -> Dict:\n        \"\"\"\n        AI가 텍스트를 분석해서 구조화된 메모리 생성\n        \n        AI가 수행할 작업:\n        1. 액탄트 구조 파싱\n        2. 의도와 감정 분석\n        3. 중요도 판단\n        4. 기존 메모리와의 관계 파악\n        \"\"\"\n        \n        # AI가 직접 채움 (MCP 환경에서)\n        memory = {\n            \"subject\": \"AI가 파싱한 주체\",\n            \"action\": \"AI가 파싱한 행동\",\n            \"object\": \"AI가 파싱한 객체\",\n            \"intent\": \"AI가 분석한 의도\",\n            \"emotion\": \"AI가 감지한 감정\",\n            \"importance\": 0.0,  # AI가 판단\n            \"causes\": [],       # AI가 찾은 원인들\n            \"effects\": [],      # AI가 예측한 결과들\n            \"original_text\": text\n        }\n        \n        return self.save_v3_memory(memory)\n    \n    @tool(name=\"v3_search_semantic\")\n    async def search_by_meaning(\n        self,\n        query: str,\n        limit: int = 10\n    ) -> List[Dict]:\n        \"\"\"\n        AI가 의미 기반으로 검색\n        단순 키워드가 아닌 의도 파악\n        \"\"\"\n        # AI가 쿼리 의도 파악\n        intent = \"AI가 파악한 검색 의도\"\n        \n        # 의미적으로 관련된 메모리 찾기\n        results = self.semantic_search(intent)\n        \n        return results\n    \n    @tool(name=\"v3_analyze_patterns\")\n    async def find_patterns(\n        self,\n        time_range: Optional[str] = None\n    ) -> Dict:\n        \"\"\"\n        AI가 메모리 패턴 분석\n        \"\"\"\n        patterns = {\n            \"recurring_subjects\": [],  # 반복되는 주체\n            \"common_actions\": [],       # 자주 하는 행동\n            \"causal_chains\": [],        # 인과 관계 체인\n            \"emotional_trends\": []      # 감정 변화 추이\n        }\n        \n        return patterns",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_CLEAN_SLATE_DESIGN.md",
      "line_number": 132,
      "example_type": "python",
      "content": "# Claude/AI가 직접 실행하는 코드\n\n# 1. 새 메모리 추가시\nuser_text = \"버그 수정 완료했고 배포 준비 중\"\n\n# AI가 직접 분석해서 저장\nmemory = await mcp.v3_add_memory(\n    text=user_text,\n    context=\"프로젝트 마무리 단계\"\n)\n\n# AI가 채운 구조:\n{\n    \"subject\": \"개발자\",      # AI가 추론\n    \"action\": \"수정\",\n    \"object\": \"버그\",\n    \"intent\": \"작업 완료 보고\",\n    \"emotion\": \"성취감\",\n    \"importance\": 0.75,\n    \"causes\": [\"memory_245\"],  # 이전 버그 리포트\n    \"effects\": [\"memory_262\"], # 배포 관련\n    \"original_text\": \"버그 수정 완료했고 배포 준비 중\"\n}\n\n# 2. 검색시\nresults = await mcp.v3_search_semantic(\n    query=\"최근에 해결한 문제들\"\n)\n# AI가 \"해결한 문제\"의 의미를 이해하고 관련 메모리 반환\n\n# 3. 패턴 분석\npatterns = await mcp.v3_analyze_patterns(\n    time_range=\"last_week\"\n)\n# AI가 일주일간의 행동 패턴 분석",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_CLEAN_SLATE_DESIGN.md",
      "line_number": 229,
      "example_type": "python",
      "content": "# 1. 새 DB 파일 생성\nv3_db = \"data/greeum_v3.db\"\n\n# 2. 테이블 생성\ncreate_v3_tables()\n\n# 3. MCP 도구 등록\nregister_v3_tools()",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_CLEAN_SLATE_DESIGN.md",
      "line_number": 241,
      "example_type": "python",
      "content": "# Claude/GPT가 직접 사용할 도구들\n- v3_add_memory()      # 구조화 저장\n- v3_search_semantic() # 의미 검색\n- v3_find_relations()  # 관계 발견\n- v3_analyze_patterns() # 패턴 분석",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_CLEAN_SLATE_DESIGN.md",
      "line_number": 250,
      "example_type": "python",
      "content": "# 모든 새 메모리는 v3로\n# v2.x는 읽기 전용으로 남김\n# 필요하면 AI가 v2 메모리 읽어서 v3로 재저장",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_NEURAL_MEMORY_DESIGN.md",
      "line_number": 19,
      "example_type": "python",
      "content": "@dataclass\nclass MemoryNode:\n    \"\"\"가장 단순한 메모리 단위\"\"\"\n    \n    node_id: str          # 고유 ID\n    content: str          # 원본 텍스트 그대로\n    timestamp: datetime   # 언제\n    activation: float = 0.0  # 현재 활성화 수준\n    \n    # 그게 다임. 진짜로.",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_NEURAL_MEMORY_DESIGN.md",
      "line_number": 34,
      "example_type": "python",
      "content": "@dataclass  \nclass Connection:\n    \"\"\"메모리 간 연결\"\"\"\n    \n    from_node: str      # 출발 노드\n    to_node: str        # 도착 노드\n    weight: float       # 연결 강도 (-1 ~ 1)\n    created_by: str     # 'temporal', 'semantic', 'causal', 'user'\n    \n    # 역시 그게 다임.",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_NEURAL_MEMORY_DESIGN.md",
      "line_number": 49,
      "example_type": "python",
      "content": "class NeuralMemory:\n    \"\"\"신경망처럼 작동하는 메모리\"\"\"\n    \n    def activate(self, text: str):\n        \"\"\"새 입력이 들어오면\"\"\"\n        \n        # 1. 새 노드 생성\n        new_node = MemoryNode(\n            node_id=generate_id(),\n            content=text,\n            timestamp=now(),\n            activation=1.0  # 새 메모리는 최대 활성화\n        )\n        \n        # 2. 기존 노드들과 연결 생성\n        for existing in self.nodes:\n            similarity = self.ai_compute_similarity(text, existing.content)\n            if similarity > 0.3:  # 임계값\n                self.connect(new_node, existing, weight=similarity)\n        \n        # 3. 활성화 전파 (Spreading Activation)\n        self.propagate_activation(new_node)\n        \n        return new_node\n    \n    def propagate_activation(self, source_node, depth=3):\n        \"\"\"활성화가 네트워크를 따라 퍼짐\"\"\"\n        \n        current_layer = [source_node]\n        \n        for _ in range(depth):\n            next_layer = []\n            for node in current_layer:\n                # 연결된 노드들에게 활성화 전달\n                for conn in self.get_connections(node):\n                    target = self.get_node(conn.to_node)\n                    # 활성화 전달 (가중치 곱하고 감쇠)\n                    target.activation += node.activation * conn.weight * 0.5\n                    next_layer.append(target)\n            current_layer = next_layer\n    \n    def recall(self, query: str, top_k=5):\n        \"\"\"기억 회상\"\"\"\n        \n        # 1. 쿼리를 임시 노드로\n        query_node = MemoryNode(\"temp\", query, now(), 1.0)\n        \n        # 2. 활성화 전파\n        self.propagate_activation(query_node)\n        \n        # 3. 가장 활성화된 노드들 반환\n        return sorted(self.nodes, key=lambda n: n.activation, reverse=True)[:top_k]",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_NEURAL_MEMORY_DESIGN.md",
      "line_number": 110,
      "example_type": "python",
      "content": "def detect_temporal_causality(self, time_window=3600):  # 1시간\n    \"\"\"시간적으로 가까운 메모리들을 연결\"\"\"\n    \n    for i, node1 in enumerate(self.nodes):\n        for node2 in self.nodes[i+1:]:\n            time_diff = abs(node2.timestamp - node1.timestamp)\n            \n            if time_diff < time_window:\n                # 시간적으로 가까우면 약한 인과관계 가능성\n                weight = 1.0 - (time_diff / time_window)  # 가까울수록 강함\n                self.connect(node1, node2, weight * 0.3, 'temporal')",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_NEURAL_MEMORY_DESIGN.md",
      "line_number": 126,
      "example_type": "python",
      "content": "def detect_semantic_causality(self):\n    \"\"\"AI가 의미적 연결 발견\"\"\"\n    \n    for node1 in self.nodes:\n        for node2 in self.nodes:\n            # AI에게 물어봄: 이 둘이 인과관계인가?\n            prompt = f\"\"\"\n            A: {node1.content}\n            B: {node2.content}\n            \n            A가 B의 원인일 가능성은? (0-1)\n            \"\"\"\n            \n            causality_score = self.ai_evaluate(prompt)\n            \n            if causality_score > 0.5:\n                self.connect(node1, node2, causality_score, 'causal')",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_NEURAL_MEMORY_DESIGN.md",
      "line_number": 148,
      "example_type": "python",
      "content": "def learn_patterns(self):\n    \"\"\"반복되는 패턴을 찾아 연결 강화\"\"\"\n    \n    # 자주 함께 활성화되는 노드들\n    co_activation_counts = {}\n    \n    for session in self.activation_history:\n        activated_nodes = session.get_activated_nodes()\n        for n1, n2 in combinations(activated_nodes, 2):\n            pair = tuple(sorted([n1.id, n2.id]))\n            co_activation_counts[pair] = co_activation_counts.get(pair, 0) + 1\n    \n    # 자주 함께 활성화되면 연결 강화\n    for (n1_id, n2_id), count in co_activation_counts.items():\n        if count > 3:  # 3번 이상 함께 활성화\n            self.strengthen_connection(n1_id, n2_id, delta=0.1)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_NEURAL_MEMORY_DESIGN.md",
      "line_number": 215,
      "example_type": "python",
      "content": "# 사용 예시\nmemory = NeuralMemory()\n\n# 메모리 추가 (자동으로 연결됨)\nmemory.activate(\"버그를 발견했다\")\nmemory.activate(\"버그를 수정했다\")  # 자동으로 이전 메모리와 연결\nmemory.activate(\"테스트 통과했다\")  # 역시 연결\n\n# 회상\nresults = memory.recall(\"버그 관련해서 뭐 했었지?\")\n# → 활성화가 퍼져서 관련 메모리들이 모두 떠오름\n\n# 인과관계 추론\nchain = memory.trace_causal_chain(\"테스트 통과\")\n# → \"버그 발견\" → \"버그 수정\" → \"테스트 통과\"",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_IMPLEMENTATION_PLAN.md",
      "line_number": 28,
      "example_type": "python",
      "content": "# greeum/core/active_context.py\n\nfrom greeum.stm_manager import STMManager\n\nclass ActiveContextManager(STMManager):\n    \"\"\"STMManager를 확장해서 Active Context로\"\"\"\n    \n    def __init__(self, db_manager):\n        super().__init__(db_manager)\n        \n        # 추가 필드\n        self.current_context_id = None\n        self.context_trigger = None  # 무엇이 이 컨텍스트를 시작했나\n        self.active_nodes = {}  # {node_id: activation_level}\n        self.context_start_time = None\n    \n    def switch_context(self, trigger: str):\n        \"\"\"컨텍스트 전환 (기존 flush_to_ltm 활용)\"\"\"\n        \n        # 기존 컨텍스트 저장\n        if self.current_context_id:\n            self.save_context_to_ltm()\n        \n        # 새 컨텍스트 시작\n        self.current_context_id = f\"ctx_{time.time()}\"\n        self.context_trigger = trigger\n        self.context_start_time = time.time()\n        self.active_nodes = {}\n        \n        logger.info(f\"Context switched: {trigger}\")\n    \n    def add_memory(self, content: str, **kwargs):\n        \"\"\"메모리 추가시 자동으로 현재 컨텍스트에 연결\"\"\"\n        \n        # 기존 STM 추가 로직\n        memory_id = super().add_memory(content, **kwargs)\n        \n        # 현재 활성 노드들과 연결\n        for active_id, activation in self.active_nodes.items():\n            if activation > 0.3:  # 임계값\n                # 연결 생성 (새 테이블에)\n                self._create_connection(memory_id, active_id, activation * 0.5)\n        \n        # 이 메모리도 활성화\n        self.active_nodes[memory_id] = 1.0\n        \n        return memory_id",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_IMPLEMENTATION_PLAN.md",
      "line_number": 80,
      "example_type": "python",
      "content": "# greeum/core/database_manager.py 에 추가\n\ndef _create_v3_context_tables(self):\n    \"\"\"v3 테이블 추가 (기존 테이블은 그대로)\"\"\"\n    \n    cursor = self.conn.cursor()\n    \n    # 컨텍스트 테이블\n    cursor.execute('''\n        CREATE TABLE IF NOT EXISTS contexts (\n            context_id TEXT PRIMARY KEY,\n            trigger TEXT,\n            start_time REAL,\n            end_time REAL,\n            memory_count INTEGER DEFAULT 0,\n            metadata TEXT\n        )\n    ''')\n    \n    # 메모리 연결 테이블 (네트워크 구조)\n    cursor.execute('''\n        CREATE TABLE IF NOT EXISTS memory_connections (\n            from_memory INTEGER,\n            to_memory INTEGER,\n            weight REAL DEFAULT 0.5,\n            connection_type TEXT,  -- 'context', 'semantic', 'temporal'\n            created_at REAL,\n            context_id TEXT,\n            PRIMARY KEY (from_memory, to_memory),\n            FOREIGN KEY (from_memory) REFERENCES blocks(block_index),\n            FOREIGN KEY (to_memory) REFERENCES blocks(block_index),\n            FOREIGN KEY (context_id) REFERENCES contexts(context_id)\n        )\n    ''')\n    \n    # 활성화 로그 (학습용)\n    cursor.execute('''\n        CREATE TABLE IF NOT EXISTS activation_log (\n            memory_id INTEGER,\n            activation_level REAL,\n            context_id TEXT,\n            timestamp REAL,\n            trigger_memory INTEGER\n        )\n    ''')\n    \n    # 인덱스\n    cursor.execute('CREATE INDEX IF NOT EXISTS idx_connections_context ON memory_connections(context_id)')\n    cursor.execute('CREATE INDEX IF NOT EXISTS idx_connections_weight ON memory_connections(weight)')",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_IMPLEMENTATION_PLAN.md",
      "line_number": 134,
      "example_type": "python",
      "content": "# greeum/core/activation_engine.py\n\nclass ActivationEngine:\n    \"\"\"간단한 Spreading Activation\"\"\"\n    \n    def __init__(self, db_manager):\n        self.db = db_manager\n        self.decay_rate = 0.5\n        self.threshold = 0.1\n    \n    def activate(self, source_memory_id: int, depth: int = 3):\n        \"\"\"메모리 활성화 전파\"\"\"\n        \n        activations = {source_memory_id: 1.0}\n        current_layer = [source_memory_id]\n        \n        for d in range(depth):\n            next_layer = []\n            \n            for memory_id in current_layer:\n                # 연결된 메모리 찾기\n                connections = self.db.get_connections(memory_id)\n                \n                for conn in connections:\n                    target_id = conn['to_memory']\n                    spread = activations[memory_id] * conn['weight'] * self.decay_rate\n                    \n                    if spread > self.threshold:\n                        if target_id not in activations:\n                            activations[target_id] = 0\n                        activations[target_id] += spread\n                        next_layer.append(target_id)\n            \n            current_layer = next_layer\n            if not current_layer:\n                break\n        \n        return activations",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_IMPLEMENTATION_PLAN.md",
      "line_number": 177,
      "example_type": "python",
      "content": "# greeum/search_engine.py 수정\n\nclass EnhancedSearchEngine(SearchEngine):\n    \"\"\"기존 검색 + 네트워크 기반 연상\"\"\"\n    \n    def __init__(self, *args, **kwargs):\n        super().__init__(*args, **kwargs)\n        self.activation_engine = ActivationEngine(self.db_manager)\n    \n    def search_with_context(self, query: str, use_activation: bool = True):\n        \"\"\"컨텍스트 인식 검색\"\"\"\n        \n        # 1. 기존 검색 (키워드, 임베딩)\n        base_results = self.search(query)\n        \n        if not use_activation:\n            return base_results\n        \n        # 2. 활성화 전파\n        all_activations = {}\n        for result in base_results[:3]:  # 상위 3개만\n            memory_id = result['block_index']\n            activations = self.activation_engine.activate(memory_id)\n            \n            for mem_id, level in activations.items():\n                if mem_id not in all_activations:\n                    all_activations[mem_id] = 0\n                all_activations[mem_id] += level\n        \n        # 3. 활성화된 메모리 추가\n        activated_memories = []\n        for mem_id, activation in all_activations.items():\n            if activation > 0.2:  # 임계값\n                memory = self.db_manager.get_block(mem_id)\n                if memory:\n                    memory['activation_score'] = activation\n                    activated_memories.append(memory)\n        \n        # 4. 통합 결과\n        return self._merge_results(base_results, activated_memories)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_IMPLEMENTATION_PLAN.md",
      "line_number": 226,
      "example_type": "python",
      "content": "class MigrationBridge:\n    \"\"\"사용하면서 점진적 마이그레이션\"\"\"\n    \n    def __init__(self):\n        self.v2_db = DatabaseManager()  # 기존\n        self.context_manager = ActiveContextManager(self.v2_db)\n        self.processed = set()\n    \n    def get_memory(self, memory_id: int):\n        \"\"\"메모리 조회시 자동 연결 생성\"\"\"\n        \n        memory = self.v2_db.get_block(memory_id)\n        \n        if memory_id not in self.processed:\n            # 첫 접근시 연결 생성\n            self._create_connections_for(memory)\n            self.processed.add(memory_id)\n        \n        return memory\n    \n    def _create_connections_for(self, memory):\n        \"\"\"과거 메모리에 대한 연결 추론\"\"\"\n        \n        # 시간적으로 가까운 메모리\n        timestamp = memory['timestamp']\n        nearby = self.v2_db.get_blocks_by_time_range(\n            timestamp - 3600, \n            timestamp + 3600\n        )\n        \n        for other in nearby:\n            if other['block_index'] != memory['block_index']:\n                # 간단한 연결 생성\n                weight = 0.3 * (1 - abs(timestamp - other['timestamp']) / 3600)\n                self.v2_db.create_connection(\n                    memory['block_index'],\n                    other['block_index'],\n                    weight,\n                    'temporal'\n                )",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_IMPLEMENTATION_PLAN.md",
      "line_number": 271,
      "example_type": "python",
      "content": "class DualModeMemory:\n    \"\"\"v2.6.4와 v3.0 동시 운영\"\"\"\n    \n    def __init__(self):\n        self.legacy_mode = BlockManager()  # v2.6.4\n        self.context_mode = ContextMemory()  # v3.0\n        self.mode = 'dual'  # 'legacy', 'context', 'dual'\n    \n    def add_memory(self, content: str):\n        \"\"\"두 시스템에 모두 저장\"\"\"\n        \n        if self.mode in ['legacy', 'dual']:\n            self.legacy_mode.add_block(content)\n        \n        if self.mode in ['context', 'dual']:\n            self.context_mode.add_memory(content)\n    \n    def search(self, query: str):\n        \"\"\"두 시스템 모두 검색\"\"\"\n        \n        results = []\n        \n        if self.mode in ['legacy', 'dual']:\n            results.extend(self.legacy_mode.search(query))\n        \n        if self.mode in ['context', 'dual']:\n            context_results = self.context_mode.search_with_activation(query)\n            results.extend(context_results)\n        \n        return self._deduplicate(results)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_IMPLEMENTATION_PLAN.md",
      "line_number": 337,
      "example_type": "python",
      "content": "# 최소 변경으로 최대 효과\nclass MinimalChange:\n    \"\"\"정말 필요한 것만 추가\"\"\"\n    \n    def __init__(self):\n        # 기존 그대로\n        self.block_manager = BlockManager()\n        self.stm_manager = STMManager()\n        \n        # 새로 추가\n        self.connections = {}  # 메모리 연결\n        self.active_context = None  # 현재 컨텍스트\n    \n    def add_memory_v3(self, content):\n        \"\"\"v3 방식 추가\"\"\"\n        \n        # 1. 기존 방식으로 저장\n        block_id = self.block_manager.add_block(content)\n        \n        # 2. 현재 컨텍스트에 연결 (새 기능)\n        if self.active_context:\n            for active_id in self.active_context:\n                self.connections[(block_id, active_id)] = 0.5\n        \n        # 3. 활성화 (새 기능)\n        self.spread_activation(block_id)\n        \n        return block_id",
      "expected_output": null
    },
    {
      "file_path": "docs/design/actant_identity_system_design.md",
      "line_number": 10,
      "example_type": "python",
      "content": "exact_match = {\n    \"subjects\": {\n        \"user_hash_001\": [\"사용자\", \"유저\", \"user\"],\n        \"claude_hash_002\": [\"Claude\", \"claude\", \"AI\", \"어시스턴트\"],\n        \"team_hash_003\": [\"팀\", \"team\", \"개발팀\"]\n    },\n    \"actions\": {\n        \"request_hash_001\": [\"요청\", \"request\", \"부탁\"],\n        \"implement_hash_002\": [\"구현\", \"개발\", \"implement\", \"develop\"],\n        \"complete_hash_003\": [\"완료\", \"완성\", \"complete\", \"finish\"]\n    },\n    \"objects\": {\n        \"project_hash_001\": [\"프로젝트\", \"project\", \"작업\"],\n        \"prototype_hash_002\": [\"프로토타입\", \"prototype\", \"시제품\"]\n    }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/design/actant_identity_system_design.md",
      "line_number": 30,
      "example_type": "python",
      "content": "pattern_rules = {\n    \"subject_patterns\": [\n        r\"^(사용자|유저|user).*$\",  # 사용자 관련\n        r\"^(개발자|dev|developer).*$\",  # 개발자 관련\n        r\"^(팀|team).*$\"  # 팀 관련\n    ],\n    \"action_patterns\": [\n        r\".*요청.*|.*request.*\",  # 요청 행동\n        r\".*구현.*|.*개발.*|.*implement.*|.*develop.*\",  # 개발 행동\n        r\".*완료.*|.*완성.*|.*complete.*|.*finish.*\"  # 완료 행동\n    ]\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/design/actant_identity_system_design.md",
      "line_number": 46,
      "example_type": "python",
      "content": "# 간단한 임베딩 유사도 (코사인 유사도 > 0.7)\nsemantic_threshold = 0.7",
      "expected_output": null
    },
    {
      "file_path": "docs/design/actant_identity_system_design.md",
      "line_number": 54,
      "example_type": "python",
      "content": "class ActantHashManager:\n    def __init__(self):\n        # 수동으로 정의된 핵심 액탄트들\n        self.subject_hashes = {\n            \"user\": [\"사용자\", \"유저\", \"나\", \"내가\", \"user\"],\n            \"claude\": [\"Claude\", \"claude\", \"AI\", \"어시스턴트\", \"assistant\"],\n            \"team\": [\"팀\", \"team\", \"개발팀\", \"우리팀\"],\n            \"system\": [\"시스템\", \"system\", \"서버\", \"프로그램\"]\n        }\n        \n        self.action_hashes = {\n            \"request\": [\"요청\", \"부탁\", \"request\", \"ask\"],\n            \"implement\": [\"구현\", \"개발\", \"만들기\", \"코딩\", \"implement\", \"develop\", \"code\"],\n            \"complete\": [\"완료\", \"완성\", \"끝\", \"complete\", \"finish\", \"done\"],\n            \"test\": [\"테스트\", \"확인\", \"검증\", \"test\", \"verify\", \"check\"],\n            \"fix\": [\"수정\", \"고치기\", \"fix\", \"repair\", \"debug\"]\n        }\n        \n        self.object_hashes = {\n            \"project\": [\"프로젝트\", \"project\", \"작업\", \"일\"],\n            \"feature\": [\"기능\", \"feature\", \"함수\", \"function\"],\n            \"bug\": [\"버그\", \"bug\", \"오류\", \"error\", \"문제\"],\n            \"code\": [\"코드\", \"code\", \"소스\", \"프로그램\"],\n            \"api\": [\"API\", \"api\", \"인터페이스\", \"interface\"]\n        }\n    \n    def get_subject_hash(self, subject_text: str) -> str:\n        for hash_key, variants in self.subject_hashes.items():\n            if any(variant.lower() in subject_text.lower() for variant in variants):\n                return f\"subject_{hash_key}\"\n        return f\"subject_unknown_{hash(subject_text)}\"\n    \n    def get_action_hash(self, action_text: str) -> str:\n        for hash_key, variants in self.action_hashes.items():\n            if any(variant.lower() in action_text.lower() for variant in variants):\n                return f\"action_{hash_key}\"\n        return f\"action_unknown_{hash(action_text)}\"\n    \n    def get_object_hash(self, object_text: str) -> str:\n        for hash_key, variants in self.object_hashes.items():\n            if any(variant.lower() in object_text.lower() for variant in variants):\n                return f\"object_{hash_key}\"\n        return f\"object_unknown_{hash(object_text)}\"",
      "expected_output": null
    },
    {
      "file_path": "docs/design/actant_identity_system_design.md",
      "line_number": 101,
      "example_type": "python",
      "content": "def normalize_actant(text: str, actant_type: str) -> str:\n    \"\"\"액탄트 텍스트를 정규화된 해시로 변환\"\"\"\n    \n    # 1단계: 기본 전처리\n    text = text.lower().strip()\n    text = re.sub(r'[^\\w\\s가-힣]', '', text)  # 특수문자 제거\n    \n    # 2단계: 패턴 매칭\n    if actant_type == \"subject\":\n        if any(word in text for word in [\"사용자\", \"유저\", \"user\", \"나\", \"내가\"]):\n            return \"subject_user\"\n        elif any(word in text for word in [\"claude\", \"ai\", \"어시스턴트\"]):\n            return \"subject_claude\"\n        elif any(word in text for word in [\"팀\", \"team\", \"개발팀\"]):\n            return \"subject_team\"\n    \n    # 3단계: 기본 해시 (매칭 실패시)\n    return f\"{actant_type}_{hashlib.md5(text.encode()).hexdigest()[:8]}\"",
      "expected_output": null
    },
    {
      "file_path": "docs/design/actant_identity_system_design.md",
      "line_number": 123,
      "example_type": "python",
      "content": "class AdaptiveActantMatcher:\n    def __init__(self):\n        self.feedback_data = []  # 사용자 피드백 저장\n        \n    def add_feedback(self, actant1: str, actant2: str, is_same: bool):\n        \"\"\"사용자 피드백으로 매칭 정확도 개선\"\"\"\n        self.feedback_data.append({\n            \"actant1\": actant1,\n            \"actant2\": actant2, \n            \"is_same\": is_same,\n            \"timestamp\": datetime.now()\n        })\n        \n    def learn_patterns(self):\n        \"\"\"피드백 데이터로 매칭 패턴 학습\"\"\"\n        # 간단한 규칙 학습 로직\n        pass",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ARCHITECTURE_DESIGN.md",
      "line_number": 156,
      "example_type": "python",
      "content": "class AssociationNetwork:\n    \"\"\"\n    메모리 노드 간 연상 관계를 관리하는 핵심 엔진\n    \"\"\"\n    \n    def __init__(self, db_manager):\n        self.db = db_manager\n        self.cache = AssociationCache()  # 자주 사용되는 연결 캐싱\n        \n    def create_association(self, source_id: int, target_id: int, \n                         assoc_type: str, strength: float = 0.5):\n        \"\"\"두 노드 간 연상 연결 생성\"\"\"\n        # 중복 체크\n        if self.has_association(source_id, target_id, assoc_type):\n            return self.strengthen_association(source_id, target_id, strength * 0.1)\n        \n        # 새 연결 생성\n        self.db.execute(\"\"\"\n            INSERT INTO associations (source_node, target_node, assoc_type, strength)\n            VALUES (?, ?, ?, ?)\n        \"\"\", (source_id, target_id, assoc_type, strength))\n        \n        # 캐시 무효화\n        self.cache.invalidate(source_id)\n        \n    def find_associations(self, node_id: int, max_depth: int = 2) -> Dict:\n        \"\"\"\n        특정 노드에서 시작하는 연상 네트워크 탐색\n        BFS 방식으로 depth만큼 확장\n        \"\"\"\n        visited = set()\n        network = {\n            \"center\": node_id,\n            \"layers\": []\n        }\n        \n        current_layer = [node_id]\n        \n        for depth in range(max_depth):\n            next_layer = []\n            layer_associations = []\n            \n            for current_node in current_layer:\n                if current_node in visited:\n                    continue\n                    \n                visited.add(current_node)\n                \n                # 현재 노드의 모든 연결 조회\n                associations = self.db.query(\"\"\"\n                    SELECT target_node, assoc_type, strength\n                    FROM associations\n                    WHERE source_node = ?\n                    ORDER BY strength DESC\n                    LIMIT 10\n                \"\"\", (current_node,))\n                \n                for assoc in associations:\n                    if assoc['target_node'] not in visited:\n                        next_layer.append(assoc['target_node'])\n                        layer_associations.append({\n                            \"from\": current_node,\n                            \"to\": assoc['target_node'],\n                            \"type\": assoc['assoc_type'],\n                            \"strength\": assoc['strength']\n                        })\n            \n            if layer_associations:\n                network[\"layers\"].append({\n                    \"depth\": depth + 1,\n                    \"associations\": layer_associations\n                })\n            \n            current_layer = next_layer\n            \n        return network\n    \n    def strengthen_association(self, source_id: int, target_id: int, delta: float):\n        \"\"\"연결 강도 증가 (사용할수록 강해짐)\"\"\"\n        self.db.execute(\"\"\"\n            UPDATE associations \n            SET strength = MIN(1.0, strength + ?),\n                activation_count = activation_count + 1,\n                last_activated = CURRENT_TIMESTAMP\n            WHERE source_node = ? AND target_node = ?\n        \"\"\", (delta, source_id, target_id))\n    \n    def decay_associations(self, decay_rate: float = 0.95):\n        \"\"\"시간에 따른 연결 강도 감쇠 (미사용 연결 약화)\"\"\"\n        self.db.execute(\"\"\"\n            UPDATE associations\n            SET strength = strength * ?\n            WHERE last_activated < datetime('now', '-7 days')\n        \"\"\", (decay_rate,))",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ARCHITECTURE_DESIGN.md",
      "line_number": 255,
      "example_type": "python",
      "content": "class SpreadingActivation:\n    \"\"\"\n    하나의 기억이 활성화되면 연관된 기억들도 함께 활성화\n    인간의 연상 작용을 모방\n    \"\"\"\n    \n    def __init__(self, network: AssociationNetwork):\n        self.network = network\n        self.activation_threshold = 0.3  # 최소 활성화 수준\n        self.decay_factor = 0.7  # 거리에 따른 감쇠\n        \n    def activate(self, trigger_nodes: List[int], session_id: str) -> Dict[int, float]:\n        \"\"\"\n        트리거 노드들로부터 활성화 확산\n        \n        Returns:\n            {node_id: activation_level} 형태의 활성화 맵\n        \"\"\"\n        activation_map = {}\n        \n        # 초기 활성화 (트리거 노드들은 1.0)\n        for node in trigger_nodes:\n            activation_map[node] = 1.0\n            self._record_activation(session_id, node, 1.0, None)\n        \n        # 3단계까지 확산\n        for depth in range(1, 4):\n            new_activations = {}\n            decay = self.decay_factor ** depth\n            \n            for active_node, activation_level in activation_map.items():\n                if activation_level < self.activation_threshold:\n                    continue\n                \n                # 연결된 노드들 활성화\n                associations = self.network.find_associations(active_node, max_depth=1)\n                \n                for layer in associations.get(\"layers\", []):\n                    for assoc in layer[\"associations\"]:\n                        target = assoc[\"to\"]\n                        \n                        # 연결 강도와 거리를 고려한 활성화 수준 계산\n                        propagated_activation = activation_level * assoc[\"strength\"] * decay\n                        \n                        if target not in activation_map:\n                            new_activations[target] = propagated_activation\n                        else:\n                            # 여러 경로로 활성화되면 최대값 사용\n                            new_activations[target] = max(\n                                new_activations.get(target, 0),\n                                propagated_activation\n                            )\n            \n            # 새로 활성화된 노드들 기록\n            for node, level in new_activations.items():\n                if level >= self.activation_threshold:\n                    activation_map[node] = level\n                    self._record_activation(session_id, node, level, active_node)\n        \n        return activation_map\n    \n    def _record_activation(self, session_id: str, node_id: int, \n                          level: float, trigger: Optional[int]):\n        \"\"\"활성화 이력 기록\"\"\"\n        self.network.db.execute(\"\"\"\n            INSERT INTO activation_history \n            (session_id, node_id, activation_level, trigger_node)\n            VALUES (?, ?, ?, ?)\n        \"\"\", (session_id, node_id, level, trigger))",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ARCHITECTURE_DESIGN.md",
      "line_number": 329,
      "example_type": "python",
      "content": "class ContextManager:\n    \"\"\"\n    대화/작업의 맥락을 추적하고 관련 기억을 지속적으로 제공\n    \"\"\"\n    \n    def __init__(self, network: AssociationNetwork, activation: SpreadingActivation):\n        self.network = network\n        self.activation = activation\n        self.active_context = {}\n        \n    def start_session(self, session_type: str = \"conversation\") -> str:\n        \"\"\"새 맥락 세션 시작\"\"\"\n        session_id = self._generate_session_id()\n        \n        self.network.db.execute(\"\"\"\n            INSERT INTO context_sessions (session_id, session_type)\n            VALUES (?, ?)\n        \"\"\", (session_id, session_type))\n        \n        self.active_context[session_id] = {\n            \"active_nodes\": [],\n            \"context_vector\": {},\n            \"turn_count\": 0\n        }\n        \n        return session_id\n    \n    def update_context(self, session_id: str, new_input: str) -> Dict:\n        \"\"\"\n        새 입력에 따라 맥락 업데이트 및 관련 기억 반환\n        \"\"\"\n        context = self.active_context.get(session_id, {})\n        \n        # 1. 새 입력에서 관련 노드 검색\n        relevant_nodes = self._find_relevant_nodes(new_input)\n        \n        # 2. 활성화 확산으로 연관 기억 찾기\n        activation_map = self.activation.activate(relevant_nodes, session_id)\n        \n        # 3. 기존 활성 노드 감쇠\n        for node in context.get(\"active_nodes\", []):\n            if node not in activation_map:\n                activation_map[node] = context[\"context_vector\"].get(node, 0) * 0.7\n        \n        # 4. 맥락 업데이트\n        context[\"active_nodes\"] = list(activation_map.keys())\n        context[\"context_vector\"] = activation_map\n        context[\"turn_count\"] += 1\n        \n        # 5. 상위 N개 활성화된 기억 반환\n        top_memories = self._get_top_memories(activation_map, limit=20)\n        \n        return {\n            \"direct_matches\": relevant_nodes,\n            \"associated_memories\": top_memories,\n            \"context_strength\": self._calculate_context_coherence(activation_map)\n        }\n    \n    def _find_relevant_nodes(self, text: str) -> List[int]:\n        \"\"\"텍스트와 관련된 초기 노드들 검색\"\"\"\n        # 키워드 추출\n        keywords = self._extract_keywords(text)\n        \n        # 키워드 기반 노드 검색\n        nodes = []\n        for keyword in keywords:\n            results = self.network.db.query(\"\"\"\n                SELECT DISTINCT node_id \n                FROM keyword_index\n                WHERE keyword = ?\n                LIMIT 5\n            \"\"\", (keyword,))\n            nodes.extend([r['node_id'] for r in results])\n        \n        return list(set(nodes))\n    \n    def _get_top_memories(self, activation_map: Dict[int, float], \n                         limit: int = 20) -> List[Dict]:\n        \"\"\"활성화 수준이 높은 상위 N개 기억 조회\"\"\"\n        sorted_nodes = sorted(\n            activation_map.items(), \n            key=lambda x: x[1], \n            reverse=True\n        )[:limit]\n        \n        memories = []\n        for node_id, activation_level in sorted_nodes:\n            memory = self.network.db.query_one(\"\"\"\n                SELECT content, subject, action, object, emotional_tone\n                FROM memory_nodes\n                WHERE node_id = ?\n            \"\"\", (node_id,))\n            \n            if memory:\n                memories.append({\n                    \"node_id\": node_id,\n                    \"activation\": activation_level,\n                    \"content\": memory['content'],\n                    \"structure\": {\n                        \"subject\": memory['subject'],\n                        \"action\": memory['action'],\n                        \"object\": memory['object']\n                    },\n                    \"emotion\": memory['emotional_tone']\n                })\n        \n        return memories",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ARCHITECTURE_DESIGN.md",
      "line_number": 441,
      "example_type": "python",
      "content": "class MemoryIndexer:\n    \"\"\"\n    메모리를 다양한 차원으로 인덱싱하여 빠른 접근 가능\n    \"\"\"\n    \n    def __init__(self, db_manager):\n        self.db = db_manager\n        \n    def index_memory(self, node_id: int, content: str, metadata: Dict):\n        \"\"\"새 메모리 노드 인덱싱\"\"\"\n        \n        # 1. 키워드 인덱싱\n        keywords = self._extract_keywords(content)\n        for keyword in keywords:\n            self.db.execute(\"\"\"\n                INSERT OR REPLACE INTO keyword_index (keyword, node_id, frequency)\n                VALUES (?, ?, COALESCE(\n                    (SELECT frequency + 1 FROM keyword_index \n                     WHERE keyword = ? AND node_id = ?), 1))\n            \"\"\", (keyword, node_id, keyword, node_id))\n        \n        # 2. 시간 윈도우 할당\n        timestamp = metadata.get('timestamp', datetime.now())\n        window_id = self._get_or_create_time_window(timestamp)\n        \n        # 3. 감정 인덱싱\n        emotional_tone = self._analyze_emotion(content)\n        \n        # 4. 구조적 요소 추출\n        structure = self._extract_structure(content)\n        \n        # 노드 메타데이터 업데이트\n        self.db.execute(\"\"\"\n            UPDATE memory_nodes\n            SET temporal_index = ?,\n                emotional_tone = ?,\n                subject = ?,\n                action = ?,\n                object = ?\n            WHERE node_id = ?\n        \"\"\", (window_id, emotional_tone, \n              structure.get('subject'),\n              structure.get('action'),\n              structure.get('object'),\n              node_id))\n    \n    def search_by_dimension(self, dimension: str, value: Any, limit: int = 10):\n        \"\"\"특정 차원으로 메모리 검색\"\"\"\n        \n        if dimension == \"temporal\":\n            # 시간 기반 검색\n            return self.db.query(\"\"\"\n                SELECT * FROM memory_nodes\n                WHERE temporal_index = ?\n                ORDER BY created_at DESC\n                LIMIT ?\n            \"\"\", (value, limit))\n            \n        elif dimension == \"emotional\":\n            # 감정 기반 검색\n            return self.db.query(\"\"\"\n                SELECT * FROM memory_nodes\n                WHERE ABS(emotional_tone - ?) < 0.2\n                ORDER BY ABS(emotional_tone - ?)\n                LIMIT ?\n            \"\"\", (value, value, limit))\n            \n        elif dimension == \"subject\":\n            # 주체 기반 검색\n            return self.db.query(\"\"\"\n                SELECT * FROM memory_nodes\n                WHERE subject = ?\n                ORDER BY importance DESC\n                LIMIT ?\n            \"\"\", (value, limit))",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ARCHITECTURE_DESIGN.md",
      "line_number": 523,
      "example_type": "python",
      "content": "class GreeumV3:\n    \"\"\"\n    v3.0.0 메인 인터페이스\n    \"\"\"\n    \n    def __init__(self):\n        self.db = DatabaseManager()\n        self.network = AssociationNetwork(self.db)\n        self.activation = SpreadingActivation(self.network)\n        self.context = ContextManager(self.network, self.activation)\n        self.indexer = MemoryIndexer(self.db)\n        \n    def add_memory(self, content: str, metadata: Dict = None) -> int:\n        \"\"\"새 메모리 추가\"\"\"\n        \n        # 1. 노드 생성\n        node_id = self.db.execute(\"\"\"\n            INSERT INTO memory_nodes (content, importance)\n            VALUES (?, ?)\n        \"\"\", (content, metadata.get('importance', 0.5)))\n        \n        # 2. 인덱싱\n        self.indexer.index_memory(node_id, content, metadata or {})\n        \n        # 3. 자동 연상 연결 생성\n        self._create_automatic_associations(node_id, content)\n        \n        return node_id\n    \n    def recall(self, query: str, session_id: str = None) -> Dict:\n        \"\"\"연상 기반 기억 회상\"\"\"\n        \n        # 세션 관리\n        if not session_id:\n            session_id = self.context.start_session()\n        \n        # 맥락 업데이트 및 연상 활성화\n        result = self.context.update_context(session_id, query)\n        \n        return {\n            \"session_id\": session_id,\n            \"memories\": result[\"associated_memories\"],\n            \"context_coherence\": result[\"context_strength\"],\n            \"association_map\": self._visualize_associations(result)\n        }\n    \n    def _create_automatic_associations(self, node_id: int, content: str):\n        \"\"\"새 메모리에 대한 자동 연상 연결 생성\"\"\"\n        \n        # 유사한 메모리 찾기\n        similar = self._find_similar_memories(content, limit=5)\n        \n        for similar_node, similarity in similar:\n            if similarity > 0.7:\n                self.network.create_association(\n                    node_id, similar_node,\n                    \"semantic\", similarity\n                )\n        \n        # 시간적으로 가까운 메모리 연결\n        recent = self.db.query(\"\"\"\n            SELECT node_id FROM memory_nodes\n            WHERE node_id != ?\n            ORDER BY created_at DESC\n            LIMIT 3\n        \"\"\", (node_id,))\n        \n        for r in recent:\n            self.network.create_association(\n                node_id, r['node_id'],\n                \"temporal\", 0.5\n            )",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line_number": 366,
      "example_type": "cli",
      "content": "main (v2.6.4.post1)\n├── develop-v3\n│   ├── alpha-1-actant-parser\n│   ├── alpha-2-hash-system\n│   └── alpha-3-causal-reasoning\n└── hotfix-v2.6.5",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line_number": 30,
      "example_type": "python",
      "content": "# 주요 작업\n1. v2.5.3 AIActantParser 코드 리뷰 및 테스트\n2. 기존 247개 메모리 샘플 분석\n3. 파싱 패턴 카테고리화\n4. 한국어/영어 파싱 규칙 정의\n\n# 성공 기준\n✓ 파서 모듈 100% 이해\n✓ 테스트 데이터셋 50개 준비\n✓ 파싱 규칙 문서화",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line_number": 44,
      "example_type": "python",
      "content": "class EnhancedActantParser:\n    \"\"\"v3.0.0 강화된 액탄트 파서\"\"\"\n    \n    def parse_memory(self, text: str) -> ActantStructure:\n        # 1. 언어 감지 (한/영/혼합)\n        language = self.detect_language(text)\n        \n        # 2. 패턴 기반 파싱\n        if self.has_explicit_pattern(text):\n            return self.pattern_based_parsing(text)\n        \n        # 3. NLP 기반 파싱 (형태소 분석)\n        tokens = self.tokenize(text, language)\n        subject = self.extract_subject(tokens)\n        action = self.extract_action(tokens)\n        object = self.extract_object(tokens)\n        \n        # 4. 신뢰도 계산\n        confidence = self.calculate_confidence(subject, action, object)\n        \n        return ActantStructure(subject, action, object, confidence)\n\n# 구현 목표\n✓ 명시적 패턴 90% 정확도\n✓ 암묵적 패턴 70% 정확도  \n✓ 다국어 지원 (한/영)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line_number": 101,
      "example_type": "python",
      "content": "test_cases = [\n    # 명시적 패턴\n    (\"[사용자-요청-기능개선]\", (\"사용자\", \"요청\", \"기능개선\"), 0.95),\n    (\"Claude가 버그를 수정했다\", (\"Claude\", \"수정\", \"버그\"), 0.90),\n    \n    # 암묵적 패턴  \n    (\"프로젝트가 성공했다\", (\"프로젝트\", \"성공\", None), 0.70),\n    (\"코딩을 많이 했다\", (None, \"코딩\", None), 0.60),\n    \n    # 복잡한 패턴\n    (\"팀이 프로젝트를 완성해서 보너스를 받았다\", \n     (\"팀\", \"완성\", \"프로젝트\"), 0.75)\n]",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line_number": 127,
      "example_type": "python",
      "content": "class ActantHashMapper:\n    \"\"\"액탄트 동일성 매핑 시스템\"\"\"\n    \n    def __init__(self):\n        # 수동 정의 핵심 매핑 (100개)\n        self.core_mappings = {\n            \"subjects\": {\n                \"user\": [\"사용자\", \"유저\", \"user\", \"나\", \"내가\", \"제가\"],\n                \"claude\": [\"Claude\", \"claude\", \"AI\", \"assistant\", \"어시스턴트\"],\n                \"team\": [\"팀\", \"team\", \"개발팀\", \"우리\", \"우리팀\"],\n                \"system\": [\"시스템\", \"system\", \"서버\", \"프로그램\", \"앱\"]\n            },\n            \"actions\": {\n                \"request\": [\"요청\", \"부탁\", \"ask\", \"request\", \"요구\"],\n                \"implement\": [\"구현\", \"개발\", \"만들기\", \"implement\", \"develop\"],\n                \"complete\": [\"완료\", \"완성\", \"끝\", \"finish\", \"done\"],\n                \"fix\": [\"수정\", \"고치기\", \"fix\", \"패치\", \"debug\"]\n            },\n            \"objects\": {\n                \"project\": [\"프로젝트\", \"project\", \"작업\", \"태스크\"],\n                \"feature\": [\"기능\", \"feature\", \"함수\", \"API\"],\n                \"bug\": [\"버그\", \"bug\", \"오류\", \"에러\", \"문제\"]\n            }\n        }\n\n# 구현 목표\n✓ 100개 핵심 액탄트 정의\n✓ 다국어 변형 포함\n✓ 유사어 그룹화",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line_number": 160,
      "example_type": "python",
      "content": "def normalize_actant(self, text: str, actant_type: str) -> str:\n    \"\"\"액탄트 텍스트를 정규화된 해시로 변환\"\"\"\n    \n    # 1. 정확 매칭 (신뢰도 0.9)\n    if exact_match := self.exact_match(text, actant_type):\n        return exact_match\n    \n    # 2. 패턴 매칭 (신뢰도 0.7)\n    if pattern_match := self.pattern_match(text, actant_type):\n        return pattern_match\n    \n    # 3. 유사도 매칭 (신뢰도 0.5)\n    if similarity_match := self.similarity_match(text, actant_type):\n        return similarity_match\n    \n    # 4. 새로운 해시 생성\n    return self.generate_new_hash(text, actant_type)\n\n# 테스트 케이스\nassert normalize_actant(\"사용자\", \"subject\") == \"subject_user\"\nassert normalize_actant(\"유저\", \"subject\") == \"subject_user\"\nassert normalize_actant(\"내가\", \"subject\") == \"subject_user\"",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line_number": 186,
      "example_type": "python",
      "content": "class AdaptiveHashLearner:\n    \"\"\"사용자 피드백 기반 해시 학습\"\"\"\n    \n    def learn_from_feedback(self, actant1, actant2, is_same: bool):\n        # 피드백 저장\n        self.feedback_store.add({\n            \"actant1\": actant1,\n            \"actant2\": actant2,\n            \"is_same\": is_same,\n            \"timestamp\": datetime.now()\n        })\n        \n        # 패턴 학습\n        if is_same and self.confidence_threshold_met():\n            self.merge_actants(actant1, actant2)\n        \n    def suggest_merges(self) -> List[MergeSuggestion]:\n        # 자주 함께 나타나는 액탄트 제안\n        return self.analyze_co_occurrence()",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line_number": 226,
      "example_type": "python",
      "content": "class StructuralCausalReasoner:\n    \"\"\"액탄트 구조 기반 인과관계 추론\"\"\"\n    \n    def analyze_causal_relationship(self, block1, block2):\n        # 1. 액탄트 동일성 체크\n        subject_match = self.compare_subjects(block1, block2)\n        object_match = self.compare_objects(block1, block2)\n        \n        # 2. 행동 인과성 분석\n        action_causality = self.analyze_action_sequence(\n            block1.actant_action, \n            block2.actant_action\n        )\n        \n        # 3. 시간적 검증\n        temporal_validity = self.validate_temporal_order(\n            block1.timestamp, \n            block2.timestamp\n        )\n        \n        # 4. 종합 신뢰도\n        confidence = self.calculate_structural_confidence(\n            subject_match, object_match, \n            action_causality, temporal_validity\n        )\n        \n        return CausalRelation(block1, block2, confidence)\n\n# 인과관계 규칙 예시\nCAUSAL_ACTION_RULES = {\n    (\"요청\", \"구현\"): 0.8,  # 요청 → 구현\n    (\"구현\", \"완료\"): 0.9,  # 구현 → 완료\n    (\"완료\", \"배포\"): 0.85, # 완료 → 배포\n    (\"오류\", \"수정\"): 0.9,  # 오류 → 수정\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line_number": 265,
      "example_type": "python",
      "content": "def infer_causal_chains(self, memories: List[Memory]) -> CausalGraph:\n    \"\"\"메모리 집합에서 인과관계 그래프 구축\"\"\"\n    \n    graph = CausalGraph()\n    \n    # 1. 모든 쌍 비교 (최적화 필요)\n    for i, mem1 in enumerate(memories):\n        for mem2 in memories[i+1:]:\n            if relation := self.analyze_causal_relationship(mem1, mem2):\n                if relation.confidence > 0.6:\n                    graph.add_edge(mem1, mem2, relation)\n    \n    # 2. 전이적 관계 추론\n    graph.infer_transitive_relations()\n    \n    # 3. 모순 제거\n    graph.resolve_contradictions()\n    \n    return graph",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line_number": 288,
      "example_type": "python",
      "content": "# 최적화 전략\n1. 인덱싱: 액탄트 해시 기반 빠른 검색\n2. 캐싱: 자주 접근하는 관계 캐시\n3. 배치 처리: 50개씩 묶어서 처리\n4. 병렬화: 멀티스레드 비교 연산\n\n# 검증 메트릭\n- 정확도: 수동 라벨링 100개와 비교\n- 재현율: 실제 관계 중 찾은 비율\n- 정밀도: 찾은 관계 중 정확한 비율\n- F1 스코어: 종합 성능 지표",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line_number": 315,
      "example_type": "python",
      "content": "# 시나리오: 프로젝트 개발 스토리\nmemories = [\n    \"사용자가 새 기능을 요청했다\",           # Block 1\n    \"Claude가 기능 설계를 시작했다\",         # Block 2  \n    \"개발팀이 프로토타입을 구현했다\",        # Block 3\n    \"테스트에서 버그가 발견되었다\",          # Block 4\n    \"개발자가 버그를 수정했다\",              # Block 5\n    \"최종 테스트를 통과했다\",                # Block 6\n    \"사용자가 기능에 만족했다\"               # Block 7\n]\n\n# 예상 결과\nexpected_actants = [\n    (\"사용자\", \"요청\", \"새 기능\"),\n    (\"Claude\", \"시작\", \"기능 설계\"),\n    (\"개발팀\", \"구현\", \"프로토타입\"),\n    (\"테스트\", \"발견\", \"버그\"),\n    (\"개발자\", \"수정\", \"버그\"),\n    (None, \"통과\", \"최종 테스트\"),\n    (\"사용자\", \"만족\", \"기능\")\n]\n\nexpected_causality = [\n    (1, 2, 0.85),  # 요청 → 설계 시작\n    (2, 3, 0.80),  # 설계 → 구현\n    (3, 4, 0.75),  # 구현 → 버그 발견\n    (4, 5, 0.90),  # 버그 발견 → 수정\n    (5, 6, 0.85),  # 수정 → 테스트 통과\n    (6, 7, 0.80)   # 통과 → 만족\n]",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line_number": 349,
      "example_type": "python",
      "content": "# 대규모 데이터 테스트\n- 1,000개 메모리: <1초\n- 10,000개 메모리: <10초\n- 100,000개 메모리: <2분\n\n# 메모리 사용량\n- 기본: <256MB\n- 1,000개: <512MB\n- 10,000개: <1GB",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line_number": 376,
      "example_type": "python",
      "content": "# 필수 패키지\ndependencies = {\n    \"core\": [\"sqlite3\", \"numpy\", \"click\"],\n    \"nlp\": [\"konlpy\", \"nltk\", \"spacy\"],\n    \"ml\": [\"scikit-learn\", \"sentence-transformers\"],\n    \"test\": [\"pytest\", \"pytest-cov\", \"pytest-benchmark\"]\n}\n\n# 개발 환경\n- Python 3.10+\n- SQLite 3.35+\n- 가상환경 권장",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line_number": 20,
      "example_type": "python",
      "content": "class TagStructure:\n    \"\"\"계층적 태그 구조\"\"\"\n    \n    # Level 1: Category (최대 5개)\n    CATEGORIES = {\n        'work': '업무 관련',\n        'personal': '개인 생활',\n        'learning': '학습/연구',\n        'social': '소셜/대화',\n        'system': '시스템/메타'\n    }\n    \n    # Level 2: Activity Type (최대 15개)\n    ACTIVITY_TYPES = {\n        'create': '생성/개발',\n        'fix': '수정/버그픽스',\n        'plan': '계획/설계',\n        'review': '리뷰/분석',\n        'document': '문서화',\n        'meeting': '회의/논의',\n        'research': '조사/연구',\n        'test': '테스트/검증',\n        'deploy': '배포/릴리즈',\n        'maintain': '유지보수'\n    }\n    \n    # Level 3: Domain Tags (최대 50개, 동적)\n    domain_tags = {\n        # Technical\n        'api', 'database', 'frontend', 'backend', 'auth',\n        'performance', 'security', 'ui', 'ux', 'algorithm',\n        \n        # Languages/Tools\n        'python', 'javascript', 'react', 'django', 'docker',\n        \n        # Concepts\n        'bug', 'feature', 'refactor', 'optimization', 'migration',\n        \n        # Project specific (자동 학습)\n        # ...dynamically added\n    }",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line_number": 66,
      "example_type": "python",
      "content": "@dataclass\nclass MemoryTags:\n    \"\"\"메모리별 태그 스키마\"\"\"\n    \n    # 필수 태그\n    category: str           # Level 1 (1개)\n    activity: str          # Level 2 (1개)\n    \n    # 선택 태그\n    domains: List[str]     # Level 3 (최대 5개)\n    \n    # 메타데이터\n    auto_generated: bool   # AI가 생성했는지\n    confidence: float      # AI 신뢰도 (0-1)\n    user_verified: bool    # 사용자가 확인했는지\n    \n    # 추가 속성\n    language: str          # 'ko', 'en', 'mixed'\n    importance: float      # 중요도 (자동 계산)\n    \n    def to_dict(self):\n        return {\n            'category': self.category,\n            'activity': self.activity,\n            'domains': self.domains,\n            'metadata': {\n                'auto': self.auto_generated,\n                'confidence': self.confidence,\n                'verified': self.user_verified,\n                'language': self.language\n            }\n        }",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line_number": 106,
      "example_type": "python",
      "content": "def quick_tag(content: str) -> Dict:\n    \"\"\"즉시 실행되는 기본 태깅\"\"\"\n    \n    # 1. Language detection\n    language = detect_language(content)\n    \n    # 2. Keyword extraction (existing)\n    keywords = extract_keywords(content)\n    \n    # 3. Rule-based category\n    category = infer_category_from_keywords(keywords)\n    \n    return {\n        'category': category,\n        'activity': 'unknown',  # AI가 나중에 채움\n        'domains': keywords[:3],\n        'language': language\n    }",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line_number": 128,
      "example_type": "python",
      "content": "async def enhance_tags_with_ai(memory_id: int, content: str):\n    \"\"\"백그라운드에서 AI로 태그 개선\"\"\"\n    \n    # MCP를 통해 Claude에게 요청\n    prompt = f\"\"\"\n    다음 메모리에 대한 태그를 생성해주세요:\n    \"{content}\"\n    \n    응답 형식:\n    - category: {CATEGORIES 중 1개}\n    - activity: {ACTIVITY_TYPES 중 1개}\n    - domains: [관련 기술/도메인 태그 3-5개]\n    - confidence: 0-1 사이 신뢰도\n    \"\"\"\n    \n    ai_tags = await mcp_client.analyze(prompt)\n    \n    # Update memory tags\n    update_memory_tags(memory_id, ai_tags)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line_number": 155,
      "example_type": "python",
      "content": "def search_with_tags(\n    query: str,\n    category: Optional[str] = None,\n    activity: Optional[str] = None,\n    domains: Optional[List[str]] = None,\n    exclude_tags: Optional[List[str]] = None\n) -> List[Memory]:\n    \"\"\"태그 기반 고급 검색\"\"\"\n    \n    results = []\n    \n    # 1. Tag-based filtering\n    if category:\n        results = filter_by_category(category)\n    \n    if activity:\n        results = filter_by_activity(results, activity)\n    \n    if domains:\n        results = filter_by_domains(results, domains)\n    \n    # 2. Exclude unwanted\n    if exclude_tags:\n        results = exclude_by_tags(results, exclude_tags)\n    \n    # 3. Text search on filtered set\n    if query:\n        results = text_search(results, query)\n    \n    # 4. Rank by relevance\n    return rank_results(results)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line_number": 190,
      "example_type": "python",
      "content": "def cross_language_search(query: str) -> List[Memory]:\n    \"\"\"언어 무관 검색\"\"\"\n    \n    # English query → search Korean memories\n    if is_english(query):\n        # Translate query to Korean\n        ko_query = translate_to_korean(query)\n        \n        # Search both\n        en_results = search_by_language(query, 'en')\n        ko_results = search_by_language(ko_query, 'ko')\n        \n        return merge_results(en_results, ko_results)\n    \n    # Korean query → search English tags\n    elif is_korean(query):\n        # Extract concepts\n        concepts = extract_concepts(query)\n        \n        # Map to English tags\n        en_tags = map_to_english_tags(concepts)\n        \n        return search_by_tags(en_tags)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line_number": 221,
      "example_type": "python",
      "content": "class TagConsolidator:\n    \"\"\"태그 자동 통합 관리\"\"\"\n    \n    # Synonym groups\n    SYNONYMS = {\n        'bug': ['bugs', '버그', 'error', 'issue'],\n        'auth': ['authentication', '인증', 'login', '로그인'],\n        'api': ['API', 'endpoint', '엔드포인트', 'rest'],\n        'db': ['database', '데이터베이스', 'DB', 'sql']\n    }\n    \n    def consolidate_tags(self):\n        \"\"\"주기적 태그 통합 (일 1회)\"\"\"\n        \n        # 1. Merge synonyms\n        for primary, synonyms in self.SYNONYMS.items():\n            for synonym in synonyms:\n                replace_tag(synonym, primary)\n        \n        # 2. Remove rare tags (사용 < 3회)\n        remove_rare_tags(min_usage=3)\n        \n        # 3. Suggest new synonyms (AI)\n        new_synonyms = detect_similar_tags()\n        if new_synonyms:\n            notify_user_for_approval(new_synonyms)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line_number": 251,
      "example_type": "python",
      "content": "class TagLifecycle:\n    \"\"\"태그 생명주기 관리\"\"\"\n    \n    def __init__(self):\n        self.tag_stats = {}  # tag -> {count, last_used, created}\n        self.max_tags = 50\n    \n    def on_tag_used(self, tag: str):\n        \"\"\"태그 사용 시 통계 업데이트\"\"\"\n        if tag not in self.tag_stats:\n            self.tag_stats[tag] = {\n                'count': 0,\n                'created': time.time(),\n                'last_used': None\n            }\n        \n        self.tag_stats[tag]['count'] += 1\n        self.tag_stats[tag]['last_used'] = time.time()\n        \n        # Check if cleanup needed\n        if len(self.tag_stats) > self.max_tags:\n            self.cleanup_tags()\n    \n    def cleanup_tags(self):\n        \"\"\"오래되고 적게 쓰인 태그 정리\"\"\"\n        \n        # Score = usage_count * recency_factor\n        scored_tags = []\n        for tag, stats in self.tag_stats.items():\n            recency = time.time() - stats['last_used']\n            recency_factor = 1 / (1 + recency / 86400)  # Daily decay\n            score = stats['count'] * recency_factor\n            scored_tags.append((tag, score))\n        \n        # Keep top 50\n        scored_tags.sort(key=lambda x: x[1], reverse=True)\n        tags_to_remove = [tag for tag, _ in scored_tags[self.max_tags:]]\n        \n        for tag in tags_to_remove:\n            self.archive_tag(tag)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line_number": 342,
      "example_type": "python",
      "content": "# 1. Update database schema\n# 2. Basic tag structure\n# 3. Manual tagging API\n\ndef add_memory_with_tags(content: str, tags: Optional[Dict] = None):\n    \"\"\"기본 태깅 지원 추가\"\"\"\n    memory_id = add_memory(content)\n    \n    if tags:\n        assign_tags(memory_id, tags)\n    else:\n        # Quick auto-tag\n        auto_tags = quick_tag(content)\n        assign_tags(memory_id, auto_tags)\n    \n    return memory_id",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line_number": 362,
      "example_type": "python",
      "content": "# 1. MCP integration for tagging\n# 2. Async tag enhancement\n# 3. Confidence scoring\n\nasync def enhance_all_untagged():\n    \"\"\"모든 미태그 메모리 처리\"\"\"\n    untagged = get_memories_without_tags()\n    \n    for memory in untagged:\n        await enhance_tags_with_ai(\n            memory.id, \n            memory.content\n        )",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line_number": 379,
      "example_type": "python",
      "content": "# 1. Tag-based search\n# 2. Cross-language support\n# 3. Advanced filtering\n\ndef search_v2(\n    text_query: Optional[str] = None,\n    tag_filter: Optional[TagFilter] = None\n):\n    \"\"\"향상된 검색\"\"\"\n    # Implementation",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line_number": 393,
      "example_type": "python",
      "content": "# 1. Auto-consolidation\n# 2. Tag lifecycle\n# 3. Analytics dashboard\n\ndef tag_maintenance_job():\n    \"\"\"일일 유지보수 작업\"\"\"\n    consolidator.run()\n    lifecycle.cleanup()\n    analytics.generate_report()",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line_number": 427,
      "example_type": "python",
      "content": "def inherit_context_tags(new_memory_id: int):\n    \"\"\"현재 컨텍스트의 태그 자동 상속\"\"\"\n    \n    active_context = get_active_context()\n    recent_tags = get_recent_tags(minutes=10)\n    \n    # 최근 사용 태그 중 관련성 높은 것 상속\n    inherited_tags = []\n    for tag in recent_tags:\n        if tag.usage_in_context > 0.3:\n            inherited_tags.append(tag)\n    \n    assign_tags(new_memory_id, inherited_tags)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line_number": 444,
      "example_type": "python",
      "content": "def learn_user_vocabulary():\n    \"\"\"사용자 특화 태그 학습\"\"\"\n    \n    # 사용자가 자주 쓰는 태그 패턴 학습\n    user_patterns = analyze_user_tagging_patterns()\n    \n    # 자동 태깅 시 사용자 패턴 반영\n    update_auto_tagger_weights(user_patterns)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ACTANT_SCHEMA_DESIGN.md",
      "line_number": 120,
      "example_type": "python",
      "content": "# 입력 예시\nmemory_text = \"사용자가 버그 수정을 요청했고 Claude가 해결했다\"\n\n# 파싱 결과\nactants = {\n    # 첫 번째 액탄트 구조\n    \"actant_1\": {\n        \"subject\": \"사용자\",\n        \"action\": \"요청\",\n        \"object\": \"버그 수정\",\n        \"sender\": None,  # 암묵적: 사용자 자신\n        \"receiver\": \"Claude\",  # 암묵적 추론\n    },\n    \n    # 두 번째 액탄트 구조  \n    \"actant_2\": {\n        \"subject\": \"Claude\",\n        \"action\": \"해결\",\n        \"object\": \"버그\",\n        \"sender\": \"사용자\",  # 요청자\n        \"receiver\": \"사용자\",  # 수혜자\n    }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ACTANT_SCHEMA_DESIGN.md",
      "line_number": 148,
      "example_type": "python",
      "content": "# 동일 엔티티 매핑\nentity_mappings = {\n    \"user_001\": [\"사용자\", \"유저\", \"user\", \"고객\", \"클라이언트\"],\n    \"claude_001\": [\"Claude\", \"claude\", \"AI\", \"assistant\", \"어시스턴트\"],\n    \"bug_001\": [\"버그\", \"bug\", \"오류\", \"에러\", \"error\", \"문제\"]\n}\n\n# 해시 생성\ndef get_entity_hash(entity_text, entity_type):\n    # 1. 기존 매핑 확인\n    for hash_id, variations in entity_mappings.items():\n        if entity_text.lower() in [v.lower() for v in variations]:\n            return hash_id\n    \n    # 2. 새 엔티티 생성\n    return create_new_entity_hash(entity_text, entity_type)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ACTANT_SCHEMA_DESIGN.md",
      "line_number": 169,
      "example_type": "python",
      "content": "# 행동 분류 체계\naction_taxonomy = {\n    \"request\": {\n        \"canonical\": \"요청\",\n        \"variations\": [\"요청\", \"부탁\", \"요구\", \"신청\", \"request\", \"ask\"],\n        \"type\": \"communication\"\n    },\n    \"solve\": {\n        \"canonical\": \"해결\",\n        \"variations\": [\"해결\", \"수정\", \"고침\", \"fix\", \"solve\", \"resolve\"],\n        \"type\": \"modification\"\n    },\n    \"create\": {\n        \"canonical\": \"생성\",\n        \"variations\": [\"생성\", \"만들기\", \"작성\", \"create\", \"make\", \"write\"],\n        \"type\": \"creation\"\n    }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ACTANT_SCHEMA_DESIGN.md",
      "line_number": 196,
      "example_type": "python",
      "content": "class ActantToNodeBridge:\n    \"\"\"액탄트 구조를 Association Network 노드로 변환\"\"\"\n    \n    def convert_actant_to_nodes(self, actant: Dict) -> List[MemoryNode]:\n        nodes = []\n        \n        # Subject 노드\n        if actant.get('subject_hash'):\n            subject_node = MemoryNode(\n                node_id=f\"entity_{actant['subject_hash']}\",\n                node_type='entity',\n                content=actant['subject_raw']\n            )\n            nodes.append(subject_node)\n        \n        # Action 노드\n        if actant.get('action_hash'):\n            action_node = MemoryNode(\n                node_id=f\"action_{actant['action_hash']}\",\n                node_type='action',\n                content=actant['action_raw']\n            )\n            nodes.append(action_node)\n        \n        # Object 노드\n        if actant.get('object_hash'):\n            object_node = MemoryNode(\n                node_id=f\"entity_{actant['object_hash']}\",\n                node_type='entity',\n                content=actant['object_raw']\n            )\n            nodes.append(object_node)\n        \n        return nodes\n    \n    def create_actant_associations(self, actant: Dict) -> List[Association]:\n        associations = []\n        \n        # Subject → Action\n        if actant.get('subject_hash') and actant.get('action_hash'):\n            associations.append(Association(\n                source_node_id=f\"entity_{actant['subject_hash']}\",\n                target_node_id=f\"action_{actant['action_hash']}\",\n                association_type='performs',\n                strength=0.9\n            ))\n        \n        # Action → Object\n        if actant.get('action_hash') and actant.get('object_hash'):\n            associations.append(Association(\n                source_node_id=f\"action_{actant['action_hash']}\",\n                target_node_id=f\"entity_{actant['object_hash']}\",\n                association_type='targets',\n                strength=0.9\n            ))\n        \n        return associations",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ACTANT_SCHEMA_DESIGN.md",
      "line_number": 258,
      "example_type": "python",
      "content": "class ActantCausalReasoner:\n    \"\"\"액탄트 기반 인과관계 추론\"\"\"\n    \n    def find_causal_chains(self, actants: List[Dict]) -> List[CausalChain]:\n        chains = []\n        \n        for i, actant1 in enumerate(actants):\n            for actant2 in actants[i+1:]:\n                # Object-Subject 매칭\n                if actant1['object_hash'] == actant2['subject_hash']:\n                    # A의 결과가 B의 주체가 됨\n                    chains.append(CausalChain(\n                        cause=actant1,\n                        effect=actant2,\n                        type='object_becomes_subject',\n                        confidence=0.8\n                    ))\n                \n                # Same Subject Sequential Actions\n                if actant1['subject_hash'] == actant2['subject_hash']:\n                    # 같은 주체의 연속 행동\n                    chains.append(CausalChain(\n                        cause=actant1,\n                        effect=actant2,\n                        type='sequential_action',\n                        confidence=0.6\n                    ))\n        \n        return chains",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_ACTANT_SCHEMA_DESIGN.md",
      "line_number": 296,
      "example_type": "json",
      "content": "{\n  \"memory_id\": 247,\n  \"context\": \"프로젝트 마일스톤 달성해서 팀이 축하했다\",\n  \"actants\": {\n    \"actant_id\": \"act_001\",\n    \"subject_raw\": \"팀\",\n    \"subject_hash\": \"team_001\",\n    \"action_raw\": \"축하했다\",\n    \"action_hash\": \"celebrate_001\",\n    \"object_raw\": \"프로젝트 마일스톤 달성\",\n    \"object_hash\": \"milestone_001\",\n    \"sender_raw\": null,\n    \"receiver_raw\": \"팀\",\n    \"receiver_hash\": \"team_001\",\n    \"confidence\": 0.85\n  },\n  \"entities\": {\n    \"team_001\": {\n      \"canonical\": \"개발팀\",\n      \"variations\": [\"팀\", \"team\", \"개발팀\", \"우리팀\"],\n      \"type\": \"group\"\n    },\n    \"milestone_001\": {\n      \"canonical\": \"마일스톤\",\n      \"variations\": [\"마일스톤\", \"milestone\", \"목표\"],\n      \"type\": \"achievement\"\n    }\n  }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 160,
      "example_type": "cli",
      "content": "# Anchor Management\ngreeum anchors status                    # Show all anchor states\ngreeum anchors set A 12345              # Set anchor A to block 12345\ngreeum anchors pin A 12345              # Pin anchor A (no auto-movement)\ngreeum anchors unpin A                  # Unpin anchor A\n\n# Enhanced Memory Operations\ngreeum memory search \"query\" --slot A --radius 2\ngreeum memory add \"content\" --slot B",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 337,
      "example_type": "cli",
      "content": "# 1. Run bootstrap to build graph index\npython scripts/bootstrap_graphindex.py\n\n# 2. Initialize anchor system (automatic on first use)\ngreeum anchors status\n\n# 3. Verify system health\npython tests/test_anchors_graph.py",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 377,
      "example_type": "cli",
      "content": "# Solution: Run bootstrap\npython scripts/bootstrap_graphindex.py",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 389,
      "example_type": "cli",
      "content": "# Solution: Periodic graph optimization  \npython scripts/optimize_graph_index.py",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 65,
      "example_type": "python",
      "content": "def select_active_slot(input_vec: np.ndarray) -> str:\n    similarities = {\n        slot: cosine_similarity(input_vec, slot_state['topic_vec'])\n        for slot, slot_state in self.state.items()\n    }\n    \n    # Apply hysteresis to prevent excessive switching\n    best_slot = max(similarities, key=similarities.get)\n    \n    # Return slot with highest similarity above threshold\n    return best_slot if similarities[best_slot] > threshold else 'A'",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 83,
      "example_type": "python",
      "content": "def beam_search(start: str, is_goal: Callable, beam: int = 32, max_hop: int = 2):\n    frontier = [(start, 0.0)]\n    visited = set()\n    hits = []\n    \n    for depth in range(max_hop + 1):\n        next_frontier = []\n        for node, score in frontier:\n            if node not in visited:\n                visited.add(node)\n                if is_goal(node):\n                    hits.append(node)\n                    \n                # Expand neighbors with beam width limit\n                neighbors = self.neighbors(node, k=beam)\n                next_frontier.extend(neighbors)\n        \n        # Keep top candidates for next hop\n        frontier = sorted(next_frontier, key=lambda x: x[1], reverse=True)[:beam]\n    \n    return hits",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 111,
      "example_type": "python",
      "content": "def write(text: str, slot: str = None, policy: dict = None) -> str:\n    embedding = embed(text)\n    active_slot = slot or select_active_slot(embedding)\n    anchor_id = get_slot_anchor(active_slot)\n    \n    # Find best insertion point near anchor\n    anchor_neighbors = graph_index.neighbors(anchor_id, k=32)\n    best_neighbor = max(anchor_neighbors, key=lambda n: similarity(embedding, n))\n    \n    # Insert new block and create edges\n    new_block = ltm.insert(text, embedding)\n    graph_index.upsert_edges(new_block.id, [best_neighbor] + anchor_neighbors[:7])\n    \n    # Update anchor position\n    if not slot_info['pinned']:\n        anchor_manager.move_anchor(active_slot, new_block.id, embedding)\n    \n    return new_block.id",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 201,
      "example_type": "python",
      "content": "from greeum.core.search_engine import SearchEngine\nfrom greeum.anchors import AnchorManager\n\n# Localized search\nsearch_engine = SearchEngine()\nresults = search_engine.search(\n    query=\"machine learning concepts\",\n    slot=\"A\",         # Use anchor slot A\n    radius=2,         # 2-hop exploration\n    fallback=True     # Fall back to global search if needed\n)\n\n# Anchor management\nanchor_manager = AnchorManager(\"data/anchors.json\")\nanchor_manager.move_anchor(\"B\", \"54321\", topic_vector)\nanchor_manager.pin_anchor(\"B\")",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 289,
      "example_type": "python",
      "content": "# Research session on AI ethics\nsearch_engine.search(\"bias in algorithms\", slot=\"A\")      # Current focus\nsearch_engine.search(\"historical context\", slot=\"B\")      # Background research  \nsearch_engine.search(\"implementation details\", slot=\"C\")   # Technical deep-dive",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 300,
      "example_type": "python",
      "content": "# Topic shift detected - anchor A moves to new domain\nanchor_manager.move_anchor(\"A\", new_relevant_block_id, new_topic_vector)\n\n# Previous context preserved in other slots\nslot_b_context = anchor_manager.get_slot_info(\"B\")  # Still available",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 312,
      "example_type": "python",
      "content": "# Pin important reference document\nanchor_manager.pin_anchor(\"C\", reference_doc_id)\n\n# Anchor C stays fixed while A and B adapt to conversation",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 325,
      "example_type": "python",
      "content": "# Existing code (still works)\nresults = search_engine.search(\"query\", top_k=5)\n\n# Enhanced with anchors (optional)\nresults = search_engine.search(\"query\", top_k=5, slot=\"A\", radius=2)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 352,
      "example_type": "python",
      "content": "# This bypasses anchor system entirely\nresults = search_engine.search(\"query\")  # Uses traditional path",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 383,
      "example_type": "python",
      "content": "# Solution: Check similarity threshold\nsearch_engine.search(query, slot=\"A\", radius=3)  # Increase radius",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 396,
      "example_type": "python",
      "content": "# Adjust graph parameters for your use case\nGraphIndex(theta=0.25, kmax=16)  # Lighter graph for speed\nGraphIndex(theta=0.45, kmax=64)  # Denser graph for quality",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 47,
      "example_type": "json",
      "content": "{\n  \"slot\": \"A|B|C\",\n  \"anchor_block_id\": \"12345\",\n  \"topic_vec\": [0.1, 0.2, ...],  // 128-dim embedding\n  \"hop_budget\": 1|2|3,\n  \"pinned\": false,\n  \"summary\": \"Context description\",\n  \"last_used_ts\": 1692123456\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 224,
      "example_type": "json",
      "content": "{\n  \"version\": 1,\n  \"slots\": [\n    {\n      \"slot\": \"A\",\n      \"anchor_block_id\": \"12345\",\n      \"topic_vec\": [0.1, 0.2, ...],\n      \"summary\": \"Context description\", \n      \"last_used_ts\": 1692123456,\n      \"hop_budget\": 2,\n      \"pinned\": false\n    }\n  ],\n  \"updated_at\": 1692123456\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/design/anchorized-memory.md",
      "line_number": 244,
      "example_type": "json",
      "content": "{\n  \"version\": 1,\n  \"nodes\": [\"block1\", \"block2\", \"block3\"],\n  \"edges\": [\n    {\n      \"u\": \"block1\",\n      \"v\": \"block2\", \n      \"w\": 0.75,\n      \"src\": [\"sim\", \"time\"]\n    }\n  ],\n  \"built_at\": 1692123456,\n  \"params\": {\n    \"theta\": 0.35,\n    \"kmax\": 32,\n    \"alpha\": 0.7,\n    \"beta\": 0.2,\n    \"gamma\": 0.1\n  }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_FINAL_SUMMARY.md",
      "line_number": 24,
      "example_type": "python",
      "content": "class ActiveContextManager(STMManager):\n    \"\"\"STM을 확장하여 Active Context로 진화\"\"\"\n    \n    def add_memory_with_context(self, content: str, importance: float = 0.5):\n        # 현재 활성 노드들과 자동 연결 (핵심!)\n        self._create_context_connections(block_index)\n        \n        # 활성화 레벨 관리\n        self.active_nodes[block_index] = 1.0\n        self._decay_activations()",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_FINAL_SUMMARY.md",
      "line_number": 43,
      "example_type": "python",
      "content": "@dataclass\nclass MemoryNode:\n    node_id: str\n    content: str\n    timestamp: float\n    activation: float = 0.0\n\nclass NeuralMemoryNetwork:\n    \"\"\"진짜 신경망처럼 작동하는 메모리\"\"\"\n    \n    def _spread_activation(self, source_id: str):\n        # Breadth-first 활성화 전파\n        # 연결 강도와 거리에 따른 감쇠",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_FINAL_SUMMARY.md",
      "line_number": 65,
      "example_type": "python",
      "content": "class V3MigrationBridge:\n    \"\"\"v2.6.4와 v3.0 동시 운영 및 점진적 전환\"\"\"\n    \n    def __init__(self):\n        self.legacy_blocks = BlockManager()  # v2.6.4\n        self.context_memory = ContextMemorySystem()  # v3.0\n        self.mode = 'hybrid'  # legacy/v3/hybrid",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_FINAL_SUMMARY.md",
      "line_number": 126,
      "example_type": "python",
      "content": "from greeum.core.context_memory import ContextMemorySystem\n\n# 초기화\nmemory = ContextMemorySystem()\n\n# 메모리 추가 (자동으로 현재 컨텍스트에 연결)\nmemory.add_memory(\"버그 수정 완료\")\n\n# 컨텍스트 전환\nmemory.switch_context(\"lunch_break\")\n\n# 연상 기반 회상\nresults = memory.recall(\"버그\", use_activation=True)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V3.0.0_FINAL_SUMMARY.md",
      "line_number": 143,
      "example_type": "python",
      "content": "from greeum.core.v3_migration_bridge import V3MigrationBridge\n\n# 하이브리드 모드로 시작\nbridge = V3MigrationBridge()\nbridge.set_mode('hybrid')\n\n# 점진적 마이그레이션\nbridge.batch_migrate(start_index=0, batch_size=10)",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V2.7.0_ROADMAP.md",
      "line_number": 55,
      "example_type": "cli",
      "content": "# 목표: 모든 멀티스레드 환경에서 안전한 동작\nexport GREEUM_THREAD_SAFE=true  # 기본값으로 설정",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V2.7.0_ROADMAP.md",
      "line_number": 184,
      "example_type": "cli",
      "content": "# 개선된 CLI 예시\ngreeum memory add \"새 기억\" --importance 0.9 --tags project,urgent\ngreeum search \"프로젝트\" --interactive --suggestions\ngreeum stats --dashboard --port 8080",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V2.7.0_ROADMAP.md",
      "line_number": 306,
      "example_type": "cli",
      "content": "# 즉시 실행 가능한 작업\nexport GREEUM_THREAD_SAFE=true\npython -m pytest tests/test_thread_safety.py -v",
      "expected_output": null
    },
    {
      "file_path": "docs/design/GREEUM_V2.7.0_ROADMAP.md",
      "line_number": 82,
      "example_type": "python",
      "content": "# 예시: 스마트 백업 스케줄러\nclass SmartBackupScheduler:\n    def __init__(self):\n        self.strategies = {\n            'incremental': IncrementalBackup(),\n            'differential': DifferentialBackup(),\n            'full': FullBackup()\n        }\n    \n    def schedule_backup(self, importance_threshold=0.8):\n        # 중요도 기반 백업 전략 자동 선택\n        pass",
      "expected_output": null
    },
    {
      "file_path": "docs/releases/RELEASE_NOTES_v2.6.4.md",
      "line_number": 68,
      "example_type": "cli",
      "content": "pip install greeum>=2.6.4",
      "expected_output": null
    },
    {
      "file_path": "docs/releases/RELEASE_NOTES_v2.6.4.md",
      "line_number": 73,
      "example_type": "cli",
      "content": "pip install --upgrade greeum",
      "expected_output": null
    },
    {
      "file_path": "docs/releases/RELEASE_NOTES_v2.6.4.md",
      "line_number": 119,
      "example_type": "python",
      "content": "from greeum.core.precompact_hook import PreCompactHookHandler\nfrom greeum.core.raw_data_backup_layer import RawDataBackupLayer\nfrom greeum.core.database_manager import DatabaseManager\n\n# Automatic setup - no configuration needed\ndb_manager = DatabaseManager()\nbackup_layer = RawDataBackupLayer(db_manager)\nhook = PreCompactHookHandler(backup_layer)\n\n# Context preservation happens automatically\nhook.register_hook()  # Monitors Claude Code environment",
      "expected_output": null
    },
    {
      "file_path": "docs/releases/RELEASE_NOTES_v2.6.4.md",
      "line_number": 134,
      "example_type": "python",
      "content": "from greeum.core.context_recovery import ContextRecoveryManager\n\nrecovery = ContextRecoveryManager(backup_layer)\nresult = recovery.recover_session_context(\"your_session_id\")\n\nprint(f\"Recovery quality: {result['quality_score']:.2f}\")\nprint(f\"Recovered contexts: {len(result['recovered_context'])}\")",
      "expected_output": null
    },
    {
      "file_path": "docs/releases/RELEASE_NOTES_v3.0.0-alpha.1.md",
      "line_number": 103,
      "example_type": "cli",
      "content": "export GREEUM_DB_PATH=\"data/greeum.db\"\nexport GREEUM_LOG_LEVEL=\"INFO\"  \nexport GREEUM_DEBUG=\"false\"\nexport GREEUM_ENV=\"development\"",
      "expected_output": null
    },
    {
      "file_path": "docs/releases/RELEASE_NOTES_v3.0.0-alpha.1.md",
      "line_number": 199,
      "example_type": "cli",
      "content": "pip install greeum>=3.0.0a1\npython -c \"from greeum.core.context_memory import ContextMemorySystem; memory = ContextMemorySystem(); memory.add_memory('Hello v3.0!')\"",
      "expected_output": null
    },
    {
      "file_path": "docs/releases/RELEASE_NOTES_v3.0.0-alpha.1.md",
      "line_number": 64,
      "example_type": "python",
      "content": "# Main interface\nContextMemorySystem(db_path=None)\n\n# Usage\nmemory = ContextMemorySystem()\nmemory.add_memory(\"API 버그 수정 완료\")  # Auto-tagged + connected\nresults = memory.recall(\"버그\", category=\"work\")",
      "expected_output": null
    },
    {
      "file_path": "docs/releases/RELEASE_NOTES_v3.0.0-alpha.1.md",
      "line_number": 79,
      "example_type": "python",
      "content": "# Context switching\nmemory.switch_context(\"lunch_break\")\n\n# Tag-based recall\nmemory.recall(\"query\", category=\"work\", activity=\"fix\")\n\n# Connection analysis  \nconnections = memory.get_memory_connections(memory_id)\n\n# Tag search\ntagger.search_by_tags(category=\"work\", domains=[\"api\"])",
      "expected_output": null
    },
    {
      "file_path": "docs/releases/RELEASE_NOTES_v3.0.0-alpha.1.md",
      "line_number": 150,
      "example_type": "python",
      "content": "# Old way\nfrom greeum import BlockManager\nblocks = BlockManager()\nblocks.add_block(content, keywords, tags, embedding, importance)\n\n# New way  \nfrom greeum.core.context_memory import ContextMemorySystem\nmemory = ContextMemorySystem()\nmemory.add_memory(content, importance)  # Auto-tagging + context",
      "expected_output": null
    },
    {
      "file_path": "docs/releases/RELEASE_NOTES_v3.0.0-alpha.1.md",
      "line_number": 205,
      "example_type": "python",
      "content": "memory = ContextMemorySystem()\n\n# Work context\nmemory.switch_context(\"morning_work\")\nmemory.add_memory(\"API 설계 시작\")\nmemory.add_memory(\"REST 엔드포인트 정의\")\n\n# Search  \nresults = memory.recall(\"API\", category=\"work\")\nprint(f\"Found {len(results)} work-related API memories\")",
      "expected_output": null
    },
    {
      "file_path": "docs/releases/RELEASE_NOTES_v3.0.0-alpha.1.md",
      "line_number": 111,
      "example_type": "json",
      "content": "{\n  \"memory\": {\n    \"enable_auto_tagging\": true,\n    \"context_timeout\": 300,\n    \"max_domain_tags\": 50\n  },\n  \"api\": {\n    \"enable_mcp\": false\n  },\n  \"system\": {\n    \"environment\": \"development\",\n    \"debug_mode\": true\n  }\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/releases/RELEASE_NOTES_v2.4.0rc1.md",
      "line_number": 46,
      "example_type": "cli",
      "content": "pip install greeum==2.4.0rc1\n\n# For full ML/NLP features:\npip install greeum[full]==2.4.0rc1",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_KR.md",
      "line_number": 42,
      "example_type": "cli",
      "content": "   git clone https://github.com/DryRainEnt/Greeum.git\n   cd Greeum\n   ```\n\n2. 의존성 설치 (v2.2.5 - 앵커 시스템 포함)\n   ```bash\n   pip install \"greeum>=2.2.5\"\n   \n   # 또는 모든 기능 포함 설치\n   pip install \"greeum[all]>=2.2.5\"\n   ```\n\n## 🧪 사용 방법\n\n### CLI 인터페이스\n",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_KR.md",
      "line_number": 81,
      "example_type": "cli",
      "content": "# API 서버 실행\npython api/memory_api.py",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_KR.md",
      "line_number": 100,
      "example_type": "python",
      "content": "from greeum import BlockManager, STMManager, CacheManager, PromptWrapper\nfrom greeum.text_utils import process_user_input\nfrom greeum.temporal_reasoner import TemporalReasoner\n\n# 사용자 입력 처리\nuser_input = \"새로운 프로젝트를 시작했고 정말 흥미로워요\"\nprocessed = process_user_input(user_input)\n\n# 블록 매니저로 기억 저장\nblock_manager = BlockManager()\nblock = block_manager.add_block(\n    context=processed[\"context\"],\n    keywords=processed[\"keywords\"],\n    tags=processed[\"tags\"],\n    embedding=processed[\"embedding\"],\n    importance=processed[\"importance\"]\n)\n\n# 시간 기반 검색 (다국어)\ntemporal_reasoner = TemporalReasoner(db_manager=block_manager, default_language=\"auto\")\ntime_query = \"3일 전에 무엇을 했지?\"\ntime_results = temporal_reasoner.search_by_time_reference(time_query)\n\n# 프롬프트 생성\ncache_manager = CacheManager(block_manager=block_manager)\nprompt_wrapper = PromptWrapper(cache_manager=cache_manager)\n\nuser_question = \"프로젝트는 어떻게 진행되고 있나요?\"\nprompt = prompt_wrapper.compose_prompt(user_question)\n\n# LLM에 전달\n# llm_response = call_your_llm(prompt)",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_KR.md",
      "line_number": 203,
      "example_type": "python",
      "content": "# 한국어\nresult = evaluate_temporal_query(\"3일 전에 뭐 했어?\", language=\"ko\")\n# 반환값: {detected: True, language: \"ko\", best_ref: {term: \"3일 전\"}}\n\n# 영어\nresult = evaluate_temporal_query(\"What did I do 3 days ago?\", language=\"en\")\n# 반환값: {detected: True, language: \"en\", best_ref: {term: \"3 days ago\"}}\n\n# 자동 감지\nresult = evaluate_temporal_query(\"What happened yesterday?\")\n# 반환값: {detected: True, language: \"en\", best_ref: {term: \"yesterday\"}}",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_KR.md",
      "line_number": 180,
      "example_type": "json",
      "content": "{\n  \"block_index\": 143,\n  \"timestamp\": \"2025-05-08T01:02:33\",\n  \"context\": \"새로운 프로젝트를 시작했고 정말 흥미로워요\",\n  \"keywords\": [\"프로젝트\", \"시작\", \"흥미로운\"],\n  \"tags\": [\"긍정적\", \"시작\", \"동기부여\"],\n  \"embedding\": [0.131, 0.847, ...],\n  \"importance\": 0.91,\n  \"hash\": \"...\",\n  \"prev_hash\": \"...\"\n}",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_JP.md",
      "line_number": 29,
      "example_type": "cli",
      "content": "# pipxでインストール（推奨）\npipx install greeum>=2.2.5\n\n# またはpipでインストール\npip install greeum>=2.2.5",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_JP.md",
      "line_number": 39,
      "example_type": "cli",
      "content": "# メモリ追加\ngreeum memory add \"今日新しいプロジェクトを開始しました。Pythonでウェブアプリケーションを開発する予定です。\"\n\n# メモリアンカーの設定（v2.2.5+の新機能）\ngreeum anchors set A 123  # 重要なメモリをスロットAにピン留め\n\n# アンカーベース検索\ngreeum memory search \"プロジェクト Python\" --slot A --radius 3\n\n# アンカー状態確認\ngreeum anchors status\n\n# 長期記憶分析\ngreeum ltm analyze --period 30d --trends\n\n# 短期記憶追加\ngreeum stm add \"一時メモ\" --ttl 1h\n\n# MCPサーバー実行\ngreeum mcp serve",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_JP.md",
      "line_number": 116,
      "example_type": "cli",
      "content": "# アンカー状態確認\ngreeum anchors status\n\n# 重要なメモリをアンカーに設定\ngreeum anchors set A 123    # メモリ#123をスロットAに設定\ngreeum anchors set B 456    # メモリ#456をスロットBに設定\n\n# アンカー周辺検索\ngreeum memory search \"会議内容\" --slot A --radius 3\n\n# アンカーのピン留め/解除\ngreeum anchors pin A        # Aの自動移動を防止\ngreeum anchors unpin A      # Aの自動移動を許可\n\n# アンカーのクリア\ngreeum anchors clear A      # スロットAをクリア",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_JP.md",
      "line_number": 175,
      "example_type": "cli",
      "content": "   greeum --version  # v2.2.5以上\n   ```\n\n2. **Claude Desktop設定**\n   ```json\n   {\n     \"mcpServers\": {\n       \"greeum\": {\n         \"command\": \"python3\",\n         \"args\": [\"-m\", \"greeum.mcp.claude_code_mcp_server\"],\n         \"env\": {\n           \"GREEUM_DATA_DIR\": \"/path/to/data\"\n         }\n       }\n     }\n   }\n   ```\n\n3. **接続確認**\n   ```bash\n   claude mcp list  # greeumサーバー確認\n   ```\n\n### その他のLLM統合",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_JP.md",
      "line_number": 234,
      "example_type": "cli",
      "content": "# ソースコードダウンロード後\npip install -e .[dev]\ntox  # テスト実行",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_JP.md",
      "line_number": 96,
      "example_type": "python",
      "content": "from greeum import BlockManager, STMManager, PromptWrapper\n\n# メモリシステム初期化\nbm = BlockManager()\nstm = STMManager()\npw = PromptWrapper()\n\n# メモリ追加\nbm.add_block(\n    context=\"重要な会議内容\",\n    keywords=[\"会議\", \"決定事項\"],\n    importance=0.9\n)\n\n# コンテキストベースプロンプト生成\nenhanced_prompt = pw.compose_prompt(\"前回の会議で何を決めましたか？\")",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_JP.md",
      "line_number": 200,
      "example_type": "python",
      "content": "# OpenAI GPT\nfrom greeum.client import MemoryClient\nclient = MemoryClient(llm_type=\"openai\")\n\n# ローカルLLM\nclient = MemoryClient(llm_type=\"local\", endpoint=\"http://localhost:8080\")",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_JP.md",
      "line_number": 180,
      "example_type": "json",
      "content": "   {\n     \"mcpServers\": {\n       \"greeum\": {\n         \"command\": \"python3\",\n         \"args\": [\"-m\", \"greeum.mcp.claude_code_mcp_server\"],\n         \"env\": {\n           \"GREEUM_DATA_DIR\": \"/path/to/data\"\n         }\n       }\n     }\n   }\n   ```\n\n3. **接続確認**\n   ```bash\n   claude mcp list  # greeumサーバー確認\n   ```\n\n### その他のLLM統合",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_EN.md",
      "line_number": 29,
      "example_type": "cli",
      "content": "# Install with pipx (recommended) - Latest version with anchor system\npipx install \"greeum>=2.2.5\"\n\n# Or install with pip\npip install \"greeum>=2.2.5\"",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_EN.md",
      "line_number": 39,
      "example_type": "cli",
      "content": "# Add memory (v2.2.5 syntax)\ngreeum memory add \"Started a new project today. Planning to develop a web application with Python.\"\n\n# Search memories\ngreeum memory search \"project Python\" --count 5\n\n# Memory Anchors (NEW in v2.2.5)\ngreeum anchors status                     # Check anchor status\ngreeum anchors set A 123                 # Pin memory #123 to slot A\ngreeum memory search \"Python\" --slot A   # Search near anchor A\n\n# Add short-term memory\ngreeum stm add \"Temporary note\" --ttl 1h\n\n# Run MCP server\npython3 -m greeum.mcp.claude_code_mcp_server",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_EN.md",
      "line_number": 144,
      "example_type": "cli",
      "content": "   greeum --version  # v2.0.5 or higher\n   ```\n\n2. **Claude Desktop Configuration**\n   ```json\n   {\n     \"mcpServers\": {\n       \"greeum\": {\n         \"command\": \"python3\",\n         \"args\": [\"-m\", \"greeum.mcp.claude_code_mcp_server\"],\n         \"env\": {\n           \"GREEUM_DATA_DIR\": \"/path/to/data\"\n         }\n       }\n     }\n   }\n   ```\n\n3. **Verify Connection**\n   ```bash\n   claude mcp list  # Check greeum server\n   ```\n\n### Other LLM Integration",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_EN.md",
      "line_number": 203,
      "example_type": "cli",
      "content": "# After downloading source code\npip install -e .[dev]\ntox  # Run tests",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_EN.md",
      "line_number": 85,
      "example_type": "python",
      "content": "from greeum import BlockManager, STMManager, PromptWrapper\n\n# Initialize memory system\nbm = BlockManager()\nstm = STMManager()\npw = PromptWrapper()\n\n# Add memory\nbm.add_block(\n    context=\"Important meeting content\",\n    keywords=[\"meeting\", \"decisions\"],\n    importance=0.9\n)\n\n# Generate context-based prompt\nenhanced_prompt = pw.compose_prompt(\"What did we decide in the last meeting?\")",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_EN.md",
      "line_number": 169,
      "example_type": "python",
      "content": "# OpenAI GPT\nfrom greeum.client import MemoryClient\nclient = MemoryClient(llm_type=\"openai\")\n\n# Local LLM\nclient = MemoryClient(llm_type=\"local\", endpoint=\"http://localhost:8080\")",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_EN.md",
      "line_number": 149,
      "example_type": "json",
      "content": "   {\n     \"mcpServers\": {\n       \"greeum\": {\n         \"command\": \"python3\",\n         \"args\": [\"-m\", \"greeum.mcp.claude_code_mcp_server\"],\n         \"env\": {\n           \"GREEUM_DATA_DIR\": \"/path/to/data\"\n         }\n       }\n     }\n   }\n   ```\n\n3. **Verify Connection**\n   ```bash\n   claude mcp list  # Check greeum server\n   ```\n\n### Other LLM Integration",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_ZH.md",
      "line_number": 29,
      "example_type": "cli",
      "content": "# 使用pipx安装（推荐）\npipx install greeum>=2.2.5\n\n# 或使用pip安装\npip install greeum>=2.2.5",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_ZH.md",
      "line_number": 39,
      "example_type": "cli",
      "content": "# 添加记忆\ngreeum memory add \"今天开始了一个新项目。计划用Python开发Web应用程序。\"\n\n# 设置记忆锚点（v2.2.5+新功能）\ngreeum anchors set A 123  # 将重要记忆固定到插槽A\n\n# 基于锚点的搜索\ngreeum memory search \"项目 Python\" --slot A --radius 3\n\n# 查看锚点状态\ngreeum anchors status\n\n# 长期记忆分析\ngreeum ltm analyze --period 30d --trends\n\n# 添加短期记忆\ngreeum stm add \"临时备忘\" --ttl 1h\n\n# 运行MCP服务器\ngreeum mcp serve",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_ZH.md",
      "line_number": 116,
      "example_type": "cli",
      "content": "# 查看锚点状态\ngreeum anchors status\n\n# 将重要记忆设置为锚点\ngreeum anchors set A 123    # 将记忆#123设置到插槽A\ngreeum anchors set B 456    # 将记忆#456设置到插槽B\n\n# 锚点周围搜索\ngreeum memory search \"会议内容\" --slot A --radius 3\n\n# 锁定/解锁锚点\ngreeum anchors pin A        # 防止A自动移动\ngreeum anchors unpin A      # 允许A自动移动\n\n# 清除锚点\ngreeum anchors clear A      # 清除插槽A",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_ZH.md",
      "line_number": 175,
      "example_type": "cli",
      "content": "   greeum --version  # v2.2.5或更高版本\n   ```\n\n2. **Claude Desktop配置**\n   ```json\n   {\n     \"mcpServers\": {\n       \"greeum\": {\n         \"command\": \"python3\",\n         \"args\": [\"-m\", \"greeum.mcp.claude_code_mcp_server\"],\n         \"env\": {\n           \"GREEUM_DATA_DIR\": \"/path/to/data\"\n         }\n       }\n     }\n   }\n   ```\n\n3. **验证连接**\n   ```bash\n   claude mcp list  # 检查greeum服务器\n   ```\n\n### 其他LLM集成",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_ZH.md",
      "line_number": 234,
      "example_type": "cli",
      "content": "# 下载源代码后\npip install -e .[dev]\ntox  # 运行测试",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_ZH.md",
      "line_number": 96,
      "example_type": "python",
      "content": "from greeum import BlockManager, STMManager, PromptWrapper\n\n# 初始化记忆系统\nbm = BlockManager()\nstm = STMManager()\npw = PromptWrapper()\n\n# 添加记忆\nbm.add_block(\n    context=\"重要的会议内容\",\n    keywords=[\"会议\", \"决定\"],\n    importance=0.9\n)\n\n# 生成基于上下文的提示\nenhanced_prompt = pw.compose_prompt(\"上次会议我们决定了什么？\")",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_ZH.md",
      "line_number": 200,
      "example_type": "python",
      "content": "# OpenAI GPT\nfrom greeum.client import MemoryClient\nclient = MemoryClient(llm_type=\"openai\")\n\n# 本地LLM\nclient = MemoryClient(llm_type=\"local\", endpoint=\"http://localhost:8080\")",
      "expected_output": null
    },
    {
      "file_path": "docs/i18n/README_ZH.md",
      "line_number": 180,
      "example_type": "json",
      "content": "   {\n     \"mcpServers\": {\n       \"greeum\": {\n         \"command\": \"python3\",\n         \"args\": [\"-m\", \"greeum.mcp.claude_code_mcp_server\"],\n         \"env\": {\n           \"GREEUM_DATA_DIR\": \"/path/to/data\"\n         }\n       }\n     }\n   }\n   ```\n\n3. **验证连接**\n   ```bash\n   claude mcp list  # 检查greeum服务器\n   ```\n\n### 其他LLM集成",
      "expected_output": null
    }
  ],
  "results": [
    {
      "file": "docs/anchors-guide.md",
      "line": 46,
      "type": "cli",
      "status": "fail",
      "message": "Command not found or failed: Usage: python -m greeum.cli [OPTIONS] COMMAND [ARGS]...\nTry 'python -m greeum.cli --help' for help.\n\nError: No such command 'anchors'.\n"
    },
    {
      "file": "docs/anchors-guide.md",
      "line": 76,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/anchors-guide.md",
      "line": 86,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/anchors-guide.md",
      "line": 99,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/anchors-guide.md",
      "line": 114,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/anchors-guide.md",
      "line": 147,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/anchors-guide.md",
      "line": 165,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/anchors-guide.md",
      "line": 193,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/anchors-guide.md",
      "line": 210,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/anchors-guide.md",
      "line": 251,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/anchors-guide.md",
      "line": 272,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/anchors-guide.md",
      "line": 278,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/anchors-guide.md",
      "line": 284,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/anchors-guide.md",
      "line": 290,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/anchors-guide.md",
      "line": 298,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/anchors-guide.md",
      "line": 308,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/anchors-guide.md",
      "line": 232,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/anchors-guide.md",
      "line": 119,
      "type": "json",
      "status": "pass",
      "message": "Valid JSON"
    },
    {
      "file": "docs/v253_migration_safety.md",
      "line": 24,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_migration_safety.md",
      "line": 115,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_migration_safety.md",
      "line": 183,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_migration_safety.md",
      "line": 275,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_migration_safety.md",
      "line": 346,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_migration_safety.md",
      "line": 428,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/troubleshooting.md",
      "line": 6,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/troubleshooting.md",
      "line": 24,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/troubleshooting.md",
      "line": 47,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/troubleshooting.md",
      "line": 102,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/troubleshooting.md",
      "line": 137,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/troubleshooting.md",
      "line": 190,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/troubleshooting.md",
      "line": 204,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/troubleshooting.md",
      "line": 125,
      "type": "json",
      "status": "fail",
      "message": "Invalid JSON at line 9, col 4: Extra data"
    },
    {
      "file": "docs/troubleshooting.md",
      "line": 167,
      "type": "json",
      "status": "pass",
      "message": "Valid JSON"
    },
    {
      "file": "docs/v2.3-roadmap.md",
      "line": 359,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/v2.3-roadmap.md",
      "line": 118,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_migration_complete.md",
      "line": 39,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/v253_migration_complete.md",
      "line": 69,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/v253_migration_complete.md",
      "line": 129,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 27,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/tutorials.md",
      "line": 42,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/tutorials.md",
      "line": 290,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/tutorials.md",
      "line": 304,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/tutorials.md",
      "line": 322,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/tutorials.md",
      "line": 1203,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/tutorials.md",
      "line": 1214,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/tutorials.md",
      "line": 1223,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/tutorials.md",
      "line": 1242,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/tutorials.md",
      "line": 55,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 78,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 126,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 159,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 191,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 223,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 260,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 277,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 360,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 385,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 407,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 428,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 457,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 492,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 527,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 567,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid | Imports are valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 593,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 640,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 733,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 841,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 947,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 987,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 1037,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 1145,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 1260,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/tutorials.md",
      "line": 334,
      "type": "json",
      "status": "fail",
      "message": "Invalid JSON at line 13, col 4: Extra data"
    },
    {
      "file": "docs/v253_actant_design.md",
      "line": 11,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_actant_design.md",
      "line": 23,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_actant_design.md",
      "line": 48,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_actant_design.md",
      "line": 69,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_compatible_design.md",
      "line": 34,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_compatible_design.md",
      "line": 52,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_compatible_design.md",
      "line": 88,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_compatible_design.md",
      "line": 103,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_compatible_design.md",
      "line": 146,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_compatible_design.md",
      "line": 170,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/developer_guide.md",
      "line": 20,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/developer_guide.md",
      "line": 67,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/developer_guide.md",
      "line": 109,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/developer_guide.md",
      "line": 147,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/developer_guide.md",
      "line": 205,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/developer_guide.md",
      "line": 247,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/developer_guide.md",
      "line": 289,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/get-started.md",
      "line": 24,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 31,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 49,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 59,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 71,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 85,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 94,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 104,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 121,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 134,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 153,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 173,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 186,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 199,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 209,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 222,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 242,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 281,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 308,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 325,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 338,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 349,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 362,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 386,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 407,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/get-started.md",
      "line": 257,
      "type": "json",
      "status": "pass",
      "message": "Valid JSON"
    },
    {
      "file": "docs/get-started.md",
      "line": 425,
      "type": "json",
      "status": "pass",
      "message": "Valid JSON"
    },
    {
      "file": "docs/installation.md",
      "line": 16,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/installation.md",
      "line": 35,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/installation.md",
      "line": 54,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/installation.md",
      "line": 110,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/installation.md",
      "line": 120,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/installation.md",
      "line": 132,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/installation.md",
      "line": 155,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/installation.md",
      "line": 167,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/installation.md",
      "line": 144,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/installation.md",
      "line": 73,
      "type": "json",
      "status": "fail",
      "message": "Invalid JSON at line 8, col 23: Expecting property name enclosed in double quotes"
    },
    {
      "file": "docs/v253_ai_migration_design.md",
      "line": 263,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/v253_ai_migration_design.md",
      "line": 44,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_ai_migration_design.md",
      "line": 73,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_ai_migration_design.md",
      "line": 97,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_ai_migration_design.md",
      "line": 159,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/v253_ai_migration_design.md",
      "line": 215,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/claude-setup.md",
      "line": 12,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/claude-setup.md",
      "line": 133,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/claude-setup.md",
      "line": 177,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/claude-setup.md",
      "line": 190,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/claude-setup.md",
      "line": 218,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/claude-setup.md",
      "line": 229,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/claude-setup.md",
      "line": 45,
      "type": "json",
      "status": "pass",
      "message": "Valid JSON"
    },
    {
      "file": "docs/claude-setup.md",
      "line": 61,
      "type": "json",
      "status": "pass",
      "message": "Valid JSON"
    },
    {
      "file": "docs/claude-setup.md",
      "line": 82,
      "type": "json",
      "status": "pass",
      "message": "Valid JSON"
    },
    {
      "file": "docs/claude-setup.md",
      "line": 97,
      "type": "json",
      "status": "pass",
      "message": "Valid JSON"
    },
    {
      "file": "docs/claude-setup.md",
      "line": 112,
      "type": "json",
      "status": "pass",
      "message": "Valid JSON"
    },
    {
      "file": "docs/api-reference.md",
      "line": 645,
      "type": "cli",
      "status": "fail",
      "message": "Command not found or failed: Usage: python -m greeum.cli [OPTIONS] COMMAND [ARGS]...\nTry 'python -m greeum.cli --help' for help.\n\nError: No such command 'anchors'.\n"
    },
    {
      "file": "docs/api-reference.md",
      "line": 657,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/api-reference.md",
      "line": 669,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/api-reference.md",
      "line": 683,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/api-reference.md",
      "line": 710,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/api-reference.md",
      "line": 736,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/api-reference.md",
      "line": 753,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/api-reference.md",
      "line": 1054,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/api-reference.md",
      "line": 53,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 78,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 93,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 101,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 112,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 124,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 138,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 152,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 167,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 176,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 189,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 201,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 216,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 228,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 240,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 257,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 272,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 297,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 307,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 336,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 346,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 365,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 375,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 389,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 402,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 417,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 427,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 446,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 461,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 498,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 509,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 522,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 536,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 552,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 562,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 572,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 586,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 600,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 619,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 788,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 798,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 810,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 820,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 831,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 840,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 898,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 909,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 923,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 933,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 954,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 965,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 982,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 995,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 1017,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 1035,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/api-reference.md",
      "line": 715,
      "type": "json",
      "status": "pass",
      "message": "Valid JSON"
    },
    {
      "file": "docs/api-reference.md",
      "line": 762,
      "type": "json",
      "status": "fail",
      "message": "Invalid JSON at line 2, col 15: Expecting value"
    },
    {
      "file": "docs/api-reference.md",
      "line": 852,
      "type": "json",
      "status": "pass",
      "message": "Valid JSON"
    },
    {
      "file": "docs/api-reference.md",
      "line": 869,
      "type": "json",
      "status": "pass",
      "message": "Valid JSON"
    },
    {
      "file": "docs/api-reference.md",
      "line": 1077,
      "type": "json",
      "status": "pass",
      "message": "Valid JSON"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_AI_MIGRATION_STRATEGY.md",
      "line": 68,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_AI_MIGRATION_STRATEGY.md",
      "line": 101,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_AI_MIGRATION_STRATEGY.md",
      "line": 122,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_AI_MIGRATION_STRATEGY.md",
      "line": 145,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line": 33,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line": 86,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line": 121,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line": 162,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line": 195,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line": 219,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line": 251,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line": 284,
      "type": "python",
      "status": "fail",
      "message": "Syntax error at line 2: invalid decimal literal"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_LLM_PARSING_DESIGN.md",
      "line": 347,
      "type": "python",
      "status": "fail",
      "message": "Syntax error at line 9: invalid character '→' (U+2192)"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_CONTEXT_DEPENDENT_MEMORY.md",
      "line": 44,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_CONTEXT_DEPENDENT_MEMORY.md",
      "line": 125,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_CONTEXT_DEPENDENT_MEMORY.md",
      "line": 163,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_CONTEXT_DEPENDENT_MEMORY.md",
      "line": 216,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_CLEAN_SLATE_DESIGN.md",
      "line": 22,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_CLEAN_SLATE_DESIGN.md",
      "line": 57,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_CLEAN_SLATE_DESIGN.md",
      "line": 132,
      "type": "python",
      "status": "fail",
      "message": "Syntax error at line 7: 'await' outside function"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_CLEAN_SLATE_DESIGN.md",
      "line": 229,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_CLEAN_SLATE_DESIGN.md",
      "line": 241,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_CLEAN_SLATE_DESIGN.md",
      "line": 250,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_NEURAL_MEMORY_DESIGN.md",
      "line": 19,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_NEURAL_MEMORY_DESIGN.md",
      "line": 34,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_NEURAL_MEMORY_DESIGN.md",
      "line": 49,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_NEURAL_MEMORY_DESIGN.md",
      "line": 110,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_NEURAL_MEMORY_DESIGN.md",
      "line": 126,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_NEURAL_MEMORY_DESIGN.md",
      "line": 148,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_NEURAL_MEMORY_DESIGN.md",
      "line": 215,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_IMPLEMENTATION_PLAN.md",
      "line": 28,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_IMPLEMENTATION_PLAN.md",
      "line": 80,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_IMPLEMENTATION_PLAN.md",
      "line": 134,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_IMPLEMENTATION_PLAN.md",
      "line": 177,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_IMPLEMENTATION_PLAN.md",
      "line": 226,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_IMPLEMENTATION_PLAN.md",
      "line": 271,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_IMPLEMENTATION_PLAN.md",
      "line": 337,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/actant_identity_system_design.md",
      "line": 10,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/actant_identity_system_design.md",
      "line": 30,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/actant_identity_system_design.md",
      "line": 46,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/actant_identity_system_design.md",
      "line": 54,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/actant_identity_system_design.md",
      "line": 101,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/actant_identity_system_design.md",
      "line": 123,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ARCHITECTURE_DESIGN.md",
      "line": 156,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ARCHITECTURE_DESIGN.md",
      "line": 255,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ARCHITECTURE_DESIGN.md",
      "line": 329,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ARCHITECTURE_DESIGN.md",
      "line": 441,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ARCHITECTURE_DESIGN.md",
      "line": 523,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line": 366,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line": 30,
      "type": "python",
      "status": "fail",
      "message": "Syntax error at line 8: invalid character '✓' (U+2713)"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line": 44,
      "type": "python",
      "status": "fail",
      "message": "Syntax error at line 24: invalid character '✓' (U+2713)"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line": 101,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line": 127,
      "type": "python",
      "status": "fail",
      "message": "Syntax error at line 27: invalid character '✓' (U+2713)"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line": 160,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line": 186,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line": 226,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line": 265,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line": 288,
      "type": "python",
      "status": "fail",
      "message": "Syntax error at line 2: invalid syntax"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line": 315,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line": 349,
      "type": "python",
      "status": "fail",
      "message": "Syntax error at line 7: invalid decimal literal"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ALPHA_MILESTONES.md",
      "line": 376,
      "type": "python",
      "status": "fail",
      "message": "Syntax error at line 10: invalid syntax"
    },
    {
      "file": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line": 20,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line": 66,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line": 106,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line": 128,
      "type": "python",
      "status": "fail",
      "message": "Syntax error at line 10: invalid syntax. Perhaps you forgot a comma?"
    },
    {
      "file": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line": 155,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line": 190,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line": 221,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line": 251,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line": 342,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line": 362,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line": 379,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line": 393,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line": 427,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.1_SEMANTIC_TAGGING_DESIGN.md",
      "line": 444,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ACTANT_SCHEMA_DESIGN.md",
      "line": 120,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ACTANT_SCHEMA_DESIGN.md",
      "line": 148,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ACTANT_SCHEMA_DESIGN.md",
      "line": 169,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ACTANT_SCHEMA_DESIGN.md",
      "line": 196,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ACTANT_SCHEMA_DESIGN.md",
      "line": 258,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_ACTANT_SCHEMA_DESIGN.md",
      "line": 296,
      "type": "json",
      "status": "pass",
      "message": "Valid JSON"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 160,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 337,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 377,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 389,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 65,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 83,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 111,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 201,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 289,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 300,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 312,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 325,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 352,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 383,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 396,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 47,
      "type": "json",
      "status": "fail",
      "message": "Invalid JSON at line 4, col 27: Expecting value"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 224,
      "type": "json",
      "status": "fail",
      "message": "Invalid JSON at line 7, col 31: Expecting value"
    },
    {
      "file": "docs/design/anchorized-memory.md",
      "line": 244,
      "type": "json",
      "status": "pass",
      "message": "Valid JSON"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_FINAL_SUMMARY.md",
      "line": 24,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_FINAL_SUMMARY.md",
      "line": 43,
      "type": "python",
      "status": "fail",
      "message": "Syntax error at line 13: expected an indented block after function definition on line 11"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_FINAL_SUMMARY.md",
      "line": 65,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_FINAL_SUMMARY.md",
      "line": 126,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V3.0.0_FINAL_SUMMARY.md",
      "line": 143,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/design/GREEUM_V2.7.0_ROADMAP.md",
      "line": 55,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/design/GREEUM_V2.7.0_ROADMAP.md",
      "line": 184,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/design/GREEUM_V2.7.0_ROADMAP.md",
      "line": 306,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/design/GREEUM_V2.7.0_ROADMAP.md",
      "line": 82,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/releases/RELEASE_NOTES_v2.6.4.md",
      "line": 68,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/releases/RELEASE_NOTES_v2.6.4.md",
      "line": 73,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/releases/RELEASE_NOTES_v2.6.4.md",
      "line": 119,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/releases/RELEASE_NOTES_v2.6.4.md",
      "line": 134,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/releases/RELEASE_NOTES_v3.0.0-alpha.1.md",
      "line": 103,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/releases/RELEASE_NOTES_v3.0.0-alpha.1.md",
      "line": 199,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/releases/RELEASE_NOTES_v3.0.0-alpha.1.md",
      "line": 64,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/releases/RELEASE_NOTES_v3.0.0-alpha.1.md",
      "line": 79,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/releases/RELEASE_NOTES_v3.0.0-alpha.1.md",
      "line": 150,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/releases/RELEASE_NOTES_v3.0.0-alpha.1.md",
      "line": 205,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/releases/RELEASE_NOTES_v3.0.0-alpha.1.md",
      "line": 111,
      "type": "json",
      "status": "pass",
      "message": "Valid JSON"
    },
    {
      "file": "docs/releases/RELEASE_NOTES_v2.4.0rc1.md",
      "line": 46,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/i18n/README_KR.md",
      "line": 42,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/i18n/README_KR.md",
      "line": 81,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/i18n/README_KR.md",
      "line": 100,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/i18n/README_KR.md",
      "line": 203,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/i18n/README_KR.md",
      "line": 180,
      "type": "json",
      "status": "fail",
      "message": "Invalid JSON at line 7, col 31: Expecting value"
    },
    {
      "file": "docs/i18n/README_JP.md",
      "line": 29,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/i18n/README_JP.md",
      "line": 39,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/i18n/README_JP.md",
      "line": 116,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/i18n/README_JP.md",
      "line": 175,
      "type": "cli",
      "status": "pass",
      "message": "Command exists and responds to --help"
    },
    {
      "file": "docs/i18n/README_JP.md",
      "line": 234,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/i18n/README_JP.md",
      "line": 96,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/i18n/README_JP.md",
      "line": 200,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/i18n/README_JP.md",
      "line": 180,
      "type": "json",
      "status": "fail",
      "message": "Invalid JSON at line 12, col 4: Extra data"
    },
    {
      "file": "docs/i18n/README_EN.md",
      "line": 29,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/i18n/README_EN.md",
      "line": 39,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/i18n/README_EN.md",
      "line": 144,
      "type": "cli",
      "status": "pass",
      "message": "Command exists and responds to --help"
    },
    {
      "file": "docs/i18n/README_EN.md",
      "line": 203,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/i18n/README_EN.md",
      "line": 85,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/i18n/README_EN.md",
      "line": 169,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/i18n/README_EN.md",
      "line": 149,
      "type": "json",
      "status": "fail",
      "message": "Invalid JSON at line 12, col 4: Extra data"
    },
    {
      "file": "docs/i18n/README_ZH.md",
      "line": 29,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/i18n/README_ZH.md",
      "line": 39,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/i18n/README_ZH.md",
      "line": 116,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/i18n/README_ZH.md",
      "line": 175,
      "type": "cli",
      "status": "pass",
      "message": "Command exists and responds to --help"
    },
    {
      "file": "docs/i18n/README_ZH.md",
      "line": 234,
      "type": "cli",
      "status": "skip",
      "message": "Not a greeum command"
    },
    {
      "file": "docs/i18n/README_ZH.md",
      "line": 96,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/i18n/README_ZH.md",
      "line": 200,
      "type": "python",
      "status": "pass",
      "message": "Syntax is valid"
    },
    {
      "file": "docs/i18n/README_ZH.md",
      "line": 180,
      "type": "json",
      "status": "fail",
      "message": "Invalid JSON at line 12, col 4: Extra data"
    }
  ],
  "summary": {
    "total": 360,
    "passed": 230,
    "failed": 23,
    "skipped": 107
  }
}