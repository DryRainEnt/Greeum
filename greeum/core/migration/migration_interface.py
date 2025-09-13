"""
Forced Migration Interface for v2.5.3 AI-Powered Migration
Interactive CLI interface that enforces migration when legacy databases are detected
"""

import sys
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from .schema_version import SchemaVersionManager, SchemaVersion, MigrationVersionGuard
from .backup_system import AtomicBackupSystem, TransactionSafetyWrapper
from .ai_parser import AIActantParser, ActantParseResult, RelationshipExtractor

logger = logging.getLogger(__name__)


class MigrationResult:
    """Result of migration operation"""
    
    def __init__(self):
        self.migrated_count = 0
        self.failed_count = 0
        self.success_rate = 0.0
        self.total_time = 0.0
        self.relationships_discovered = 0
        self.backup_id = None
        self.errors: List[str] = []


class ForcedMigrationInterface:
    """
    Interactive interface that forces migration when legacy databases are detected
    Implements the "forced upgrade experience" with clear value proposition
    """
    
    def __init__(self, data_dir: str, ai_client=None):
        self.data_dir = Path(data_dir)
        self.db_path = self.data_dir / "memory.db"
        
        # Initialize components
        self.version_manager = SchemaVersionManager(str(self.db_path))
        self.backup_system = AtomicBackupSystem(str(self.data_dir))
        self.ai_parser = AIActantParser(ai_client)
        self.relationship_extractor = RelationshipExtractor()
        
        # Migration state
        self.migration_required = False
        self.migration_stats = None
    
    def check_and_force_migration(self) -> bool:
        """
        Check for legacy database and force migration if needed
        
        Returns:
            bool: True if system is ready to use (migration completed or not needed)
        """
        try:
            # Check schema version
            if not self.db_path.exists():
                # New installation - no migration needed
                self._setup_new_database()
                return True
            
            version = self.version_manager.detect_schema_version()
            
            if version == SchemaVersion.V253_ACTANT:
                # Already migrated
                print("[OK] Greeum v2.5.3 database detected - ready to use!")
                return True
            
            elif version == SchemaVersion.V252_LEGACY:
                # Legacy database found - force migration
                if self.version_manager.needs_migration():
                    return self._force_migration_flow()
                else:
                    # Empty legacy database - upgrade schema only
                    return self._upgrade_empty_database()
            
            else:
                # Unknown schema version
                print("[ERROR] Unknown database schema detected")
                print("Please backup your data and reinstall Greeum v2.5.3")
                return False
                
        except Exception as e:
            logger.error(f"Migration check failed: {e}")
            print(f"[ERROR] Database check failed: {e}")
            return False
        
        finally:
            self.version_manager.close()
    
    def _force_migration_flow(self) -> bool:
        """Execute the forced migration user flow"""
        
        # Get migration statistics
        self.migration_stats = self.version_manager.get_migration_stats()
        
        # Present compelling migration case
        self._present_migration_case()
        
        # Get user consent (required to proceed)
        if not self._get_user_consent():
            print("[ERROR] Migration required to use v2.5.3. Exiting...")
            return False
        
        # Perform AI-powered migration
        print("\n[AI] Starting AI-powered migration...")
        migration_result = self._perform_ai_migration()
        
        if migration_result.migrated_count > 0:
            # Show migration results
            self._show_migration_results(migration_result)
            
            # Discover relationships
            self._discover_and_show_relationships()
            
            print("\n[SPECIAL] Your memory system is now enhanced with actant structure!")
            print("🔍 Enjoy improved search and relationship analysis capabilities!")
            return True
        else:
            print("[ERROR] Migration failed. Your original data is safe.")
            return False
    
    def _present_migration_case(self) -> None:
        """Present compelling case for migration"""
        stats = self.migration_stats
        
        print("\n" + "="*60)
        print("[ALERT] Greeum v2.5.3 Schema Migration Required")
        print("="*60)
        print(f"[INFO] Legacy database detected with {stats['total_blocks']} memories")
        print(f"[DATE] Memory range: {stats['earliest_memory']} to {stats['latest_memory']}")
        print()
        print("[TARGET] Migration Benefits:")
        print("  [FAST] AI will enhance your memories with structured actant format")
        print("  [LINK] Enables powerful relationship and causality analysis") 
        print("  [FORMAT] [Subject-Action-Object] structure for better organization")
        print("  [IMPROVE] Improved search accuracy and context discovery")
        print("  [MEMORY] Foundation for advanced memory features in v3.0")
        print()
        print("[SECURE] Safety Guarantees:")
        print("  [BACKUP] Complete backup created before any changes")
        print("  [SAFE]  Original memories preserved (context field untouched)")
        print("  [ROLLBACK]  Instant rollback available if needed")
        print("  [SPECIAL] AI parsing failures → memories preserved as-is")
        print()
        
        # Show sample contexts
        if stats.get('sample_contexts'):
            print("[NOTE] Sample memories to be enhanced:")
            for i, sample in enumerate(stats['sample_contexts'], 1):
                print(f"   {i}. {sample}")
            print()
    
    def _get_user_consent(self) -> bool:
        """Get user consent for migration"""
        print("💡 This migration is safe and reversible!")
        print("   Your original data will never be modified or lost.")
        print()
        
        max_attempts = 3
        attempts = 0
        
        while attempts < max_attempts:
            try:
                choice = input("Proceed with AI migration? [Y/n]: ").lower().strip()
                
                if choice in ['y', 'yes', '']:
                    return True
                elif choice in ['n', 'no']:
                    return False
                else:
                    print("Please enter Y for yes or N for no")
                    attempts += 1
                    
            except (KeyboardInterrupt, EOFError):
                print("\n[ERROR] Migration cancelled by user")
                return False
        
        print("[ERROR] Too many invalid attempts")
        return False
    
    def _perform_ai_migration(self) -> MigrationResult:
        """Perform the actual AI-powered migration"""
        result = MigrationResult()
        start_time = time.time()
        
        try:
            # Create safety backup
            backup_id = self.backup_system.create_backup(str(self.db_path))
            result.backup_id = backup_id
            print(f"[BACKUP] Safety backup created: {backup_id}")
            
            # Use transaction safety wrapper
            with TransactionSafetyWrapper(str(self.db_path), self.backup_system):
                # Upgrade schema first
                if not self.version_manager.upgrade_schema_to_v253():
                    raise RuntimeError("Schema upgrade failed")
                
                print("[INFO] Schema upgraded to v2.5.3")
                
                # Get all legacy blocks
                legacy_blocks = self._get_legacy_blocks()
                total_blocks = len(legacy_blocks)
                
                print(f"[INFO] Found {total_blocks} memories to migrate")
                
                # Process blocks with AI parsing
                for i, block in enumerate(legacy_blocks):
                    try:
                        # AI parsing
                        parse_result = self.ai_parser.parse_legacy_memory(block['context'])
                        
                        if parse_result.success and parse_result.confidence >= 0.5:
                            # Update block with actant data
                            self._update_block_with_actant(block['block_index'], parse_result)
                            result.migrated_count += 1
                            status = "[OK]"
                        else:
                            # Keep original (actant fields remain NULL)
                            result.failed_count += 1 
                            status = "[WARNING]"
                        
                        # Progress indicator
                        progress = (i + 1) / total_blocks * 100
                        print(f"\r{status} Migrating: {progress:.1f}% ({i+1}/{total_blocks})", end="", flush=True)
                        
                    except Exception as e:
                        logger.error(f"Migration error for block {block['block_index']}: {e}")
                        result.failed_count += 1
                        result.errors.append(str(e))
                
                print()  # New line after progress
                
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            result.errors.append(str(e))
            # TransactionSafetyWrapper will automatically restore backup
        
        result.total_time = time.time() - start_time
        total = result.migrated_count + result.failed_count
        result.success_rate = result.migrated_count / total if total > 0 else 0
        
        return result
    
    def _get_legacy_blocks(self) -> List[Dict[str, Any]]:
        """Get all legacy blocks that need migration"""
        conn = self.version_manager.conn
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT block_index, timestamp, context, importance, hash
            FROM blocks 
            WHERE actant_subject IS NULL
            ORDER BY block_index
        """)
        
        columns = ['block_index', 'timestamp', 'context', 'importance', 'hash']
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def _update_block_with_actant(self, block_index: int, parse_result: ActantParseResult) -> None:
        """Update block with parsed actant data"""
        conn = self.version_manager.conn
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE blocks 
            SET actant_subject = ?, 
                actant_action = ?, 
                actant_object = ?,
                actant_parsed_at = datetime('now'),
                migration_confidence = ?
            WHERE block_index = ?
        """, (
            parse_result.subject,
            parse_result.action,
            parse_result.object_target,
            parse_result.confidence,
            block_index
        ))
    
    def _show_migration_results(self, result: MigrationResult) -> None:
        """Display migration results to user"""
        print(f"\n[SUCCESS] Migration completed in {result.total_time:.1f} seconds!")
        print(f"[OK] Successfully migrated: {result.migrated_count}")
        print(f"[WARNING]  Preserved as-is: {result.failed_count}")
        
        if result.migrated_count + result.failed_count > 0:
            print(f"[IMPROVE] Migration success rate: {result.success_rate*100:.1f}%")
        
        if result.errors:
            print(f"[WARNING]  {len(result.errors)} errors occurred (data preserved)")
        
        # Show parsing statistics
        stats = self.ai_parser.get_parsing_stats()
        if stats['total_parsed'] > 0:
            print(f"[AI] AI parsing accuracy: {stats['success_rate']*100:.1f}%")
            print(f"   High confidence: {stats['high_confidence']}")
            print(f"   Medium confidence: {stats['medium_confidence']}")
            print(f"   Low confidence: {stats['low_confidence']}")
    
    def _discover_and_show_relationships(self) -> None:
        """Discover and display relationships in migrated data"""
        print("\n🔍 Discovering relationships in migrated data...")
        
        try:
            # Get successfully migrated blocks
            migrated_blocks = self._get_migrated_blocks()
            
            if not migrated_blocks:
                print("No migrated blocks found for relationship analysis")
                return
            
            # Extract relationships
            relationships = self.relationship_extractor.extract_relationships(migrated_blocks)
            
            total_relationships = (
                len(relationships['subject_collaborations']) +
                len(relationships['action_causalities']) + 
                len(relationships['object_dependencies'])
            )
            
            print(f"[LINK] Discovered {total_relationships} relationships:")
            print(f"   👥 Subject collaborations: {len(relationships['subject_collaborations'])}")
            print(f"   [FAST] Action causalities: {len(relationships['action_causalities'])}")
            print(f"   [LINK] Object dependencies: {len(relationships['object_dependencies'])}")
            
            # Store relationships in database
            self._store_relationships(relationships)
            
        except Exception as e:
            logger.error(f"Relationship discovery failed: {e}")
            print(f"[WARNING]  Relationship discovery failed: {e}")
    
    def _get_migrated_blocks(self) -> List[ActantParseResult]:
        """Get successfully migrated blocks as ActantParseResult objects"""
        conn = self.version_manager.conn
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT context, actant_subject, actant_action, actant_object, migration_confidence
            FROM blocks 
            WHERE actant_subject IS NOT NULL
            AND migration_confidence >= 0.5
        """)
        
        results = []
        for row in cursor.fetchall():
            result = ActantParseResult(
                subject=row[1],
                action=row[2],
                object_target=row[3],
                confidence=row[4],
                original_context=row[0],
                success=True
            )
            results.append(result)
        
        return results
    
    def _store_relationships(self, relationships: Dict[str, List[Dict]]) -> None:
        """Store discovered relationships in database"""
        conn = self.version_manager.conn
        cursor = conn.cursor()
        
        # Store each type of relationship
        for rel_type, rel_list in relationships.items():
            for rel in rel_list:
                cursor.execute("""
                    INSERT INTO actant_relationships 
                    (source_block, target_block, relationship_type, confidence, discovered_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """, (
                    rel.get('source_memory', 0),
                    rel.get('target_memory', 0), 
                    rel_type,
                    rel.get('confidence', 0.5)
                ))
        
        conn.commit()
    
    def _setup_new_database(self) -> None:
        """Setup new v2.5.3 database"""
        print("[NEW] Setting up new Greeum v2.5.3 database...")
        self.version_manager.connect()
        
        if self.version_manager.upgrade_schema_to_v253():
            print("[OK] New database initialized with v2.5.3 schema")
        else:
            raise RuntimeError("Failed to initialize new database")
    
    def _upgrade_empty_database(self) -> bool:
        """Upgrade empty legacy database to v2.5.3"""
        print("[PROCESS] Upgrading empty database to v2.5.3...")
        
        try:
            with TransactionSafetyWrapper(str(self.db_path), self.backup_system):
                if self.version_manager.upgrade_schema_to_v253():
                    print("[OK] Database upgraded to v2.5.3")
                    return True
                else:
                    raise RuntimeError("Schema upgrade failed")
                    
        except Exception as e:
            logger.error(f"Empty database upgrade failed: {e}")
            print(f"[ERROR] Upgrade failed: {e}")
            return False


class MigrationCLI:
    """Command-line interface for migration operations"""
    
    def __init__(self, data_dir: str):
        self.interface = ForcedMigrationInterface(data_dir)
    
    def run_migration_check(self) -> int:
        """
        Run migration check and return exit code
        
        Returns:
            int: 0 if ready to use, 1 if migration failed/cancelled
        """
        print("🔍 Checking Greeum database compatibility...")
        
        if self.interface.check_and_force_migration():
            return 0  # Success
        else:
            return 1  # Failed or cancelled
    
    def force_migration(self) -> int:
        """Force migration regardless of current state"""
        print("🚀 Forcing migration to v2.5.3...")
        
        if self.interface._force_migration_flow():
            return 0
        else:
            return 1


def main():
    """CLI entry point for migration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Greeum v2.5.3 Migration Tool")
    parser.add_argument("--data-dir", default="data", help="Data directory path")
    parser.add_argument("--force", action="store_true", help="Force migration")
    
    args = parser.parse_args()
    
    cli = MigrationCLI(args.data_dir)
    
    if args.force:
        exit_code = cli.force_migration()
    else:
        exit_code = cli.run_migration_check()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()