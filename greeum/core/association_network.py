"""
Greeum v3.0.0: Association Network Core
Memory association and spreading activation system
"""

import uuid
import json
import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class MemoryNode:
    """Memory node in the association network"""
    node_id: str
    memory_id: Optional[int]
    node_type: str  # 'memory', 'concept', 'entity', 'event'
    content: str
    embedding: Optional[List[float]] = None
    activation_level: float = 0.0
    last_activated: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class Association:
    """Association between memory nodes"""
    association_id: str
    source_node_id: str
    target_node_id: str
    association_type: str  # 'semantic', 'temporal', 'causal', 'entity'
    strength: float = 0.5  # 0.0 to 1.0
    weight: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activated: Optional[str] = None
    activation_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class AssociationNetwork:
    """
    Core association network for v3.0.0
    Manages memory nodes and their associations
    """
    
    def __init__(self, db_manager):
        """
        Initialize association network
        
        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager
        self.nodes: Dict[str, MemoryNode] = {}
        self.associations: Dict[str, Association] = {}
        self.adjacency_list: Dict[str, Set[str]] = {}
        self._load_network()
    
    def _load_network(self):
        """Load existing network from database"""
        try:
            cursor = self.db_manager.conn.cursor()
            
            # Load memory nodes
            cursor.execute("SELECT * FROM memory_nodes")
            for row in cursor.fetchall():
                node = MemoryNode(
                    node_id=row['node_id'],
                    memory_id=row['memory_id'],
                    node_type=row['node_type'],
                    content=row['content'],
                    embedding=json.loads(row['embedding']) if row['embedding'] else None,
                    activation_level=row['activation_level'],
                    last_activated=row['last_activated'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {},
                    created_at=row['created_at']
                )
                self.nodes[node.node_id] = node
            
            # Load associations
            cursor.execute("SELECT * FROM associations")
            for row in cursor.fetchall():
                assoc = Association(
                    association_id=row['association_id'],
                    source_node_id=row['source_node_id'],
                    target_node_id=row['target_node_id'],
                    association_type=row['association_type'],
                    strength=row['strength'],
                    weight=row['weight'],
                    created_at=row['created_at'],
                    last_activated=row['last_activated'],
                    activation_count=row['activation_count'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
                self.associations[assoc.association_id] = assoc
                
                # Build adjacency list
                if assoc.source_node_id not in self.adjacency_list:
                    self.adjacency_list[assoc.source_node_id] = set()
                self.adjacency_list[assoc.source_node_id].add(assoc.target_node_id)
            
            logger.info(f"Loaded {len(self.nodes)} nodes and {len(self.associations)} associations")
            
        except Exception as e:
            logger.debug(f"Network loading (expected on first run): {e}")
    
    def create_node(self, content: str, node_type: str = 'memory', 
                   memory_id: Optional[int] = None,
                   embedding: Optional[List[float]] = None) -> MemoryNode:
        """
        Create a new memory node
        
        Args:
            content: Node content
            node_type: Type of node
            memory_id: Associated memory block ID
            embedding: Optional embedding vector
            
        Returns:
            Created MemoryNode
        """
        node_id = f"node_{uuid.uuid4().hex[:12]}"
        node = MemoryNode(
            node_id=node_id,
            memory_id=memory_id,
            node_type=node_type,
            content=content,
            embedding=embedding
        )
        
        # Save to database
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            INSERT INTO memory_nodes 
            (node_id, memory_id, node_type, content, embedding, 
             activation_level, last_activated, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            node.node_id,
            node.memory_id,
            node.node_type,
            node.content,
            json.dumps(node.embedding) if node.embedding else None,
            node.activation_level,
            node.last_activated,
            json.dumps(node.metadata),
            node.created_at
        ))
        self.db_manager.conn.commit()
        
        # Add to memory
        self.nodes[node_id] = node
        logger.debug(f"Created node: {node_id} ({node_type})")
        
        return node
    
    def create_association(self, source_node_id: str, target_node_id: str,
                          association_type: str = 'semantic',
                          strength: float = 0.5) -> Association:
        """
        Create association between nodes
        
        Args:
            source_node_id: Source node ID
            target_node_id: Target node ID
            association_type: Type of association
            strength: Initial strength (0.0 to 1.0)
            
        Returns:
            Created Association
        """
        # Check nodes exist
        if source_node_id not in self.nodes or target_node_id not in self.nodes:
            raise ValueError("Source or target node not found")
        
        association_id = f"assoc_{uuid.uuid4().hex[:12]}"
        assoc = Association(
            association_id=association_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            association_type=association_type,
            strength=strength
        )
        
        # Save to database
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            INSERT INTO associations
            (association_id, source_node_id, target_node_id, association_type,
             strength, weight, created_at, last_activated, activation_count, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            assoc.association_id,
            assoc.source_node_id,
            assoc.target_node_id,
            assoc.association_type,
            assoc.strength,
            assoc.weight,
            assoc.created_at,
            assoc.last_activated,
            assoc.activation_count,
            json.dumps(assoc.metadata)
        ))
        self.db_manager.conn.commit()
        
        # Update in-memory structures
        self.associations[association_id] = assoc
        if source_node_id not in self.adjacency_list:
            self.adjacency_list[source_node_id] = set()
        self.adjacency_list[source_node_id].add(target_node_id)
        
        logger.debug(f"Created association: {source_node_id} -> {target_node_id} ({association_type})")
        
        return assoc
    
    def get_node_associations(self, node_id: str) -> List[Association]:
        """
        Get all associations for a node
        
        Args:
            node_id: Node ID
            
        Returns:
            List of associations
        """
        associations = []
        for assoc in self.associations.values():
            if assoc.source_node_id == node_id or assoc.target_node_id == node_id:
                associations.append(assoc)
        return associations
    
    def find_path(self, source_id: str, target_id: str, 
                 max_depth: int = 5) -> Optional[List[str]]:
        """
        Find path between two nodes using BFS
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            max_depth: Maximum search depth
            
        Returns:
            Path as list of node IDs, or None if no path exists
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return None
        
        if source_id == target_id:
            return [source_id]
        
        # BFS
        from collections import deque
        queue = deque([(source_id, [source_id])])
        visited = {source_id}
        depth = 0
        
        while queue and depth < max_depth:
            level_size = len(queue)
            for _ in range(level_size):
                current, path = queue.popleft()
                
                if current in self.adjacency_list:
                    for neighbor in self.adjacency_list[current]:
                        if neighbor == target_id:
                            return path + [neighbor]
                        
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append((neighbor, path + [neighbor]))
            depth += 1
        
        return None
    
    def strengthen_association(self, association_id: str, delta: float = 0.1):
        """
        Strengthen an association
        
        Args:
            association_id: Association ID
            delta: Strength increase (clamped to [0, 1])
        """
        if association_id not in self.associations:
            return
        
        assoc = self.associations[association_id]
        assoc.strength = min(1.0, assoc.strength + delta)
        assoc.activation_count += 1
        assoc.last_activated = datetime.now().isoformat()
        
        # Update database
        cursor = self.db_manager.conn.cursor()
        cursor.execute('''
            UPDATE associations 
            SET strength = ?, activation_count = ?, last_activated = ?
            WHERE association_id = ?
        ''', (assoc.strength, assoc.activation_count, assoc.last_activated, association_id))
        self.db_manager.conn.commit()
    
    def decay_associations(self, decay_rate: float = 0.01):
        """
        Apply decay to all associations
        
        Args:
            decay_rate: Rate of decay
        """
        cursor = self.db_manager.conn.cursor()
        
        for assoc in self.associations.values():
            # Don't decay below minimum threshold
            assoc.strength = max(0.1, assoc.strength - decay_rate)
        
        # Batch update
        cursor.execute('''
            UPDATE associations 
            SET strength = MAX(0.1, strength - ?)
        ''', (decay_rate,))
        self.db_manager.conn.commit()
        
        logger.debug(f"Applied decay rate {decay_rate} to all associations")
    
    def get_network_stats(self) -> Dict[str, Any]:
        """
        Get network statistics
        
        Returns:
            Dictionary with network stats
        """
        total_strength = sum(a.strength for a in self.associations.values())
        avg_strength = total_strength / len(self.associations) if self.associations else 0
        
        node_degrees = {}
        for node_id in self.nodes:
            degree = len(self.adjacency_list.get(node_id, []))
            node_degrees[node_id] = degree
        
        return {
            'total_nodes': len(self.nodes),
            'total_associations': len(self.associations),
            'average_strength': avg_strength,
            'max_degree': max(node_degrees.values()) if node_degrees else 0,
            'isolated_nodes': sum(1 for d in node_degrees.values() if d == 0),
            'node_types': self._count_node_types()
        }
    
    def _count_node_types(self) -> Dict[str, int]:
        """Count nodes by type"""
        type_counts = {}
        for node in self.nodes.values():
            type_counts[node.node_type] = type_counts.get(node.node_type, 0) + 1
        return type_counts