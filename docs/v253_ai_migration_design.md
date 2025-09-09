# Greeum v2.5.3: AI-Powered Schema Migration

## 🎯 **혁신적 컨셉**: AI가 직접 데이터를 해석하고 마이그레이션

**핵심 아이디어**: 구형 DB 감지 → AI 강제 마이그레이션 → 액탄트 스키마 전환

## 📊 **새로운 스키마 설계**

### v2.5.3 Enhanced Schema
```sql
-- 기존 blocks 테이블 확장
CREATE TABLE IF NOT EXISTS blocks (
    block_index INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    context TEXT NOT NULL,              -- 기존 유지 (하위 호환)
    importance REAL NOT NULL,
    hash TEXT NOT NULL,
    
    -- v2.5.3 새로운 액탄트 필드들 (기본값으로 마이그레이션 안전성 보장)
    actant_subject TEXT DEFAULT NULL,   -- AI가 파싱한 주체
    actant_action TEXT DEFAULT NULL,    -- AI가 파싱한 행동
    actant_object TEXT DEFAULT NULL,    -- AI가 파싱한 대상
    actant_parsed_at TEXT DEFAULT NULL, -- 마이그레이션 시점
    migration_confidence REAL DEFAULT NULL  -- AI 파싱 신뢰도
)

-- 새로운 관계 추론 테이블
CREATE TABLE IF NOT EXISTS actant_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_block INTEGER NOT NULL,
    target_block INTEGER NOT NULL,
    relationship_type TEXT NOT NULL,    -- 'subject_collab', 'action_causality', 'object_dependency'
    confidence REAL NOT NULL,
    discovered_at TEXT NOT NULL,
    FOREIGN KEY (source_block) REFERENCES blocks(block_index),
    FOREIGN KEY (target_block) REFERENCES blocks(block_index)
)
```

## 🤖 **AI 마이그레이션 시스템**

### 1. **Schema Version Detection**
```python
class SchemaVersionDetector:
    """스키마 버전 감지 및 마이그레이션 필요성 판단"""
    
    def detect_schema_version(self) -> SchemaVersion:
        """현재 데이터베이스 스키마 버전 확인"""
        cursor = self.conn.cursor()
        
        # actant 필드 존재 여부 확인
        cursor.execute("PRAGMA table_info(blocks)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'actant_subject' in columns:
            return SchemaVersion.V253_ACTANT
        else:
            return SchemaVersion.V252_LEGACY
    
    def needs_migration(self) -> bool:
        """마이그레이션 필요 여부 확인"""
        version = self.detect_schema_version()
        if version == SchemaVersion.V252_LEGACY:
            # 구형 데이터 존재하면 마이그레이션 필요
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM blocks")
            return cursor.fetchone()[0] > 0
        return False
```

### 2. **Forced Migration UI**
```python
class ForcedMigrationInterface:
    """사용자에게 마이그레이션을 강제하는 인터페이스"""
    
    def check_and_force_migration(self):
        """시작시 마이그레이션 필수 체크"""
        if self.detector.needs_migration():
            print("🚨 Greeum v2.5.3 Schema Migration Required")
            print("📊 Legacy database detected. AI-powered migration needed.")
            print("⚡ This will enhance your memories with actant structure.")
            print()
            
            while True:
                choice = input("Proceed with AI migration? [Y/n]: ").lower()
                if choice in ['y', 'yes', '']:
                    return self.perform_ai_migration()
                elif choice in ['n', 'no']:
                    print("❌ Migration required to use v2.5.3. Exiting...")
                    exit(1)
                else:
                    print("Please enter Y or N")
```

### 3. **AI Parsing Engine**
```python
class AIActantParser:
    """AI 기반 액탄트 패턴 파싱"""
    
    def parse_legacy_memory(self, context: str) -> ActantParseResult:
        """
        AI가 기존 메모리를 액탄트 구조로 해석
        
        사용 방법:
        1. Claude/GPT API 호출
        2. 프롬프트: "다음 텍스트를 [주체-행동-대상] 형식으로 분석해줘"
        3. 결과 파싱 및 검증
        """
        
        prompt = f'''
다음 메모리 텍스트를 그레마스 액탄트 모델의 [주체-행동-대상] 구조로 분석해주세요:

원본: "{context}"

분석 결과를 다음 JSON 형식으로 제공해주세요:
{{
    "subject": "행동을 수행한 주체 (사용자/Claude/팀/시스템)",
    "action": "구체적인 행동 (요청/발견/결정/구현/완료 등)", 
    "object": "행동의 대상",
    "confidence": 0.0-1.0,
    "original_preserved": true
}}

주의사항:
- 원본 의미를 정확히 보존해야 합니다
- 애매한 경우 confidence를 낮게 설정하세요
- subject는 반드시 명확한 행위자여야 합니다
'''

        try:
            # AI API 호출 (Claude/OpenAI)
            response = self.ai_client.complete(prompt)
            parsed = json.loads(response)
            
            return ActantParseResult(
                subject=parsed['subject'],
                action=parsed['action'],
                object_target=parsed['object'],
                confidence=parsed['confidence'],
                original_context=context,
                success=True
            )
            
        except Exception as e:
            # AI 파싱 실패시 안전한 폴백
            return ActantParseResult(
                subject=None,
                action=None, 
                object_target=None,
                confidence=0.0,
                original_context=context,
                success=False,
                error=str(e)
            )
```

