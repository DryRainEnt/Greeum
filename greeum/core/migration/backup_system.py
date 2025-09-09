"""
Atomic Backup System for AI-Powered Migration
Provides complete data protection during schema migration
"""

import os
import shutil
import sqlite3
import hashlib
import json
import gzip
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class BackupMetadata:
    """Metadata for backup operations"""
    
    def __init__(self, backup_id: str, source_path: str, backup_path: str):
        self.backup_id = backup_id
        self.source_path = source_path
        self.backup_path = backup_path
        self.created_at = datetime.now().isoformat()
        self.source_size = os.path.getsize(source_path) if os.path.exists(source_path) else 0
        self.source_hash = self._calculate_file_hash(source_path)
        self.backup_verified = False
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        if not os.path.exists(file_path):
            return ""
        
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "backup_id": self.backup_id,
            "source_path": self.source_path,
            "backup_path": self.backup_path,
            "created_at": self.created_at,
            "source_size": self.source_size,
            "source_hash": self.source_hash,
            "backup_verified": self.backup_verified
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupMetadata':
        """Create from dictionary"""
        backup = cls(data["backup_id"], data["source_path"], data["backup_path"])
        backup.created_at = data["created_at"]
        backup.source_size = data["source_size"]
        backup.source_hash = data["source_hash"]
        backup.backup_verified = data.get("backup_verified", False)
        return backup


