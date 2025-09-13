"""
Greeum v3.0.0: Neural Memory Network
A truly connected memory system, not just numbered blocks
"""

import time
import json
import sqlite3
import hashlib
import logging
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
import math

logger = logging.getLogger(__name__)

@dataclass
class MemoryNode:
    """The simplest memory unit"""
    node_id: str
    content: str
    timestamp: float
    activation: float = 0.0


class NeuralMemoryNetwork:
    """
    A memory system where memories form a network, not a list
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize Neural Memory Network"""
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Path("data") / "neural_memory.db"
            self.db_path.parent.mkdir(exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path))
        self._create_tables()
        
        # In-memory cache for fast activation spreading
        self.nodes: Dict[str, MemoryNode] = {}
        self.edges: Dict[Tuple[str, str], float] = {}
        self._load_network()
        
        # Activation parameters
        self.activation_decay = 0.5  # How much activation decays per hop
        self.activation_threshold = 0.1  # Minimum activation to propagate
        self.max_propagation_depth = 3  # How far activation spreads
        
        logger.info(f"Neural Memory Network initialized: {self.db_path}")
    
    def _create_tables(self):
        """Create simple network tables"""
        cursor = self.conn.cursor()
        
        # Nodes table - just the essentials
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nodes (
                node_id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                activation REAL DEFAULT 0.0
            )
        ''')
        
        # Connections table - the network structure
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS connections (
                from_node TEXT NOT NULL,
                to_node TEXT NOT NULL,
                weight REAL DEFAULT 0.5,
                created_by TEXT,  -- 'temporal', 'semantic', 'causal', 'user'
                created_at REAL,
                PRIMARY KEY (from_node, to_node),
                FOREIGN KEY (from_node) REFERENCES nodes(node_id),
                FOREIGN KEY (to_node) REFERENCES nodes(node_id)
            )
        ''')
        
        # Activation history for learning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activation_history (
                session_id TEXT,
                node_id TEXT,
                activation_level REAL,
                timestamp REAL,
                FOREIGN KEY (node_id) REFERENCES nodes(node_id)
            )
        ''')
        
        # Indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_timestamp ON nodes(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_connections_from ON connections(from_node)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_connections_to ON connections(to_node)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_connections_weight ON connections(weight)')
        
        self.conn.commit()
    
    def _load_network(self):
        """Load network into memory for fast access"""
        cursor = self.conn.cursor()
        
        # Load nodes
        cursor.execute('SELECT node_id, content, timestamp, activation FROM nodes')
        for row in cursor.fetchall():
            self.nodes[row[0]] = MemoryNode(
                node_id=row[0],
                content=row[1],
                timestamp=row[2],
                activation=row[3]
            )
        
        # Load edges
        cursor.execute('SELECT from_node, to_node, weight FROM connections')
        for row in cursor.fetchall():
            self.edges[(row[0], row[1])] = row[2]
        
        logger.debug(f"Loaded {len(self.nodes)} nodes and {len(self.edges)} connections")
    
    def add_memory(self, content: str) -> str:
        """
        Add a new memory and automatically connect it to related memories
        
        Args:
            content: The memory content
            
        Returns:
            node_id of the new memory
        """
        # Generate unique ID
        node_id = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:12]
        timestamp = time.time()
        
        # Create node
        node = MemoryNode(
            node_id=node_id,
            content=content,
            timestamp=timestamp,
            activation=1.0  # New memories start fully activated
        )
        
        # Save to database
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO nodes (node_id, content, timestamp, activation) VALUES (?, ?, ?, ?)',
            (node.node_id, node.content, node.timestamp, node.activation)
        )
        
        # Add to memory
        self.nodes[node_id] = node
        
        # Automatically create connections
        self._create_connections(node)
        
        # Spread activation through the network
        self._spread_activation(node_id)
        
        self.conn.commit()
        
        logger.info(f"Added memory node: {node_id[:8]}... with {len(self._get_connections(node_id))} connections")
        
        return node_id
    
    def _create_connections(self, new_node: MemoryNode):
        """
        Automatically create connections to related memories
        """
        cursor = self.conn.cursor()
        connections_created = 0
        
        for existing_id, existing_node in self.nodes.items():
            if existing_id == new_node.node_id:
                continue
            
            # Temporal connection (recent memories)
            time_diff = abs(new_node.timestamp - existing_node.timestamp)
            if time_diff < 3600:  # Within 1 hour
                weight = 0.3 * (1 - time_diff / 3600)  # Closer in time = stronger
                self._add_connection(new_node.node_id, existing_id, weight, 'temporal')
                connections_created += 1
            
            # Semantic connection (similar content)
            # For now, simple keyword overlap. In production, use AI similarity
            new_words = set(new_node.content.lower().split())
            existing_words = set(existing_node.content.lower().split())
            
            if new_words and existing_words:
                overlap = len(new_words & existing_words)
                if overlap > 0:
                    weight = min(0.8, overlap / min(len(new_words), len(existing_words)))
                    self._add_connection(new_node.node_id, existing_id, weight, 'semantic')
                    connections_created += 1
        
        logger.debug(f"Created {connections_created} connections for new node")
    
    def _add_connection(self, from_node: str, to_node: str, weight: float, created_by: str):
        """Add a connection between two nodes"""
        cursor = self.conn.cursor()
        
        # Add to database (bidirectional for now)
        cursor.execute('''
            INSERT OR REPLACE INTO connections 
            (from_node, to_node, weight, created_by, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (from_node, to_node, weight, created_by, time.time()))
        
        # Also add reverse connection with reduced weight
        cursor.execute('''
            INSERT OR REPLACE INTO connections 
            (from_node, to_node, weight, created_by, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (to_node, from_node, weight * 0.7, created_by, time.time()))
        
        # Add to memory
        self.edges[(from_node, to_node)] = weight
        self.edges[(to_node, from_node)] = weight * 0.7
    
    def _spread_activation(self, source_id: str, session_id: Optional[str] = None):
        """
        Spread activation through the network from a source node
        """
        if source_id not in self.nodes:
            return
        
        if not session_id:
            session_id = f"session_{int(time.time())}"
        
        # Reset all activations
        for node in self.nodes.values():
            node.activation = 0.0
        
        # Start with source fully activated
        self.nodes[source_id].activation = 1.0
        
        # Breadth-first activation spreading
        current_layer = [(source_id, 1.0)]
        visited = {source_id}
        
        for depth in range(self.max_propagation_depth):
            next_layer = []
            
            for node_id, activation_level in current_layer:
                # Get all connections from this node
                connections = self._get_connections(node_id)
                
                for target_id, weight in connections:
                    if target_id in visited:
                        continue
                    
                    # Calculate activation to spread
                    spread_activation = activation_level * weight * self.activation_decay
                    
                    if spread_activation > self.activation_threshold:
                        self.nodes[target_id].activation += spread_activation
                        next_layer.append((target_id, self.nodes[target_id].activation))
                        visited.add(target_id)
                        
                        # Log activation for learning
                        self._log_activation(session_id, target_id, self.nodes[target_id].activation)
            
            current_layer = next_layer
            
            if not current_layer:
                break
        
        # Update database with new activation levels
        cursor = self.conn.cursor()
        for node_id, node in self.nodes.items():
            cursor.execute(
                'UPDATE nodes SET activation = ? WHERE node_id = ?',
                (node.activation, node_id)
            )
        self.conn.commit()
    
    def _get_connections(self, node_id: str) -> List[Tuple[str, float]]:
        """Get all connections from a node"""
        connections = []
        for (from_id, to_id), weight in self.edges.items():
            if from_id == node_id:
                connections.append((to_id, weight))
        return connections
    
    def _log_activation(self, session_id: str, node_id: str, activation_level: float):
        """Log activation for learning patterns"""
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO activation_history (session_id, node_id, activation_level, timestamp) VALUES (?, ?, ?, ?)',
            (session_id, node_id, activation_level, time.time())
        )
    
    def recall(self, query: str, top_k: int = 5) -> List[Tuple[MemoryNode, float]]:
        """
        Recall memories related to a query
        
        Args:
            query: The query text
            top_k: Number of memories to return
            
        Returns:
            List of (MemoryNode, activation_level) tuples
        """
        # Create temporary node for query
        query_id = "query_temp"
        query_node = MemoryNode(query_id, query, time.time(), 1.0)
        
        # Temporarily add to network
        self.nodes[query_id] = query_node
        
        # Create temporary connections based on similarity
        for node_id, node in self.nodes.items():
            if node_id == query_id:
                continue
            
            # Simple keyword similarity (in production, use AI)
            query_words = set(query.lower().split())
            node_words = set(node.content.lower().split())
            
            if query_words and node_words:
                overlap = len(query_words & node_words)
                if overlap > 0:
                    weight = min(1.0, overlap / min(len(query_words), len(node_words)))
                    self.edges[(query_id, node_id)] = weight
        
        # Spread activation from query
        self._spread_activation(query_id)
        
        # Get activated nodes
        activated = [
            (node, node.activation) 
            for node_id, node in self.nodes.items() 
            if node_id != query_id and node.activation > 0
        ]
        
        # Sort by activation
        activated.sort(key=lambda x: x[1], reverse=True)
        
        # Clean up temporary node
        del self.nodes[query_id]
        self.edges = {k: v for k, v in self.edges.items() if query_id not in k}
        
        return activated[:top_k]
    
    def find_path(self, from_content: str, to_content: str) -> List[str]:
        """
        Find a path between two memories (useful for causal chains)
        
        Args:
            from_content: Starting memory content
            to_content: Target memory content
            
        Returns:
            List of node contents forming the path
        """
        # Find matching nodes
        from_node = None
        to_node = None
        
        for node_id, node in self.nodes.items():
            if from_content.lower() in node.content.lower():
                from_node = node_id
            if to_content.lower() in node.content.lower():
                to_node = node_id
        
        if not from_node or not to_node:
            return []
        
        # BFS to find path
        queue = [(from_node, [from_node])]
        visited = {from_node}
        
        while queue:
            current, path = queue.pop(0)
            
            if current == to_node:
                # Convert path to contents
                return [self.nodes[node_id].content for node_id in path]
            
            for target_id, weight in self._get_connections(current):
                if target_id not in visited:
                    visited.add(target_id)
                    queue.append((target_id, path + [target_id]))
        
        return []
    
    def strengthen_connection(self, from_id: str, to_id: str, delta: float = 0.1):
        """Strengthen a connection (learning)"""
        key = (from_id, to_id)
        if key in self.edges:
            self.edges[key] = min(1.0, self.edges[key] + delta)
            
            cursor = self.conn.cursor()
            cursor.execute(
                'UPDATE connections SET weight = ? WHERE from_node = ? AND to_node = ?',
                (self.edges[key], from_id, to_id)
            )
            self.conn.commit()
    
    def learn_from_coactivation(self):
        """
        Learn patterns from activation history
        Strengthen connections between frequently co-activated nodes
        """
        cursor = self.conn.cursor()
        
        # Find co-activated nodes
        cursor.execute('''
            SELECT a.node_id, b.node_id, COUNT(*) as coactivation_count
            FROM activation_history a
            JOIN activation_history b ON a.session_id = b.session_id
            WHERE a.node_id < b.node_id
            GROUP BY a.node_id, b.node_id
            HAVING coactivation_count > 2
        ''')
        
        for row in cursor.fetchall():
            node1, node2, count = row
            
            # Strengthen connection based on co-activation frequency
            strength_increase = min(0.3, count * 0.05)
            self.strengthen_connection(node1, node2, strength_increase)
            self.strengthen_connection(node2, node1, strength_increase * 0.7)
        
        logger.info("Learned from co-activation patterns")
    
    def get_network_stats(self) -> Dict:
        """Get network statistics"""
        cursor = self.conn.cursor()
        
        # Node degree distribution
        node_degrees = defaultdict(int)
        for node_id in self.nodes:
            node_degrees[node_id] = len(self._get_connections(node_id))
        
        # Find hubs (highly connected nodes)
        avg_degree = sum(node_degrees.values()) / len(node_degrees) if node_degrees else 0
        hubs = [node_id for node_id, degree in node_degrees.items() if degree > avg_degree * 2]
        
        # Most activated nodes in recent sessions
        cursor.execute('''
            SELECT node_id, AVG(activation_level) as avg_activation
            FROM activation_history
            WHERE timestamp > ?
            GROUP BY node_id
            ORDER BY avg_activation DESC
            LIMIT 5
        ''', (time.time() - 86400,))  # Last 24 hours
        
        hot_nodes = [(row[0], row[1]) for row in cursor.fetchall()]
        
        return {
            'total_nodes': len(self.nodes),
            'total_connections': len(self.edges),
            'average_degree': avg_degree,
            'hub_nodes': len(hubs),
            'hot_nodes': hot_nodes,
            'network_density': len(self.edges) / (len(self.nodes) * (len(self.nodes) - 1)) if len(self.nodes) > 1 else 0
        }
    
    def visualize_subgraph(self, center_id: str, depth: int = 2) -> Dict:
        """
        Get subgraph around a node for visualization
        
        Returns dict suitable for graph visualization libraries
        """
        nodes_to_include = {center_id}
        edges_to_include = []
        
        # BFS to find nearby nodes
        current_layer = [center_id]
        for _ in range(depth):
            next_layer = []
            for node_id in current_layer:
                for target_id, weight in self._get_connections(node_id):
                    if target_id not in nodes_to_include:
                        nodes_to_include.add(target_id)
                        next_layer.append(target_id)
                    edges_to_include.append({
                        'from': node_id,
                        'to': target_id,
                        'weight': weight
                    })
            current_layer = next_layer
        
        # Build visualization data
        viz_data = {
            'nodes': [
                {
                    'id': node_id,
                    'label': self.nodes[node_id].content[:30] + '...',
                    'activation': self.nodes[node_id].activation
                }
                for node_id in nodes_to_include
                if node_id in self.nodes
            ],
            'edges': edges_to_include
        }
        
        return viz_data
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info(f"Neural Memory Network closed: {self.db_path}")