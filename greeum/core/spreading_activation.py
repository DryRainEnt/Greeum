"""
Greeum v3.0.0: Spreading Activation Algorithm
Implements cognitive spreading activation for memory retrieval
"""

import logging
import json
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import heapq

logger = logging.getLogger(__name__)

@dataclass
class ActivationRecord:
    """Record of node activation"""
    node_id: str
    activation_level: float
    source: str  # 'direct', 'spread', 'decay'
    timestamp: str


class SpreadingActivation:
    """
    Spreading activation algorithm for memory retrieval
    Based on cognitive psychology models
    """
    
    def __init__(self, network, db_manager):
        """
        Initialize spreading activation
        
        Args:
            network: AssociationNetwork instance
            db_manager: DatabaseManager instance
        """
        self.network = network
        self.db_manager = db_manager
        self.activation_threshold = 0.1  # Minimum activation to propagate
        self.decay_rate = 0.8  # Decay factor per hop
        self.max_iterations = 5  # Maximum spreading iterations
        self.session_id = None
    
    def activate(self, seed_nodes: List[str], 
                initial_activation: float = 1.0) -> Dict[str, float]:
        """
        Perform spreading activation from seed nodes
        
        Args:
            seed_nodes: Initial activated nodes
            initial_activation: Initial activation level
            
        Returns:
            Dictionary of node_id -> final activation level
        """
        # Initialize session with microseconds for uniqueness
        import uuid
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        self._create_session()
        
        # Activation levels
        activation = {}
        for node_id in seed_nodes:
            if node_id in self.network.nodes:
                activation[node_id] = initial_activation
                self._record_activation(node_id, initial_activation, 'direct')
        
        # Spreading iterations
        for iteration in range(self.max_iterations):
            new_activation = {}
            
            for node_id, level in activation.items():
                if level < self.activation_threshold:
                    continue
                
                # Get connected nodes
                if node_id in self.network.adjacency_list:
                    for neighbor_id in self.network.adjacency_list[node_id]:
                        # Find association strength
                        assoc = self._find_association(node_id, neighbor_id)
                        if not assoc:
                            continue
                        
                        # Calculate spread activation
                        spread = level * assoc.strength * self.decay_rate
                        
                        if neighbor_id not in new_activation:
                            new_activation[neighbor_id] = 0
                        new_activation[neighbor_id] += spread
            
            # Merge activations
            for node_id, spread_level in new_activation.items():
                if node_id not in activation:
                    activation[node_id] = 0
                activation[node_id] = min(1.0, activation[node_id] + spread_level)
                self._record_activation(node_id, activation[node_id], 'spread')
        
        # Update node activation levels
        self._update_node_activations(activation)
        
        # Save session snapshot
        self._save_session_snapshot(activation)
        
        return activation
    
    def _find_association(self, source_id: str, target_id: str):
        """Find association between two nodes"""
        for assoc in self.network.associations.values():
            if assoc.source_node_id == source_id and assoc.target_node_id == target_id:
                return assoc
        return None
    
    def _create_session(self):
        """Create new activation session"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            INSERT INTO context_sessions 
            (session_id, active_nodes, activation_snapshot, created_at, last_updated, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            self.session_id,
            '[]',
            '{}',
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            '{}'
        ))
        self.db_manager.conn.commit()
    
    def _record_activation(self, node_id: str, level: float, source: str):
        """Record activation in history"""
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            INSERT INTO activation_history
            (node_id, activation_level, trigger_type, trigger_source, timestamp, session_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            node_id,
            level,
            'spreading',
            source,
            datetime.now().isoformat(),
            self.session_id
        ))
        self.db_manager.conn.commit()
    
    def _update_node_activations(self, activation: Dict[str, float]):
        """Update node activation levels in database"""
        cursor = self.db_manager.conn.cursor()
        
        for node_id, level in activation.items():
            if node_id in self.network.nodes:
                self.network.nodes[node_id].activation_level = level
                self.network.nodes[node_id].last_activated = datetime.now().isoformat()
                
                cursor.execute('''
                    UPDATE memory_nodes
                    SET activation_level = ?, last_activated = ?
                    WHERE node_id = ?
                ''', (level, datetime.now().isoformat(), node_id))
        
        self.db_manager.conn.commit()
    
    def _save_session_snapshot(self, activation: Dict[str, float]):
        """Save session activation snapshot"""
        active_nodes = [node_id for node_id, level in activation.items() 
                       if level >= self.activation_threshold]
        
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            UPDATE context_sessions
            SET active_nodes = ?, activation_snapshot = ?, last_updated = ?
            WHERE session_id = ?
        ''', (
            json.dumps(active_nodes),
            json.dumps(activation),
            datetime.now().isoformat(),
            self.session_id
        ))
        self.db_manager.conn.commit()
    
    def get_activated_memories(self, activation: Dict[str, float],
                              threshold: float = 0.3) -> List[Dict]:
        """
        Get memory blocks for activated nodes
        
        Args:
            activation: Activation levels from spreading
            threshold: Minimum activation to include
            
        Returns:
            List of memory blocks with activation info
        """
        memories = []
        
        for node_id, level in activation.items():
            if level < threshold:
                continue
            
            node = self.network.nodes.get(node_id)
            if not node or not node.memory_id:
                continue
            
            # Get memory block
            block = self.db_manager.get_block(node.memory_id)
            if block:
                block['activation_level'] = level
                block['node_id'] = node_id
                memories.append(block)
        
        # Sort by activation level
        memories.sort(key=lambda x: x['activation_level'], reverse=True)
        
        return memories
    
    def find_associations_by_pattern(self, pattern: str) -> List[str]:
        """
        Find nodes matching a pattern
        
        Args:
            pattern: Search pattern
            
        Returns:
            List of matching node IDs
        """
        matching_nodes = []
        pattern_lower = pattern.lower()
        
        for node_id, node in self.network.nodes.items():
            if pattern_lower in node.content.lower():
                matching_nodes.append(node_id)
        
        return matching_nodes
    
    def trace_activation_path(self, start_node: str, 
                             end_node: str) -> Optional[List[Tuple[str, float]]]:
        """
        Trace activation path between nodes
        
        Args:
            start_node: Starting node ID
            end_node: Target node ID
            
        Returns:
            Path with activation levels, or None
        """
        # Use Dijkstra's algorithm with activation as weight
        if start_node not in self.network.nodes or end_node not in self.network.nodes:
            return None
        
        # Priority queue: (negative_activation, node_id, path)
        pq = [(-1.0, start_node, [(start_node, 1.0)])]
        visited = set()
        
        while pq:
            neg_activation, current, path = heapq.heappop(pq)
            activation = -neg_activation
            
            if current == end_node:
                return path
            
            if current in visited:
                continue
            visited.add(current)
            
            # Check neighbors
            if current in self.network.adjacency_list:
                for neighbor in self.network.adjacency_list[current]:
                    if neighbor in visited:
                        continue
                    
                    assoc = self._find_association(current, neighbor)
                    if assoc:
                        new_activation = activation * assoc.strength * self.decay_rate
                        if new_activation >= self.activation_threshold:
                            new_path = path + [(neighbor, new_activation)]
                            heapq.heappush(pq, (-new_activation, neighbor, new_path))
        
        return None
    
    def get_activation_history(self, node_id: str, limit: int = 10) -> List[Dict]:
        """
        Get activation history for a node
        
        Args:
            node_id: Node ID
            limit: Maximum records to return
            
        Returns:
            List of activation records
        """
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            SELECT * FROM activation_history
            WHERE node_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (node_id, limit))
        
        history = []
        for row in cursor.fetchall():
            history.append(dict(row))
        
        return history
    
    def reset_activations(self):
        """Reset all node activations to zero"""
        cursor = self.db_manager.conn.cursor()
        
        # Reset in memory
        for node in self.network.nodes.values():
            node.activation_level = 0.0
        
        # Reset in database
        cursor.execute('UPDATE memory_nodes SET activation_level = 0.0')
        self.db_manager.conn.commit()
        
        logger.info("Reset all node activations")
    
    def adaptive_spread(self, seed_nodes: List[str], 
                       context_weights: Dict[str, float] = None) -> Dict[str, float]:
        """
        Context-aware spreading activation
        
        Args:
            seed_nodes: Initial nodes
            context_weights: Optional weights for different association types
            
        Returns:
            Activation levels
        """
        if not context_weights:
            context_weights = {
                'semantic': 1.0,
                'temporal': 0.8,
                'causal': 0.9,
                'entity': 0.7
            }
        
        activation = {}
        for node_id in seed_nodes:
            if node_id in self.network.nodes:
                activation[node_id] = 1.0
        
        for iteration in range(self.max_iterations):
            new_activation = {}
            
            for node_id, level in activation.items():
                if level < self.activation_threshold:
                    continue
                
                if node_id in self.network.adjacency_list:
                    for neighbor_id in self.network.adjacency_list[node_id]:
                        assoc = self._find_association(node_id, neighbor_id)
                        if not assoc:
                            continue
                        
                        # Apply context weight
                        weight = context_weights.get(assoc.association_type, 0.5)
                        spread = level * assoc.strength * weight * self.decay_rate
                        
                        if neighbor_id not in new_activation:
                            new_activation[neighbor_id] = 0
                        new_activation[neighbor_id] += spread
            
            # Merge with normalization
            for node_id, spread_level in new_activation.items():
                if node_id not in activation:
                    activation[node_id] = 0
                # Sigmoid normalization to keep values in [0, 1]
                combined = activation[node_id] + spread_level
                activation[node_id] = combined / (1 + abs(combined))
        
        return activation