class AtomicBackupSystem:
    """
    Atomic backup system with verification and rollback capabilities
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.backup_dir = self.data_dir / "migration_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        self.active_backups: Dict[str, BackupMetadata] = {}
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load backup metadata from disk"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    self.active_backups = {
                        bid: BackupMetadata.from_dict(meta) 
                        for bid, meta in data.items()
                    }
            except Exception as e:
                logger.warning(f"Failed to load backup metadata: {e}")
                self.active_backups = {}
    
    def _save_metadata(self) -> None:
        """Save backup metadata to disk"""
        try:
            metadata = {
                bid: backup.to_dict() 
                for bid, backup in self.active_backups.items()
            }
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save backup metadata: {e}")
    
    def create_backup(self, source_path: str, backup_id: Optional[str] = None) -> str:
        """
        Create atomic backup of database file
        
        Args:
            source_path: Path to source database
            backup_id: Optional custom backup ID
            
        Returns:
            str: Backup ID for reference
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Generate backup ID
        if not backup_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"migration_backup_{timestamp}"
        
        # Create backup file path
        source_name = Path(source_path).name
        backup_filename = f"{backup_id}_{source_name}.gz"
        backup_path = self.backup_dir / backup_filename
        
        try:
            logger.info(f"Creating backup: {source_path} -> {backup_path}")
            
            # Create compressed backup
            with open(source_path, 'rb') as src:
                with gzip.open(backup_path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
            
            # Create metadata
            metadata = BackupMetadata(backup_id, source_path, str(backup_path))
            
            # Verify backup integrity
            if self._verify_backup_integrity(metadata):
                metadata.backup_verified = True
                self.active_backups[backup_id] = metadata
                self._save_metadata()
                
                logger.info(f"Backup created successfully: {backup_id}")
                return backup_id
            else:
                # Remove failed backup
                if backup_path.exists():
                    backup_path.unlink()
                raise RuntimeError("Backup verification failed")
                
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            if backup_path.exists():
                backup_path.unlink()
            raise
    
    def _verify_backup_integrity(self, metadata: BackupMetadata) -> bool:
        """Verify backup file integrity"""
        try:
            backup_path = Path(metadata.backup_path)
            if not backup_path.exists():
                return False
            
            # Decompress and verify
            temp_restored = backup_path.parent / f"temp_verify_{metadata.backup_id}.db"
            
            try:
                with gzip.open(backup_path, 'rb') as src:
                    with open(temp_restored, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
                
                # Verify restored file hash matches original
                restored_hash = metadata._calculate_file_hash(str(temp_restored))
                integrity_check = restored_hash == metadata.source_hash
                
                if integrity_check:
                    # Additional SQLite integrity check
                    conn = sqlite3.connect(str(temp_restored))
                    cursor = conn.cursor()
                    cursor.execute("PRAGMA integrity_check")
                    integrity_result = cursor.fetchone()[0]
                    conn.close()
                    
                    integrity_check = integrity_result == "ok"
                
                return integrity_check
                
            finally:
                if temp_restored.exists():
                    temp_restored.unlink()
                    
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False
    
    def restore_backup(self, backup_id: str, target_path: Optional[str] = None) -> bool:
        """
        Restore database from backup
        
        Args:
            backup_id: ID of backup to restore
            target_path: Optional custom target path
            
        Returns:
            bool: True if restore successful
        """
        if backup_id not in self.active_backups:
            raise ValueError(f"Backup not found: {backup_id}")
        
        metadata = self.active_backups[backup_id]
        
        if not metadata.backup_verified:
            logger.warning(f"Restoring unverified backup: {backup_id}")
        
        # Determine target path
        restore_target = target_path or metadata.source_path
        
        try:
            logger.info(f"Restoring backup {backup_id} to {restore_target}")
            
            # Create backup of current file if it exists
            if os.path.exists(restore_target):
                current_backup_id = f"pre_restore_{backup_id}_{datetime.now().strftime('%H%M%S')}"
                self.create_backup(restore_target, current_backup_id)
                logger.info(f"Created safety backup: {current_backup_id}")
            
            # Restore from compressed backup
            backup_path = Path(metadata.backup_path)
            with gzip.open(backup_path, 'rb') as src:
                with open(restore_target, 'wb') as dst:
                    shutil.copyfileobj(src, dst)
            
            # Verify restored file
            restored_hash = metadata._calculate_file_hash(restore_target)
            if restored_hash != metadata.source_hash:
                logger.error("Restored file hash mismatch")
                return False
            
            logger.info(f"Backup restored successfully: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Backup restore failed: {e}")
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        return [backup.to_dict() for backup in self.active_backups.values()]
    
    def cleanup_old_backups(self, keep_count: int = 5) -> None:
        """
        Clean up old backups, keeping only the most recent ones
        
        Args:
            keep_count: Number of backups to keep
        """
        if len(self.active_backups) <= keep_count:
            return
        
        # Sort by creation time
        sorted_backups = sorted(
            self.active_backups.items(),
            key=lambda x: x[1].created_at,
            reverse=True
        )
        
        # Remove oldest backups
        for backup_id, metadata in sorted_backups[keep_count:]:
            try:
                backup_path = Path(metadata.backup_path)
                if backup_path.exists():
                    backup_path.unlink()
                
                del self.active_backups[backup_id]
                logger.info(f"Removed old backup: {backup_id}")
                
            except Exception as e:
                logger.error(f"Failed to remove backup {backup_id}: {e}")
        
        self._save_metadata()
    
    def get_backup_size(self, backup_id: str) -> int:
        """Get size of backup file in bytes"""
        if backup_id not in self.active_backups:
            return 0
        
        backup_path = Path(self.active_backups[backup_id].backup_path)
        return backup_path.stat().st_size if backup_path.exists() else 0
    
    def validate_backup_health(self) -> Dict[str, Any]:
        """
        Validate health of all backups
        
        Returns:
            Dict with validation results
        """
        results = {
            "total_backups": len(self.active_backups),
            "verified_backups": 0,
            "failed_backups": [],
            "total_size": 0
        }
        
        for backup_id, metadata in self.active_backups.items():
            backup_path = Path(metadata.backup_path)
            
            if not backup_path.exists():
                results["failed_backups"].append({
                    "backup_id": backup_id,
                    "error": "Backup file missing"
                })
                continue
            
            results["total_size"] += backup_path.stat().st_size
            
            if metadata.backup_verified:
                results["verified_backups"] += 1
            else:
                # Try to verify now
                if self._verify_backup_integrity(metadata):
                    metadata.backup_verified = True
                    results["verified_backups"] += 1
                else:
                    results["failed_backups"].append({
                        "backup_id": backup_id,
                        "error": "Verification failed"
                    })
        
        self._save_metadata()
        return results


class TransactionSafetyWrapper:
    """Wrapper for database operations with automatic backup and rollback"""
    
    def __init__(self, db_path: str, backup_system: AtomicBackupSystem):
        self.db_path = db_path
        self.backup_system = backup_system
        self.backup_id = None
    
    def __enter__(self):
        """Create backup before entering transaction"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_id = f"transaction_safety_{timestamp}"
        
        logger.info(f"Creating safety backup for transaction: {self.backup_id}")
        self.backup_system.create_backup(self.db_path, self.backup_id)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Handle transaction completion or failure"""
        if exc_type is not None:
            # Transaction failed - restore backup
            logger.error(f"Transaction failed, restoring backup: {self.backup_id}")
            self.backup_system.restore_backup(self.backup_id)
            return False
        else:
            # Transaction succeeded - keep backup for safety
            logger.info(f"Transaction completed successfully: {self.backup_id}")
            return True