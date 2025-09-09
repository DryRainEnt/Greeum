"""
Migration Validation and Rollback System
Comprehensive validation and emergency rollback for AI-powered migration
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging

from .schema_version import SchemaVersionManager, SchemaVersion
from .backup_system import AtomicBackupSystem, BackupMetadata
from .ai_parser import ActantParseResult

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation failures"""
    pass


class RollbackError(Exception):
    """Custom exception for rollback failures"""
    pass


class MigrationValidator:
    """
    Comprehensive validation system for migration operations
    Validates data integrity, schema compliance, and functional correctness
    """
    
    def __init__(self, db_path: str, backup_system: AtomicBackupSystem):
        self.db_path = db_path
        self.backup_system = backup_system
        self.validation_results = {}
    
    def validate_full_migration(self, backup_id: str) -> Dict[str, Any]:
        """
        Perform comprehensive migration validation
        
        Args:
            backup_id: ID of backup used for migration
            
        Returns:
            Dict containing detailed validation results
        """
        results = {
            "overall_status": "UNKNOWN",
            "validation_timestamp": datetime.now().isoformat(),
            "backup_id": backup_id,
            "checks": {}
        }
        
        try:
            # 1. Database Integrity Check
            results["checks"]["database_integrity"] = self._check_database_integrity()
            
            # 2. Schema Validation
            results["checks"]["schema_validation"] = self._validate_schema_structure()
            
            # 3. Data Preservation Check
            results["checks"]["data_preservation"] = self._validate_data_preservation(backup_id)
            
            # 4. Actant Data Quality Check
            results["checks"]["actant_quality"] = self._validate_actant_data_quality()
            
            # 5. Relationship Consistency Check
            results["checks"]["relationship_consistency"] = self._validate_relationship_consistency()
            
            # 6. Performance Impact Check
            results["checks"]["performance_impact"] = self._check_performance_impact()
            
            # 7. Rollback Preparedness Check
            results["checks"]["rollback_preparedness"] = self._validate_rollback_readiness(backup_id)
            
            # Determine overall status
            results["overall_status"] = self._determine_overall_status(results["checks"])
            
            # Store validation results
            self._store_validation_results(results)
            
        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            results["overall_status"] = "CRITICAL_FAILURE"
            results["error"] = str(e)
        
        return results
    
    def _check_database_integrity(self) -> Dict[str, Any]:
        """Check SQLite database integrity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # SQLite integrity check
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            # Quick consistency check
            cursor.execute("PRAGMA quick_check")
            quick_result = cursor.fetchone()[0]
            
            # Foreign key check
            cursor.execute("PRAGMA foreign_key_check")
            fk_errors = cursor.fetchall()
            
            conn.close()
            
            return {
                "status": "PASS" if integrity_result == "ok" and quick_result == "ok" and not fk_errors else "FAIL",
                "integrity_check": integrity_result,
                "quick_check": quick_result,
                "foreign_key_errors": len(fk_errors),
                "error_details": fk_errors[:5] if fk_errors else None
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    def _validate_schema_structure(self) -> Dict[str, Any]:
        """Validate that schema matches v2.5.3 requirements"""
        try:
            version_manager = SchemaVersionManager(self.db_path)
            version_manager.connect()
            
            # Check schema version
            version = version_manager.detect_schema_version()
            
            # Validate schema integrity
            schema_validation = version_manager.validate_schema_integrity()
            
            version_manager.close()
            
            return {
                "status": "PASS" if schema_validation["valid"] else "FAIL",
                "detected_version": version.value,
                "expected_version": SchemaVersion.V253_ACTANT.value,
                "errors": schema_validation.get("errors", []),
                "warnings": schema_validation.get("warnings", [])
            }
            
        except Exception as e:
            return {
                "status": "ERROR", 
                "error": str(e)
            }
    
    def _validate_data_preservation(self, backup_id: str) -> Dict[str, Any]:
        """Validate that original data was preserved during migration"""
        try:
            if backup_id not in self.backup_system.active_backups:
                return {
                    "status": "ERROR",
                    "error": f"Backup {backup_id} not found"
                }
            
            # Get backup metadata
            backup_meta = self.backup_system.active_backups[backup_id]
            
            # Restore backup to temporary location for comparison
            temp_restore = Path(self.db_path).parent / f"temp_validation_{backup_id}.db"
            
            try:
                success = self.backup_system.restore_backup(backup_id, str(temp_restore))
                if not success:
                    return {
                        "status": "ERROR",
                        "error": "Failed to restore backup for validation"
                    }
                
                # Compare critical data
                comparison_results = self._compare_critical_data(str(temp_restore), self.db_path)
                
                return {
                    "status": "PASS" if comparison_results["data_preserved"] else "FAIL",
                    "backup_verified": backup_meta.backup_verified,
                    "data_preservation_rate": comparison_results["preservation_rate"],
                    "missing_records": comparison_results["missing_records"],
                    "modified_records": comparison_results["modified_records"]
                }
                
            finally:
                if temp_restore.exists():
                    temp_restore.unlink()
                    
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    def _compare_critical_data(self, backup_path: str, current_path: str) -> Dict[str, Any]:
        """Compare critical data between backup and current database"""
        try:
            backup_conn = sqlite3.connect(backup_path)
            current_conn = sqlite3.connect(current_path)
            
            # Get original data from backup
            backup_cursor = backup_conn.cursor()
            backup_cursor.execute("SELECT block_index, context, hash FROM blocks ORDER BY block_index")
            original_blocks = {row[0]: (row[1], row[2]) for row in backup_cursor.fetchall()}
            
            # Get current data
            current_cursor = current_conn.cursor()
            current_cursor.execute("SELECT block_index, context, hash FROM blocks ORDER BY block_index")
            current_blocks = {row[0]: (row[1], row[2]) for row in current_cursor.fetchall()}
            
            # Compare
            missing_records = []
            modified_records = []
            
            for block_index, (orig_context, orig_hash) in original_blocks.items():
                if block_index not in current_blocks:
                    missing_records.append(block_index)
                else:
                    curr_context, curr_hash = current_blocks[block_index]
                    if orig_context != curr_context or orig_hash != curr_hash:
                        modified_records.append({
                            "block_index": block_index,
                            "context_changed": orig_context != curr_context,
                            "hash_changed": orig_hash != curr_hash
                        })
            
            preservation_rate = 1.0 - (len(missing_records) + len(modified_records)) / len(original_blocks)
            
            backup_conn.close()
            current_conn.close()
            
            return {
                "data_preserved": len(missing_records) == 0 and len(modified_records) == 0,
                "preservation_rate": preservation_rate,
                "missing_records": missing_records,
                "modified_records": modified_records,
                "total_original": len(original_blocks),
                "total_current": len(current_blocks)
            }
            
        except Exception as e:
            return {
                "data_preserved": False,
                "preservation_rate": 0.0,
                "error": str(e),
                "missing_records": [],
                "modified_records": []
            }
    
    def _validate_actant_data_quality(self) -> Dict[str, Any]:
        """Validate quality of actant parsing results"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get actant parsing statistics
            cursor.execute("SELECT COUNT(*) FROM blocks")
            total_blocks = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM blocks WHERE actant_subject IS NOT NULL")
            parsed_blocks = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM blocks 
                WHERE actant_subject IS NOT NULL 
                AND actant_action IS NOT NULL 
                AND actant_object IS NOT NULL
            """)
            complete_actants = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT AVG(migration_confidence) FROM blocks 
                WHERE migration_confidence IS NOT NULL
            """)
            avg_confidence = cursor.fetchone()[0] or 0.0
            
            cursor.execute("""
                SELECT COUNT(*) FROM blocks 
                WHERE migration_confidence >= 0.8
            """)
            high_confidence = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM blocks 
                WHERE migration_confidence >= 0.5 AND migration_confidence < 0.8
            """)
            medium_confidence = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM blocks 
                WHERE migration_confidence < 0.5 AND migration_confidence IS NOT NULL
            """)
            low_confidence = cursor.fetchone()[0]
            
            conn.close()
            
            parsing_rate = parsed_blocks / total_blocks if total_blocks > 0 else 0
            completeness_rate = complete_actants / parsed_blocks if parsed_blocks > 0 else 0
            
            # Determine status based on quality metrics
            status = "PASS"
            if parsing_rate < 0.5:
                status = "WARN"
            if parsing_rate < 0.3 or avg_confidence < 0.5:
                status = "FAIL"
            
            return {
                "status": status,
                "total_blocks": total_blocks,
                "parsed_blocks": parsed_blocks,
                "complete_actants": complete_actants,
                "parsing_rate": parsing_rate,
                "completeness_rate": completeness_rate,
                "avg_confidence": avg_confidence,
                "confidence_distribution": {
                    "high": high_confidence,
                    "medium": medium_confidence, 
                    "low": low_confidence
                }
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    def _validate_relationship_consistency(self) -> Dict[str, Any]:
        """Validate relationship data consistency"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if relationship table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='actant_relationships'
            """)
            
            if not cursor.fetchone():
                return {
                    "status": "WARN",
                    "message": "Relationship table not found"
                }
            
            # Count relationships
            cursor.execute("SELECT COUNT(*) FROM actant_relationships")
            total_relationships = cursor.fetchone()[0]
            
            # Check for orphaned relationships
            cursor.execute("""
                SELECT COUNT(*) FROM actant_relationships ar
                WHERE NOT EXISTS (
                    SELECT 1 FROM blocks b WHERE b.block_index = ar.source_block
                ) OR NOT EXISTS (
                    SELECT 1 FROM blocks b WHERE b.block_index = ar.target_block
                )
            """)
            orphaned_relationships = cursor.fetchone()[0]
            
            # Check relationship type distribution
            cursor.execute("""
                SELECT relationship_type, COUNT(*) 
                FROM actant_relationships 
                GROUP BY relationship_type
            """)
            type_distribution = dict(cursor.fetchall())
            
            conn.close()
            
            status = "PASS"
            if orphaned_relationships > 0:
                status = "FAIL"
            
            return {
                "status": status,
                "total_relationships": total_relationships,
                "orphaned_relationships": orphaned_relationships,
                "type_distribution": type_distribution
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    def _check_performance_impact(self) -> Dict[str, Any]:
        """Check for performance regressions after migration"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Time basic queries
            import time
            
            # Test query 1: Simple search
            start = time.time()
            cursor.execute("SELECT COUNT(*) FROM blocks WHERE context LIKE '%test%'")
            cursor.fetchone()
            query1_time = time.time() - start
            
            # Test query 2: Actant search
            start = time.time()
            cursor.execute("""
                SELECT COUNT(*) FROM blocks 
                WHERE actant_subject IS NOT NULL 
                AND actant_action LIKE '%test%'
            """)
            cursor.fetchone()
            query2_time = time.time() - start
            
            # Test query 3: Relationship query
            start = time.time()
            cursor.execute("SELECT COUNT(*) FROM actant_relationships")
            cursor.fetchone()
            query3_time = time.time() - start
            
            conn.close()
            
            # Simple performance check (queries should be fast)
            status = "PASS"
            if query1_time > 1.0 or query2_time > 1.0 or query3_time > 1.0:
                status = "WARN"
            if query1_time > 5.0 or query2_time > 5.0 or query3_time > 5.0:
                status = "FAIL"
            
            return {
                "status": status,
                "query_times": {
                    "basic_search": query1_time,
                    "actant_search": query2_time,
                    "relationship_query": query3_time
                }
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    def _validate_rollback_readiness(self, backup_id: str) -> Dict[str, Any]:
        """Validate that rollback is possible if needed"""
        try:
            if backup_id not in self.backup_system.active_backups:
                return {
                    "status": "FAIL",
                    "error": f"Backup {backup_id} not found"
                }
            
            backup_meta = self.backup_system.active_backups[backup_id]
            backup_path = Path(backup_meta.backup_path)
            
            # Check backup file exists and is readable
            if not backup_path.exists():
                return {
                    "status": "FAIL", 
                    "error": "Backup file missing"
                }
            
            # Verify backup integrity
            if not backup_meta.backup_verified:
                return {
                    "status": "WARN",
                    "message": "Backup not verified"
                }
            
            # Test restore capability (to temporary location)
            temp_test = Path(self.db_path).parent / f"rollback_test_{datetime.now().strftime('%H%M%S')}.db"
            
            try:
                restore_success = self.backup_system.restore_backup(backup_id, str(temp_test))
                
                if not restore_success:
                    return {
                        "status": "FAIL",
                        "error": "Test restore failed"
                    }
                
                # Quick validation of restored file
                test_conn = sqlite3.connect(str(temp_test))
                test_cursor = test_conn.cursor()
                test_cursor.execute("SELECT COUNT(*) FROM blocks")
                restored_count = test_cursor.fetchone()[0]
                test_conn.close()
                
                return {
                    "status": "PASS",
                    "backup_verified": backup_meta.backup_verified,
                    "backup_size": backup_path.stat().st_size,
                    "restored_record_count": restored_count,
                    "test_restore": "SUCCESS"
                }
                
            finally:
                if temp_test.exists():
                    temp_test.unlink()
                    
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    def _determine_overall_status(self, checks: Dict[str, Dict[str, Any]]) -> str:
        """Determine overall validation status from individual checks"""
        
        critical_checks = ['database_integrity', 'schema_validation', 'data_preservation']
        important_checks = ['actant_quality', 'rollback_preparedness']
        optional_checks = ['relationship_consistency', 'performance_impact']
        
        # Check critical items
        for check_name in critical_checks:
            if check_name in checks:
                status = checks[check_name].get("status", "ERROR")
                if status in ["FAIL", "ERROR"]:
                    return "CRITICAL_FAILURE"
        
        # Check important items
        important_failures = 0
        for check_name in important_checks:
            if check_name in checks:
                status = checks[check_name].get("status", "ERROR")
                if status in ["FAIL", "ERROR"]:
                    important_failures += 1
        
        if important_failures >= 2:
            return "MAJOR_ISSUES"
        elif important_failures >= 1:
            return "MINOR_ISSUES"
        
        # Check for warnings
        warnings = 0
        for check_name, check_result in checks.items():
            if check_result.get("status") == "WARN":
                warnings += 1
        
        if warnings >= 2:
            return "WARNINGS"
        elif warnings >= 1:
            return "MINOR_WARNINGS"
        
        return "VALIDATION_PASSED"
    
    def _store_validation_results(self, results: Dict[str, Any]) -> None:
        """Store validation results in database for future reference"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create validation results table if needed
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migration_validations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    validation_timestamp TEXT NOT NULL,
                    backup_id TEXT NOT NULL,
                    overall_status TEXT NOT NULL,
                    results_json TEXT NOT NULL
                )
            """)
            
            cursor.execute("""
                INSERT INTO migration_validations 
                (validation_timestamp, backup_id, overall_status, results_json)
                VALUES (?, ?, ?, ?)
            """, (
                results["validation_timestamp"],
                results["backup_id"],
                results["overall_status"],
                json.dumps(results["checks"], ensure_ascii=False)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store validation results: {e}")


class EmergencyRollbackManager:
    """
    Emergency rollback system for failed migrations
    Provides multiple rollback strategies with safety checks
    """
    
    def __init__(self, db_path: str, backup_system: AtomicBackupSystem):
        self.db_path = db_path
        self.backup_system = backup_system
    
    def perform_emergency_rollback(self, backup_id: str, reason: str = "") -> Dict[str, Any]:
        """
        Perform emergency rollback to pre-migration state
        
        Args:
            backup_id: ID of backup to restore
            reason: Reason for rollback
            
        Returns:
            Dict containing rollback results
        """
        rollback_start = datetime.now()
        
        result = {
            "rollback_timestamp": rollback_start.isoformat(),
            "backup_id": backup_id,
            "reason": reason,
            "status": "UNKNOWN",
            "steps_completed": [],
            "errors": []
        }
        
        try:
            # Step 1: Validate backup availability
            self._validate_backup_for_rollback(backup_id)
            result["steps_completed"].append("backup_validation")
            
            # Step 2: Create safety backup of current state
            current_backup_id = f"pre_rollback_{rollback_start.strftime('%Y%m%d_%H%M%S')}"
            self.backup_system.create_backup(self.db_path, current_backup_id)
            result["current_state_backup"] = current_backup_id
            result["steps_completed"].append("current_state_backup")
            
            # Step 3: Perform rollback
            rollback_success = self.backup_system.restore_backup(backup_id, self.db_path)
            
            if not rollback_success:
                raise RollbackError("Backup restore failed")
            
            result["steps_completed"].append("backup_restore")
            
            # Step 4: Validate rolled back state
            validation_results = self._validate_rollback_success(backup_id)
            result["validation"] = validation_results
            result["steps_completed"].append("rollback_validation")
            
            if validation_results["valid"]:
                result["status"] = "SUCCESS"
                logger.info(f"Emergency rollback completed successfully: {backup_id}")
            else:
                result["status"] = "PARTIAL_SUCCESS"
                result["errors"].extend(validation_results.get("errors", []))
                logger.warning(f"Rollback completed with validation issues: {backup_id}")
            
        except Exception as e:
            result["status"] = "FAILED"
            result["errors"].append(str(e))
            logger.error(f"Emergency rollback failed: {e}")
            
            # Attempt to restore current state if rollback failed
            try:
                if "current_state_backup" in result:
                    self.backup_system.restore_backup(result["current_state_backup"], self.db_path)
                    result["current_state_restored"] = True
            except Exception as restore_error:
                result["errors"].append(f"Failed to restore current state: {restore_error}")
        
        result["rollback_duration"] = (datetime.now() - rollback_start).total_seconds()
        
        # Log rollback event
        self._log_rollback_event(result)
        
        return result
    
    def _validate_backup_for_rollback(self, backup_id: str) -> None:
        """Validate that backup is suitable for rollback"""
        if backup_id not in self.backup_system.active_backups:
            raise RollbackError(f"Backup {backup_id} not found")
        
        backup_meta = self.backup_system.active_backups[backup_id]
        
        if not backup_meta.backup_verified:
            raise RollbackError(f"Backup {backup_id} not verified")
        
        backup_path = Path(backup_meta.backup_path)
        if not backup_path.exists():
            raise RollbackError(f"Backup file missing: {backup_path}")
    
    def _validate_rollback_success(self, backup_id: str) -> Dict[str, Any]:
        """Validate that rollback was successful"""
        try:
            # Basic database integrity check
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM blocks")
            block_count = cursor.fetchone()[0]
            
            # Check schema version
            version_manager = SchemaVersionManager(self.db_path)
            version_manager.connect()
            version = version_manager.detect_schema_version()
            version_manager.close()
            
            conn.close()
            
            valid = (
                integrity == "ok" and 
                block_count > 0 and
                version == SchemaVersion.V252_LEGACY  # Should be back to legacy
            )
            
            return {
                "valid": valid,
                "integrity_check": integrity,
                "block_count": block_count,
                "schema_version": version.value,
                "errors": [] if valid else ["Rollback validation failed"]
            }
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [str(e)]
            }
    
    def _log_rollback_event(self, result: Dict[str, Any]) -> None:
        """Log rollback event for audit trail"""
        try:
            log_entry = {
                "event_type": "emergency_rollback",
                "timestamp": result["rollback_timestamp"],
                "backup_id": result["backup_id"],
                "status": result["status"],
                "reason": result["reason"],
                "duration": result["rollback_duration"],
                "steps_completed": result["steps_completed"],
                "errors": result["errors"]
            }
            
            # Store in rollback log file
            log_dir = Path(self.db_path).parent / "logs"
            log_dir.mkdir(exist_ok=True)
            
            log_file = log_dir / "rollback_events.jsonl"
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                
        except Exception as e:
            logger.error(f"Failed to log rollback event: {e}")
    
    def list_rollback_options(self) -> List[Dict[str, Any]]:
        """List available rollback options"""
        options = []
        
        for backup_id, backup_meta in self.backup_system.active_backups.items():
            # Skip very old backups (older than 30 days)
            backup_time = datetime.fromisoformat(backup_meta.created_at)
            if datetime.now() - backup_time > timedelta(days=30):
                continue
            
            options.append({
                "backup_id": backup_id,
                "created_at": backup_meta.created_at,
                "source_path": backup_meta.source_path,
                "backup_verified": backup_meta.backup_verified,
                "backup_size": backup_meta.source_size
            })
        
        # Sort by creation time (newest first)
        options.sort(key=lambda x: x["created_at"], reverse=True)
        
        return options


class MigrationHealthMonitor:
    """
    Continuous health monitoring for migrated systems
    Detects issues and suggests corrective actions
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def run_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check on migrated system"""
        
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": "UNKNOWN",
            "checks": {}
        }
        
        try:
            # Database health
            health_report["checks"]["database"] = self._check_database_health()
            
            # Data quality
            health_report["checks"]["data_quality"] = self._check_data_quality()
            
            # Performance metrics
            health_report["checks"]["performance"] = self._check_performance_metrics()
            
            # Schema consistency
            health_report["checks"]["schema"] = self._check_schema_consistency()
            
            # Determine overall health
            health_report["overall_health"] = self._determine_overall_health(health_report["checks"])
            
        except Exception as e:
            health_report["overall_health"] = "ERROR"
            health_report["error"] = str(e)
        
        return health_report
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check basic database health metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Basic checks
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM blocks")
            total_blocks = cursor.fetchone()[0]
            
            # Check for growth (new data)
            cursor.execute("""
                SELECT COUNT(*) FROM blocks 
                WHERE timestamp > datetime('now', '-7 days')
            """)
            recent_blocks = cursor.fetchone()[0]
            
            conn.close()
            
            status = "HEALTHY" if integrity == "ok" and total_blocks > 0 else "UNHEALTHY"
            
            return {
                "status": status,
                "integrity": integrity,
                "total_blocks": total_blocks,
                "recent_blocks": recent_blocks,
                "growth_rate": recent_blocks / 7 if recent_blocks > 0 else 0
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    def _check_data_quality(self) -> Dict[str, Any]:
        """Check ongoing data quality metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Actant data quality
            cursor.execute("SELECT COUNT(*) FROM blocks WHERE actant_subject IS NOT NULL")
            actant_blocks = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(migration_confidence) FROM blocks WHERE migration_confidence IS NOT NULL")
            avg_confidence = cursor.fetchone()[0] or 0.0
            
            # Check for data inconsistencies
            cursor.execute("""
                SELECT COUNT(*) FROM blocks 
                WHERE LENGTH(context) = 0 OR context IS NULL
            """)
            empty_contexts = cursor.fetchone()[0]
            
            conn.close()
            
            quality_score = avg_confidence if empty_contexts == 0 else avg_confidence * 0.8
            status = "GOOD" if quality_score > 0.6 else "NEEDS_ATTENTION"
            
            return {
                "status": status,
                "actant_blocks": actant_blocks,
                "avg_confidence": avg_confidence,
                "empty_contexts": empty_contexts,
                "quality_score": quality_score
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    def _check_performance_metrics(self) -> Dict[str, Any]:
        """Check system performance metrics"""
        try:
            import time
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Time common queries
            start = time.time()
            cursor.execute("SELECT COUNT(*) FROM blocks")
            cursor.fetchone()
            count_time = time.time() - start
            
            start = time.time()
            cursor.execute("SELECT * FROM blocks ORDER BY timestamp DESC LIMIT 10")
            cursor.fetchall()
            recent_time = time.time() - start
            
            start = time.time()
            cursor.execute("""
                SELECT COUNT(*) FROM blocks 
                WHERE actant_subject = 'Claude'
            """)
            cursor.fetchone()
            search_time = time.time() - start
            
            conn.close()
            
            avg_query_time = (count_time + recent_time + search_time) / 3
            status = "GOOD" if avg_query_time < 0.1 else "SLOW"
            
            return {
                "status": status,
                "avg_query_time": avg_query_time,
                "count_query_time": count_time,
                "recent_query_time": recent_time,
                "search_query_time": search_time
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    def _check_schema_consistency(self) -> Dict[str, Any]:
        """Check schema consistency over time"""
        try:
            version_manager = SchemaVersionManager(self.db_path)
            version_manager.connect()
            
            version = version_manager.detect_schema_version()
            validation = version_manager.validate_schema_integrity()
            
            version_manager.close()
            
            status = "CONSISTENT" if validation["valid"] else "INCONSISTENT"
            
            return {
                "status": status,
                "current_version": version.value,
                "schema_valid": validation["valid"],
                "errors": validation.get("errors", [])
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    def _determine_overall_health(self, checks: Dict[str, Dict[str, Any]]) -> str:
        """Determine overall system health from individual checks"""
        
        critical_issues = 0
        moderate_issues = 0
        
        for check_name, check_result in checks.items():
            status = check_result.get("status", "ERROR")
            
            if status in ["ERROR", "UNHEALTHY", "INCONSISTENT"]:
                critical_issues += 1
            elif status in ["NEEDS_ATTENTION", "SLOW"]:
                moderate_issues += 1
        
        if critical_issues > 0:
            return "CRITICAL"
        elif moderate_issues >= 2:
            return "DEGRADED" 
        elif moderate_issues >= 1:
            return "WARNING"
        else:
            return "HEALTHY"