"""
Greeum v3.0.0: Context Manager
Maintains and manages context sessions for coherent memory retrieval
"""

import json
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ContextSession:
    """Represents an active context session"""
    session_id: str
    active_nodes: List[str] = field(default_factory=list)
    activation_snapshot: Dict[str, float] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)


class ContextManager:
    """
    Manages context sessions and maintains coherent memory state
    """
    
    def __init__(self, network, spreading_activation, db_manager):
        """
        Initialize context manager
        
        Args:
            network: AssociationNetwork instance
            spreading_activation: SpreadingActivation instance
            db_manager: DatabaseManager instance
        """
        self.network = network
        self.spreading = spreading_activation
        self.db_manager = db_manager
        self.current_session: Optional[ContextSession] = None
        self.context_window = 10  # Number of recent activations to maintain
        self.session_timeout = 3600  # Session timeout in seconds (1 hour)
    
    def start_session(self, initial_context: Optional[List[str]] = None) -> str:
        """
        Start a new context session
        
        Args:
            initial_context: Optional initial node IDs to activate
            
        Returns:
            Session ID
        """
        session_id = f"ctx_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:18]}"
        
        self.current_session = ContextSession(session_id=session_id)
        
        # Initialize with context if provided
        if initial_context:
            activation = self.spreading.activate(initial_context)
            self.current_session.activation_snapshot = activation
            self.current_session.active_nodes = [
                node_id for node_id, level in activation.items()
                if level > self.spreading.activation_threshold
            ]
        
        # Save to database
        self._save_session()
        
        logger.info(f"Started context session: {session_id}")
        return session_id
    
    def update_context(self, new_nodes: List[str], 
                      preserve_ratio: float = 0.7) -> Dict[str, float]:
        """
        Update current context with new nodes
        
        Args:
            new_nodes: New nodes to add to context
            preserve_ratio: Ratio of previous context to preserve (0-1)
            
        Returns:
            Updated activation levels
        """
        if not self.current_session:
            self.start_session()
        
        # Decay previous activations
        prev_activation = {}
        for node_id, level in self.current_session.activation_snapshot.items():
            prev_activation[node_id] = level * preserve_ratio
        
        # Add new activations
        new_activation = self.spreading.activate(new_nodes)
        
        # Merge activations
        merged = prev_activation.copy()
        for node_id, level in new_activation.items():
            if node_id in merged:
                merged[node_id] = min(1.0, merged[node_id] + level * (1 - preserve_ratio))
            else:
                merged[node_id] = level
        
        # Update session
        self.current_session.activation_snapshot = merged
        self.current_session.active_nodes = [
            node_id for node_id, level in merged.items()
            if level > self.spreading.activation_threshold
        ]
        self.current_session.last_updated = datetime.now().isoformat()
        
        self._save_session()
        
        return merged
    
    def get_context_memories(self, top_k: int = 10) -> List[Dict]:
        """
        Get memories most relevant to current context
        
        Args:
            top_k: Number of memories to return
            
        Returns:
            List of memory blocks with relevance scores
        """
        if not self.current_session:
            return []
        
        memories = []
        
        for node_id, activation in self.current_session.activation_snapshot.items():
            if activation < self.spreading.activation_threshold:
                continue
            
            node = self.network.nodes.get(node_id)
            if not node or not node.memory_id:
                continue
            
            block = self.db_manager.get_block(node.memory_id)
            if block:
                block['relevance_score'] = activation
                block['node_id'] = node_id
                memories.append(block)
        
        # Sort by relevance
        memories.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return memories[:top_k]
    
    def find_related_context(self, query_nodes: List[str]) -> List[str]:
        """
        Find nodes related to query within current context
        
        Args:
            query_nodes: Query node IDs
            
        Returns:
            Related node IDs from current context
        """
        if not self.current_session:
            return []
        
        related = set()
        
        for query_node in query_nodes:
            if query_node not in self.network.nodes:
                continue
            
            # Find directly connected nodes in current context
            if query_node in self.network.adjacency_list:
                for neighbor in self.network.adjacency_list[query_node]:
                    if neighbor in self.current_session.active_nodes:
                        related.add(neighbor)
            
            # Check reverse connections
            for node_id in self.current_session.active_nodes:
                if node_id in self.network.adjacency_list:
                    if query_node in self.network.adjacency_list[node_id]:
                        related.add(node_id)
        
        return list(related)
    
    def maintain_coherence(self, threshold: float = 0.2):
        """
        Maintain context coherence by pruning weak activations
        
        Args:
            threshold: Minimum activation to maintain
        """
        if not self.current_session:
            return
        
        # Prune weak activations
        pruned = {}
        for node_id, level in self.current_session.activation_snapshot.items():
            if level >= threshold:
                pruned[node_id] = level
        
        self.current_session.activation_snapshot = pruned
        self.current_session.active_nodes = list(pruned.keys())
        
        self._save_session()
        
        logger.debug(f"Pruned context to {len(pruned)} active nodes")
    
    def switch_context(self, session_id: str) -> bool:
        """
        Switch to a different context session
        
        Args:
            session_id: Session ID to switch to
            
        Returns:
            True if successful
        """
        session = self._load_session(session_id)
        if session:
            self.current_session = session
            logger.info(f"Switched to context session: {session_id}")
            return True
        return False
    
    def merge_contexts(self, session_ids: List[str]) -> str:
        """
        Merge multiple context sessions
        
        Args:
            session_ids: Session IDs to merge
            
        Returns:
            New merged session ID
        """
        merged_activation = {}
        merged_nodes = set()
        
        for session_id in session_ids:
            session = self._load_session(session_id)
            if not session:
                continue
            
            # Merge activations (average)
            for node_id, level in session.activation_snapshot.items():
                if node_id not in merged_activation:
                    merged_activation[node_id] = 0
                merged_activation[node_id] += level / len(session_ids)
            
            merged_nodes.update(session.active_nodes)
        
        # Create new session with merged context
        new_session_id = self.start_session()
        self.current_session.activation_snapshot = merged_activation
        self.current_session.active_nodes = list(merged_nodes)
        self.current_session.metadata = {
            'merged_from': session_ids,
            'merge_time': datetime.now().isoformat()
        }
        
        self._save_session()
        
        logger.info(f"Merged {len(session_ids)} sessions into {new_session_id}")
        return new_session_id
    
    def get_context_summary(self) -> Dict:
        """
        Get summary of current context
        
        Returns:
            Context summary dictionary
        """
        if not self.current_session:
            return {'status': 'no_active_session'}
        
        # Analyze node types in context
        node_types = {}
        for node_id in self.current_session.active_nodes:
            node = self.network.nodes.get(node_id)
            if node:
                node_types[node.node_type] = node_types.get(node.node_type, 0) + 1
        
        # Find strongest activations
        top_nodes = sorted(
            self.current_session.activation_snapshot.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'session_id': self.current_session.session_id,
            'active_nodes': len(self.current_session.active_nodes),
            'total_activation': sum(self.current_session.activation_snapshot.values()),
            'average_activation': (
                sum(self.current_session.activation_snapshot.values()) / 
                len(self.current_session.activation_snapshot)
                if self.current_session.activation_snapshot else 0
            ),
            'node_types': node_types,
            'top_nodes': [
                {'node_id': node_id, 'activation': level}
                for node_id, level in top_nodes
            ],
            'created_at': self.current_session.created_at,
            'last_updated': self.current_session.last_updated
        }
    
    def cleanup_old_sessions(self, days: int = 7):
        """
        Clean up old context sessions
        
        Args:
            days: Sessions older than this many days will be deleted
        """
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            DELETE FROM context_sessions
            WHERE created_at < ?
        ''', (cutoff_str,))
        
        deleted = cursor.rowcount
        self.db_manager.conn.commit()
        
        logger.info(f"Cleaned up {deleted} old context sessions")
    
    def _save_session(self):
        """Save current session to database"""
        if not self.current_session:
            return
        
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO context_sessions
            (session_id, active_nodes, activation_snapshot, 
             created_at, last_updated, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            self.current_session.session_id,
            json.dumps(self.current_session.active_nodes),
            json.dumps(self.current_session.activation_snapshot),
            self.current_session.created_at,
            self.current_session.last_updated,
            json.dumps(self.current_session.metadata)
        ))
        self.db_manager.conn.commit()
    
    def _load_session(self, session_id: str) -> Optional[ContextSession]:
        """Load session from database"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            SELECT * FROM context_sessions
            WHERE session_id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return ContextSession(
            session_id=row['session_id'],
            active_nodes=json.loads(row['active_nodes']),
            activation_snapshot=json.loads(row['activation_snapshot']),
            created_at=row['created_at'],
            last_updated=row['last_updated'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )
    
    def export_context(self) -> Dict:
        """
        Export current context for external use
        
        Returns:
            Exportable context data
        """
        if not self.current_session:
            return {}
        
        return {
            'session_id': self.current_session.session_id,
            'activation': self.current_session.activation_snapshot,
            'active_nodes': self.current_session.active_nodes,
            'metadata': self.current_session.metadata,
            'timestamp': datetime.now().isoformat()
        }
    
    def import_context(self, context_data: Dict) -> str:
        """
        Import external context data
        
        Args:
            context_data: Context data to import
            
        Returns:
            New session ID
        """
        session_id = self.start_session()
        
        self.current_session.activation_snapshot = context_data.get('activation', {})
        self.current_session.active_nodes = context_data.get('active_nodes', [])
        self.current_session.metadata = context_data.get('metadata', {})
        self.current_session.metadata['imported_at'] = datetime.now().isoformat()
        
        self._save_session()
        
        return session_id