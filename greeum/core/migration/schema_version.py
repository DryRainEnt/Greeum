"""
Schema Version Management for AI-Powered Migration System
Handles detection, validation, and version transitions for Greeum v2.5.3
"""

import sqlite3
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class SchemaVersion(Enum):
    """Database schema versions"""
    V252_LEGACY = "2.5.2"
    V253_ACTANT = "2.5.3"
    UNKNOWN = "unknown"


class SchemaVersionManager:
    """Manages schema version detection and validation"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
    
    def connect(self) -> None:
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            logger.error(f"Failed to connect to database {self.db_path}: {e}")
            raise
    
    def close(self) -> None:
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def detect_schema_version(self) -> SchemaVersion:
        """
        Detect current database schema version
        
        Returns:
            SchemaVersion: Current schema version
        """
        if not self.conn:
            self.connect()
        
        try:
            cursor = self.conn.cursor()
            
            # Check if blocks table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='blocks'
            """)
            
            if not cursor.fetchone():
                # No blocks table - completely new database
                return SchemaVersion.V253_ACTANT
            
            # Check for v2.5.3 actant fields
            cursor.execute("PRAGMA table_info(blocks)")
            columns = [col[1] for col in cursor.fetchall()]
            
            actant_fields = [
                'actant_subject', 'actant_action', 'actant_object', 
                'actant_parsed_at', 'migration_confidence'
            ]
            
            if all(field in columns for field in actant_fields):
                return SchemaVersion.V253_ACTANT
            elif 'context' in columns:
                return SchemaVersion.V252_LEGACY
            else:
                return SchemaVersion.UNKNOWN
                
        except Exception as e:
            logger.error(f"Schema version detection failed: {e}")
            return SchemaVersion.UNKNOWN
    
    def needs_migration(self) -> bool:
        """
        Check if migration is needed
        
        Returns:
            bool: True if legacy data exists and needs migration
        """
        version = self.detect_schema_version()
        
        if version == SchemaVersion.V252_LEGACY:
            # Check if there's actual data to migrate
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM blocks")
            count = cursor.fetchone()[0]
            return count > 0
        
        return False
    
    def get_migration_stats(self) -> Dict[str, Any]:
        """
        Get statistics about data that needs migration
        
        Returns:
            Dict containing migration statistics
        """
        if not self.needs_migration():
            return {"needs_migration": False}
        
        cursor = self.conn.cursor()
        
        # Count total blocks
        cursor.execute("SELECT COUNT(*) FROM blocks")
        total_blocks = cursor.fetchone()[0]
        
        # Get date range
        cursor.execute("""
            SELECT MIN(timestamp) as earliest, MAX(timestamp) as latest 
            FROM blocks
        """)
        date_range = cursor.fetchone()
        
        # Sample some contexts for complexity analysis
        cursor.execute("""
            SELECT context, LENGTH(context) as length 
            FROM blocks 
            ORDER BY RANDOM() 
            LIMIT 10
        """)
        samples = cursor.fetchall()
        
        avg_length = sum(row[1] for row in samples) / len(samples) if samples else 0
        
        return {
            "needs_migration": True,
            "total_blocks": total_blocks,
            "earliest_memory": date_range[0] if date_range else None,
            "latest_memory": date_range[1] if date_range else None,
            "avg_context_length": avg_length,
            "sample_contexts": [row[0][:100] + "..." if len(row[0]) > 100 else row[0] 
                             for row in samples[:3]]
        }
    
    def upgrade_schema_to_v253(self) -> bool:
        """
        Safely upgrade database schema to v2.5.3 actant format
        
        Returns:
            bool: True if upgrade successful
        """
        try:
            cursor = self.conn.cursor()
            
            # Add actant fields to blocks table (safe ALTER TABLE)
            actant_additions = [
                "ALTER TABLE blocks ADD COLUMN actant_subject TEXT DEFAULT NULL",
                "ALTER TABLE blocks ADD COLUMN actant_action TEXT DEFAULT NULL", 
                "ALTER TABLE blocks ADD COLUMN actant_object TEXT DEFAULT NULL",
                "ALTER TABLE blocks ADD COLUMN actant_parsed_at TEXT DEFAULT NULL",
                "ALTER TABLE blocks ADD COLUMN migration_confidence REAL DEFAULT NULL"
            ]
            
            for sql in actant_additions:
                try:
                    cursor.execute(sql)
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        # Column already exists, skip
                        logger.info(f"Column already exists, skipping: {sql}")
                        continue
                    else:
                        raise
            
            # Create actant relationships table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS actant_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_block INTEGER NOT NULL,
                    target_block INTEGER NOT NULL,
                    relationship_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    discovered_at TEXT NOT NULL,
                    FOREIGN KEY (source_block) REFERENCES blocks(block_index),
                    FOREIGN KEY (target_block) REFERENCES blocks(block_index)
                )
            """)
            
            # Create schema version tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_versions (
                    version TEXT PRIMARY KEY,
                    upgraded_at TEXT NOT NULL,
                    migration_stats TEXT
                )
            """)
            
            # Record schema upgrade
            cursor.execute("""
                INSERT OR REPLACE INTO schema_versions 
                (version, upgraded_at, migration_stats) 
                VALUES (?, ?, ?)
            """, (
                SchemaVersion.V253_ACTANT.value,
                datetime.now().isoformat(),
                "Schema upgraded to v2.5.3 actant format"
            ))
            
            self.conn.commit()
            logger.info("Successfully upgraded schema to v2.5.3")
            return True
            
        except Exception as e:
            logger.error(f"Schema upgrade failed: {e}")
            self.conn.rollback()
            return False
    
    def validate_schema_integrity(self) -> Dict[str, Any]:
        """
        Validate schema integrity after migration
        
        Returns:
            Dict containing validation results
        """
        try:
            cursor = self.conn.cursor()
            results = {
                "valid": True,
                "errors": [],
                "warnings": []
            }
            
            # Check required tables exist
            required_tables = ['blocks', 'actant_relationships', 'schema_versions']
            for table in required_tables:
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table,))
                
                if not cursor.fetchone():
                    results["valid"] = False
                    results["errors"].append(f"Missing required table: {table}")
            
            # Check blocks table has all required columns
            cursor.execute("PRAGMA table_info(blocks)")
            columns = [col[1] for col in cursor.fetchall()]
            
            required_columns = [
                'block_index', 'timestamp', 'context', 'importance', 'hash',
                'actant_subject', 'actant_action', 'actant_object', 
                'actant_parsed_at', 'migration_confidence'
            ]
            
            for column in required_columns:
                if column not in columns:
                    results["valid"] = False
                    results["errors"].append(f"Missing required column: {column}")
            
            # Check for orphaned data
            cursor.execute("""
                SELECT COUNT(*) FROM blocks 
                WHERE actant_subject IS NOT NULL 
                AND (actant_action IS NULL OR actant_object IS NULL)
            """)
            
            partial_actants = cursor.fetchone()[0]
            if partial_actants > 0:
                results["warnings"].append(
                    f"{partial_actants} blocks have incomplete actant parsing"
                )
            
            return results
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation failed: {e}"],
                "warnings": []
            }


class MigrationVersionGuard:
    """Guards against operations on incompatible schema versions"""
    
    def __init__(self, version_manager: SchemaVersionManager):
        self.version_manager = version_manager
        self.required_version = SchemaVersion.V253_ACTANT
    
    def check_compatibility(self) -> bool:
        """Check if current schema is compatible with operations"""
        current_version = self.version_manager.detect_schema_version()
        return current_version == self.required_version
    
    def enforce_compatibility(self) -> None:
        """Raise exception if schema is incompatible"""
        if not self.check_compatibility():
            current = self.version_manager.detect_schema_version()
            raise RuntimeError(
                f"Schema version {current.value} is incompatible. "
                f"Required: {self.required_version.value}. "
                "Please run migration first."
            )