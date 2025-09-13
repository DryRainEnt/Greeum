"""
Greeum v2.5.3 AI-Powered Migration System

Revolutionary AI-powered database migration with comprehensive safety guarantees.
This system provides forced migration with AI parsing when legacy databases are detected.

Key Features:
- AI-powered actant parsing for legacy memory blocks
- 5-layer safety system with atomic backups
- Forced migration interface with compelling value proposition
- Comprehensive validation and emergency rollback
- Relationship discovery and causality inference

Usage:
    from greeum.core.migration import ForcedMigrationInterface
    
    interface = ForcedMigrationInterface("data/")
    success = interface.check_and_force_migration()
"""

from .schema_version import (
    SchemaVersionManager,
    SchemaVersion,
    MigrationVersionGuard
)

from .backup_system import (
    AtomicBackupSystem,
    BackupMetadata,
    TransactionSafetyWrapper
)

from .ai_parser import (
    AIActantParser,
    ActantParseResult,
    ParseConfidence,
    RelationshipExtractor
)

from .migration_interface import (
    ForcedMigrationInterface,
    MigrationResult,
    MigrationCLI
)

from .validation_rollback import (
    MigrationValidator,
    EmergencyRollbackManager,
    MigrationHealthMonitor,
    ValidationError,
    RollbackError
)

__all__ = [
    # Core migration interface
    'ForcedMigrationInterface',
    'MigrationResult',
    'MigrationCLI',
    
    # Schema management
    'SchemaVersionManager',
    'SchemaVersion',
    'MigrationVersionGuard',
    
    # Safety systems
    'AtomicBackupSystem',
    'BackupMetadata', 
    'TransactionSafetyWrapper',
    
    # AI parsing
    'AIActantParser',
    'ActantParseResult',
    'ParseConfidence',
    'RelationshipExtractor',
    
    # Validation and rollback
    'MigrationValidator',
    'EmergencyRollbackManager',
    'MigrationHealthMonitor',
    'ValidationError',
    'RollbackError'
]

# Version info - use main package version
try:
    from greeum import __version__
except ImportError:
    __version__ = "unknown"
__migration_version__ = SchemaVersion.V253_ACTANT