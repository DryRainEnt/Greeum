"""
Greeum v3.0.0: Engram - AI-Native Memory Structure
Engram (기억흔적): The physical trace of memory in the brain
"""

import uuid
import json
import sqlite3
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class Engram:
    """
    Engram: AI-native memory trace
    The fundamental unit of memory in Greeum v3.0.0
    """
    engram_id: str
    timestamp: str
    
    # Primary Actants (WHO-WHAT-WHOM)
    subject: Optional[str] = None
    action: Optional[str] = None
    object: Optional[str] = None
    
    # Extended Actants
    sender: Optional[str] = None      # Who initiated
    receiver: Optional[str] = None    # Who benefits
    context: Optional[str] = None     # Where/When/Why
    
    # AI Cognition Layer
    intent: Optional[str] = None      # Understood purpose
    emotion: Optional[str] = None     # Detected feeling
    importance: float = 0.5           # Judged significance
    
    # Associative Network
    causes: List[str] = field(default_factory=list)   # What led to this
    effects: List[str] = field(default_factory=list)  # What this leads to
    related: List[str] = field(default_factory=list)  # Associated engrams
    
    # Preservation
    original_text: str = ""           # Exact input preserved
    
    # Meta-cognition
    ai_model: str = "claude"          # Which AI processed this
    confidence: float = 0.5           # How certain the AI is
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __str__(self):
        """Human-readable representation"""
        actant = f"{self.subject or '?'} {self.action or '?'} {self.object or '?'}"
        return f"Engram({self.engram_id[:8]}): {actant}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return asdict(self)