### 4. **Progressive Migration Engine**
```python
class ProgressiveMigrator:
    """점진적 AI 마이그레이션 실행"""
    
    def perform_full_migration(self) -> MigrationResult:
        """전체 데이터베이스 AI 마이그레이션"""
        
        print("🤖 Starting AI-powered migration...")
        
        # 1. 스키마 업그레이드 (안전한 ALTER TABLE)
        self._upgrade_schema()
        
        # 2. 모든 기존 블록 조회
        legacy_blocks = self._get_legacy_blocks()
        print(f"📊 Found {len(legacy_blocks)} memories to migrate")
        
        # 3. 진행률 표시와 함께 순차 마이그레이션
        migrated = 0
        failed = 0
        
        for i, block in enumerate(legacy_blocks):
            try:
                # AI 파싱
                parse_result = self.ai_parser.parse_legacy_memory(block['context'])
                
                if parse_result.success and parse_result.confidence >= 0.5:
                    # 성공적 파싱 → DB 업데이트
                    self._update_block_with_actant(block['block_index'], parse_result)
                    migrated += 1
                    status = "✅"
                else:
                    # 파싱 실패 → 원본 유지 (actant 필드 NULL)
                    failed += 1
                    status = "⚠️"
                
                # 진행률 표시
                progress = (i + 1) / len(legacy_blocks) * 100
                print(f"\r{status} Migrating: {progress:.1f}% ({i+1}/{len(legacy_blocks)})", end="")
                
            except Exception as e:
                failed += 1
                print(f"\n❌ Migration error for block {block['block_index']}: {e}")
        
        print(f"\n🎉 Migration completed!")
        print(f"✅ Successfully migrated: {migrated}")
        print(f"⚠️  Preserved as-is: {failed}")
        print(f"📈 Migration success rate: {migrated/(migrated+failed)*100:.1f}%")
        
        return MigrationResult(
            migrated_count=migrated,
            failed_count=failed,
            success_rate=migrated/(migrated+failed) if (migrated+failed) > 0 else 0
        )
```

### 5. **Relationship Discovery Post-Migration**
```python
class PostMigrationRelationshipDiscovery:
    """마이그레이션 완료 후 자동 관계 발견"""
    
    def discover_relationships(self) -> None:
        """마이그레이션된 액탄트 데이터에서 관계 추론"""
        
        print("🔍 Discovering relationships in migrated data...")
        
        # 액탄트가 성공적으로 파싱된 블록들만 대상
        migrated_blocks = self._get_migrated_blocks()
        
        relationships = []
        
        for source_block in migrated_blocks:
            for target_block in migrated_blocks:
                if source_block['block_index'] == target_block['block_index']:
                    continue
                
                # 주체 협업 관계 발견
                if (source_block['actant_subject'] == target_block['actant_subject'] and
                    source_block['actant_subject'] is not None):
                    relationships.append({
                        'source': source_block['block_index'],
                        'target': target_block['block_index'],
                        'type': 'subject_collaboration',
                        'confidence': 0.8
                    })
                
                # 행동 인과관계 발견 
                if self._is_causal_action_pair(source_block['actant_action'], 
                                                target_block['actant_action']):
                    relationships.append({
                        'source': source_block['block_index'],
                        'target': target_block['block_index'],
                        'type': 'action_causality',
                        'confidence': 0.7
                    })
        
        # 관계 데이터베이스 저장
        self._store_relationships(relationships)
        print(f"🔗 Discovered {len(relationships)} relationships")
```

## 🎯 **사용자 경험 시나리오**

### 시나리오: 기존 사용자가 v2.5.3으로 업그레이드

```bash
$ greeum memory search "프로젝트"

🚨 Greeum v2.5.3 Schema Migration Required
📊 Legacy database detected with 150 memories
⚡ AI will enhance your memories with structured actant format
🤖 This enables powerful relationship and causality analysis

Proceed with AI migration? [Y/n]: y

🤖 Starting AI-powered migration...
📊 Found 150 memories to migrate

✅ Migrating: 100.0% (150/150)
🎉 Migration completed!
✅ Successfully migrated: 142
⚠️  Preserved as-is: 8
📈 Migration success rate: 94.7%

🔍 Discovering relationships in migrated data...
🔗 Discovered 89 relationships

✨ Your memory system is now enhanced with actant structure!
🔍 Search results: Found 12 project-related memories
```

## 🔒 **안전성 보장**

1. **원본 보존**: `context` 필드는 절대 변경하지 않음
2. **점진적 실패**: 일부 파싱 실패해도 시스템 정상 동작
3. **롤백 가능**: 새로운 필드만 NULL로 초기화하면 v2.5.2와 동일
4. **신뢰도 기반**: AI 파싱 신뢰도 낮으면 원본 유지

## 🎉 **v2.5.3의 혁신성**

- **AI 기반 자동 마이그레이션**: 업계 최초 AI 파워드 데이터 마이그레이션
- **강제적 업그레이드 경험**: 명확한 가치 제공과 함께 필수 전환
- **관계 발견**: 마이그레이션과 동시에 메모리 간 관계 자동 분석
- **의미있는 버전 차이**: 진짜 큰 변화를 경험할 수 있음

**이제 v2.5.3은 정말 "업그레이드할 만한 가치"가 확실한 버전이 됩니다!** 🚀