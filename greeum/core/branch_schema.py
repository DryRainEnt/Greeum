"""
Branch/DFS Schema for Greeum v3.0.0+
Implements tree-based memory structure with local-first DFS search
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

@dataclass
class BranchBlock:
    """Branch-aware memory block with tree structure"""
    # Core identifiers
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    block_index: int = 0
    
    # Tree structure
    root: Optional[str] = None  # Root branch ID
    before: Optional[str] = None  # Parent block ID
    after: List[str] = field(default_factory=list)  # Child block IDs
    
    # Content and metadata
    content: str = ""
    context: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    tags: Dict[str, Any] = field(default_factory=dict)
    embedding: List[float] = field(default_factory=list)
    importance: float = 0.5
    
    # Stats for DFS optimization
    stats: Dict[str, Any] = field(default_factory=lambda: {
        "visit_count": 0,
        "last_seen_at": 0,
        "depth": 0,
        "branch_size": 0
    })
    
    # Timestamps
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.now().timestamp())
    
    # Cross-references for non-tree links
    xref: List[str] = field(default_factory=list)
    
    # Hash for integrity
    hash: Optional[str] = None
    prev_hash: Optional[str] = None


@dataclass 
class BranchMeta:
    """Metadata for branch management"""
    root: str  # Branch root ID
    title: str = "Untitled Branch"
    heads: Dict[str, str] = field(default_factory=lambda: {
        "A": None,
        "B": None, 
        "C": None
    })  # STM slot heads
    size: int = 0  # Number of nodes in branch
    depth: int = 0  # Max depth of branch
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    last_modified: float = field(default_factory=lambda: datetime.now().timestamp())
    
    # Merge tracking
    merge_history: List[Dict[str, Any]] = field(default_factory=list)
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    
    # Stats
    total_visits: int = 0
    total_searches: int = 0
    local_hits: int = 0


@dataclass
class SearchMeta:
    """Metadata for search operations"""
    search_type: str  # "local", "jump", "global"
    slot: Optional[str] = None  # STM slot used
    root: Optional[str] = None  # Branch root
    depth_used: int = 0  # Actual DFS depth explored
    hops: int = 0  # Number of nodes visited
    local_used: bool = False  # Whether local DFS was used
    fallback_used: bool = False  # Whether global fallback was triggered
    query_time_ms: float = 0.0
    result_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "search_type": self.search_type,
            "slot": self.slot,
            "root": self.root,
            "depth_used": self.depth_used,
            "hops": self.hops,
            "local_used": self.local_used,
            "fallback_used": self.fallback_used,
            "query_time_ms": self.query_time_ms,
            "result_count": self.result_count
        }


@dataclass
class MergeProposal:
    """Soft merge proposal between branches"""
    source_head: str
    target_head: str
    root: str  # Must be same root for auto-merge
    merge_score: float = 0.0
    ema_score: float = 0.0  # Exponential moving average
    
    # Scoring components
    cosine_similarity: float = 0.0
    centroid_similarity: float = 0.0
    tag_jaccard: float = 0.0
    temporal_proximity: float = 0.0
    divergence: float = 0.0
    
    # Merge metadata
    proposed_at: float = field(default_factory=lambda: datetime.now().timestamp())
    checkpoint_id: Optional[str] = None
    reversible: bool = True
    cooldown_until: Optional[float] = None  # 30min cooldown
    
    # History
    evaluation_count: int = 0
    acceptance_history: List[bool] = field(default_factory=list)
    
    def should_merge(self, threshold: float = 0.7) -> bool:
        """Check if merge should proceed based on EMA score"""
        return self.ema_score >= threshold and not self.is_cooling_down()
    
    def is_cooling_down(self) -> bool:
        """Check if merge is in cooldown period"""
        if self.cooldown_until is None:
            return False
        return datetime.now().timestamp() < self.cooldown_until


class BranchSchemaSQL:
    """SQL schema definitions for branch tables"""
    
    @staticmethod
    def get_migration_sql() -> List[str]:
        """Get SQL statements for schema migration"""
        return [
            # Add branch columns to blocks table
            """
            ALTER TABLE blocks ADD COLUMN root TEXT;
            """,
            """
            ALTER TABLE blocks ADD COLUMN before TEXT;
            """,
            """
            ALTER TABLE blocks ADD COLUMN after TEXT DEFAULT '[]';
            """,
            """
            ALTER TABLE blocks ADD COLUMN xref TEXT DEFAULT '[]';
            """,
            """
            ALTER TABLE blocks ADD COLUMN branch_depth INTEGER DEFAULT 0;
            """,
            """
            ALTER TABLE blocks ADD COLUMN visit_count INTEGER DEFAULT 0;
            """,
            """
            ALTER TABLE blocks ADD COLUMN last_seen_at REAL DEFAULT 0;
            """,
            """
            ALTER TABLE blocks ADD COLUMN slot TEXT;
            """,
            """
            ALTER TABLE blocks ADD COLUMN branch_similarity REAL DEFAULT 0;
            """,
            """
            ALTER TABLE blocks ADD COLUMN branch_created_at REAL DEFAULT 0;
            """,
            
            # Create branch_meta table
            """
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
            """,

            # Create merge_proposals table
            """
            CREATE TABLE IF NOT EXISTS merge_proposals (
                id TEXT PRIMARY KEY,
                source_head TEXT NOT NULL,
                target_head TEXT NOT NULL,
                root TEXT NOT NULL,
                merge_score REAL DEFAULT 0.0,
                ema_score REAL DEFAULT 0.0,
                cosine_similarity REAL DEFAULT 0.0,
                centroid_similarity REAL DEFAULT 0.0,
                tag_jaccard REAL DEFAULT 0.0,
                temporal_proximity REAL DEFAULT 0.0,
                divergence REAL DEFAULT 0.0,
                proposed_at REAL NOT NULL,
                checkpoint_id TEXT,
                reversible INTEGER DEFAULT 1,
                cooldown_until REAL,
                evaluation_count INTEGER DEFAULT 0,
                acceptance_history TEXT DEFAULT '[]',
                status TEXT DEFAULT 'pending'
            );
            """,
            
            # Create indexes for efficient DFS
            """
            CREATE INDEX IF NOT EXISTS idx_blocks_root ON blocks(root);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_blocks_before ON blocks(before);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_blocks_slot ON blocks(slot);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_blocks_created_at ON blocks(timestamp);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_merge_proposals_status ON merge_proposals(status);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_merge_proposals_root ON merge_proposals(root);
            """
        ]
    
    @staticmethod
    def check_migration_needed(cursor) -> bool:
        """Check if migration is needed"""
        try:
            # Check if branch columns exist
            cursor.execute("PRAGMA table_info(blocks)")
            columns = {row[1] for row in cursor.fetchall()}
            branch_columns = {
                'root',
                'before',
                'after',
                'xref',
                'slot',
                'branch_similarity',
                'branch_created_at'
            }

            if not branch_columns.issubset(columns):
                return True

            # Check if branch_meta table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='branch_meta'
            """)
            if not cursor.fetchone():
                return True

            return False
        except Exception:
            return True