class EngramCore:
    """
    Core system for Engram management
    Handles storage, retrieval, and association of memory traces
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize Engram core
        
        Args:
            db_path: Path to engram database (default: data/engrams.db)
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            # Default engram database
            self.db_path = Path("data") / "engrams.db"
            self.db_path.parent.mkdir(exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        
        logger.info(f"Engram Core initialized: {self.db_path}")
    
    def _create_tables(self):
        """Create engram storage tables"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS engrams (
                engram_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                
                -- Actant Structure
                subject TEXT,
                action TEXT,
                object TEXT,
                sender TEXT,
                receiver TEXT,
                context TEXT,
                
                -- AI Cognition
                intent TEXT,
                emotion TEXT,
                importance REAL DEFAULT 0.5,
                
                -- Associations (JSON arrays)
                causes TEXT DEFAULT '[]',
                effects TEXT DEFAULT '[]',
                related TEXT DEFAULT '[]',
                
                -- Preservation
                original_text TEXT NOT NULL,
                
                -- Meta-cognition
                ai_model TEXT DEFAULT 'claude',
                confidence REAL DEFAULT 0.5,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Indexes for efficient retrieval
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_engram_timestamp ON engrams(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_engram_subject ON engrams(subject)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_engram_action ON engrams(action)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_engram_importance ON engrams(importance DESC)')
        
        # Association tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS engram_associations (
                association_id TEXT PRIMARY KEY,
                source_engram TEXT NOT NULL,
                target_engram TEXT NOT NULL,
                association_type TEXT,  -- 'causal', 'temporal', 'semantic'
                strength REAL DEFAULT 0.5,
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_engram) REFERENCES engrams(engram_id),
                FOREIGN KEY (target_engram) REFERENCES engrams(engram_id)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_assoc_source ON engram_associations(source_engram)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_assoc_target ON engram_associations(target_engram)')
        
        self.conn.commit()
    
    def create_engram(self, text: str, **kwargs) -> Engram:
        """
        Create a new engram (typically called by AI)
        
        Args:
            text: Original text to encode
            **kwargs: Additional fields for the engram
            
        Returns:
            Created Engram object
        """
        engram_id = kwargs.get('engram_id', f"eng_{uuid.uuid4().hex[:12]}")
        
        engram = Engram(
            engram_id=engram_id,
            timestamp=datetime.now().isoformat(),
            original_text=text,
            **{k: v for k, v in kwargs.items() if k != 'engram_id'}
        )
        
        return engram
    
    def store(self, engram: Engram) -> str:
        """
        Store an engram in the database
        
        Args:
            engram: Engram object to store
            
        Returns:
            engram_id of stored engram
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO engrams (
                engram_id, timestamp, subject, action, object,
                sender, receiver, context, intent, emotion, importance,
                causes, effects, related, original_text,
                ai_model, confidence, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            engram.engram_id,
            engram.timestamp,
            engram.subject,
            engram.action,
            engram.object,
            engram.sender,
            engram.receiver,
            engram.context,
            engram.intent,
            engram.emotion,
            engram.importance,
            json.dumps(engram.causes),
            json.dumps(engram.effects),
            json.dumps(engram.related),
            engram.original_text,
            engram.ai_model,
            engram.confidence,
            engram.created_at
        ))
        
        self.conn.commit()
        logger.debug(f"Stored engram: {engram}")
        
        return engram.engram_id
    
    def recall(self, engram_id: str) -> Optional[Engram]:
        """
        Recall a specific engram
        
        Args:
            engram_id: ID of engram to recall
            
        Returns:
            Engram object or None
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM engrams WHERE engram_id = ?', (engram_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return self._row_to_engram(row)
    
    def search(self, 
              subject: Optional[str] = None,
              action: Optional[str] = None,
              object: Optional[str] = None,
              min_importance: Optional[float] = None,
              limit: int = 20) -> List[Engram]:
        """
        Search engrams by various criteria
        
        Returns:
            List of matching engrams
        """
        cursor = self.conn.cursor()
        
        conditions = []
        params = []
        
        if subject:
            conditions.append("subject = ?")
            params.append(subject)
        if action:
            conditions.append("action = ?")
            params.append(action)
        if object:
            conditions.append("object = ?")
            params.append(object)
        if min_importance is not None:
            conditions.append("importance >= ?")
            params.append(min_importance)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        query = f'''
            SELECT * FROM engrams 
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        '''
        params.append(limit)
        
        cursor.execute(query, params)
        
        return [self._row_to_engram(row) for row in cursor.fetchall()]
    
    def find_associations(self, engram_id: str) -> Dict[str, List[Engram]]:
        """
        Find all associated engrams
        
        Args:
            engram_id: Source engram ID
            
        Returns:
            Dictionary with 'causes', 'effects', and 'related' engrams
        """
        engram = self.recall(engram_id)
        if not engram:
            return {'causes': [], 'effects': [], 'related': []}
        
        result = {
            'causes': [],
            'effects': [],
            'related': []
        }
        
        # Recall cause engrams
        for cause_id in engram.causes:
            if cause_engram := self.recall(cause_id):
                result['causes'].append(cause_engram)
        
        # Recall effect engrams
        for effect_id in engram.effects:
            if effect_engram := self.recall(effect_id):
                result['effects'].append(effect_engram)
        
        # Recall related engrams
        for related_id in engram.related:
            if related_engram := self.recall(related_id):
                result['related'].append(related_engram)
        
        return result
    
    def create_association(self, source_id: str, target_id: str, 
                         association_type: str = 'related', 
                         strength: float = 0.5):
        """
        Create an association between two engrams
        
        Args:
            source_id: Source engram ID
            target_id: Target engram ID
            association_type: Type of association
            strength: Strength of association (0-1)
        """
        cursor = self.conn.cursor()
        
        association_id = f"assoc_{uuid.uuid4().hex[:12]}"
        
        cursor.execute('''
            INSERT INTO engram_associations
            (association_id, source_engram, target_engram, 
             association_type, strength, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            association_id,
            source_id,
            target_id,
            association_type,
            strength,
            datetime.now().isoformat()
        ))
        
        # Also update the engram's relation lists
        source = self.recall(source_id)
        if source and association_type == 'causal':
            if target_id not in source.effects:
                source.effects.append(target_id)
                self.store(source)
        
        self.conn.commit()
    
    def get_recent(self, limit: int = 10) -> List[Engram]:
        """Get most recent engrams"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM engrams
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        return [self._row_to_engram(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engram statistics"""
        cursor = self.conn.cursor()
        
        # Total count
        cursor.execute('SELECT COUNT(*) FROM engrams')
        total = cursor.fetchone()[0]
        
        # Average importance
        cursor.execute('SELECT AVG(importance) FROM engrams')
        avg_importance = cursor.fetchone()[0] or 0
        
        # Engrams with associations
        cursor.execute('''
            SELECT COUNT(*) FROM engrams
            WHERE causes != '[]' OR effects != '[]' OR related != '[]'
        ''')
        with_associations = cursor.fetchone()[0]
        
        # Top subjects
        cursor.execute('''
            SELECT subject, COUNT(*) as count 
            FROM engrams 
            WHERE subject IS NOT NULL
            GROUP BY subject 
            ORDER BY count DESC
            LIMIT 5
        ''')
        top_subjects = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            'total_engrams': total,
            'average_importance': avg_importance,
            'engrams_with_associations': with_associations,
            'association_percentage': (with_associations / total * 100) if total > 0 else 0,
            'top_subjects': top_subjects
        }
    
    def _row_to_engram(self, row) -> Engram:
        """Convert database row to Engram object"""
        return Engram(
            engram_id=row['engram_id'],
            timestamp=row['timestamp'],
            subject=row['subject'],
            action=row['action'],
            object=row['object'],
            sender=row['sender'],
            receiver=row['receiver'],
            context=row['context'],
            intent=row['intent'],
            emotion=row['emotion'],
            importance=row['importance'],
            causes=json.loads(row['causes']) if row['causes'] else [],
            effects=json.loads(row['effects']) if row['effects'] else [],
            related=json.loads(row['related']) if row['related'] else [],
            original_text=row['original_text'],
            ai_model=row['ai_model'],
            confidence=row['confidence'],
            created_at=row['created_at']
        )
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info(f"Engram Core closed: {self.db_path}")