#!/usr/bin/env python3
"""
Bootstrap GraphIndex from existing LTM blocks.

Creates graph edges using similarity, temporal, and co-occurrence signals
with configurable alpha/beta/gamma weights.
"""

import argparse
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Set
from datetime import datetime, timedelta
import numpy as np

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from greeum.core.database_manager import DatabaseManager
from greeum.core.block_manager import BlockManager
from greeum.embedding_models import get_embedding
from greeum.graph import GraphIndex
from greeum.anchors import AnchorManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GraphBootstrapper:
    """Bootstrap graph index from existing memory blocks."""
    
    def __init__(self, db_path: str, alpha: float = 0.7, beta: float = 0.2, gamma: float = 0.1):
        """
        Initialize bootstrapper with weight parameters.
        
        Args:
            db_path: Database file path
            alpha: Similarity weight (0.0-1.0)
            beta: Temporal proximity weight (0.0-1.0)  
            gamma: Co-occurrence weight (0.0-1.0)
        """
        self.db_manager = DatabaseManager(db_path)
        self.block_manager = BlockManager(self.db_manager)
        self.alpha = alpha
        self.beta = beta  
        self.gamma = gamma
        
        # Normalize weights
        total = alpha + beta + gamma
        if total > 0:
            self.alpha /= total
            self.beta /= total
            self.gamma /= total
            
        logger.info(f"Bootstrap weights: α={self.alpha:.2f}, β={self.beta:.2f}, γ={self.gamma:.2f}")
    
    def get_all_blocks(self) -> List[Dict]:
        """Get all memory blocks from database."""
        try:
            # Get blocks with embeddings
            blocks = self.db_manager.search_blocks_by_embedding(
                query_embedding=[0.0] * 128,  # Dummy embedding
                top_k=10000  # Large number to get all
            )
            
            if not blocks:
                logger.warning("No blocks found in database")
                return []
                
            logger.info(f"Loaded {len(blocks)} blocks from database")
            return blocks
            
        except Exception as e:
            logger.error(f"Failed to load blocks: {e}")
            return []
    
    def compute_similarity_edges(self, blocks: List[Dict], threshold: float = 0.3) -> Dict[str, List[Tuple[str, float]]]:
        """Compute similarity-based edges between blocks."""
        logger.info("Computing similarity edges...")
        
        edges = {}
        total_pairs = len(blocks) * (len(blocks) - 1) // 2
        processed = 0
        
        for i, block_a in enumerate(blocks):
            block_id_a = str(block_a['block_index'])
            embedding_a = np.array(block_a['embedding'])
            
            if block_id_a not in edges:
                edges[block_id_a] = []
            
            for j in range(i + 1, len(blocks)):
                block_b = blocks[j]
                block_id_b = str(block_b['block_index'])
                embedding_b = np.array(block_b['embedding'])
                
                # Compute cosine similarity
                dot_product = np.dot(embedding_a, embedding_b)
                norm_a = np.linalg.norm(embedding_a)
                norm_b = np.linalg.norm(embedding_b)
                
                if norm_a > 0 and norm_b > 0:
                    similarity = dot_product / (norm_a * norm_b)
                    
                    # Add edge if above threshold
                    if similarity > threshold:
                        if block_id_b not in edges:
                            edges[block_id_b] = []
                            
                        edges[block_id_a].append((block_id_b, similarity))
                        edges[block_id_b].append((block_id_a, similarity))
                
                processed += 1
                if processed % 1000 == 0:
                    logger.info(f"Processed {processed}/{total_pairs} similarity pairs")
        
        # Sort neighbors by similarity
        for block_id in edges:
            edges[block_id].sort(key=lambda x: -x[1])
            edges[block_id] = edges[block_id][:32]  # Limit to top 32
        
        total_edges = sum(len(neighbors) for neighbors in edges.values())
        logger.info(f"Created {total_edges} similarity edges")
        
        return edges
    
    def compute_temporal_edges(self, blocks: List[Dict], max_time_gap: int = 3600) -> Dict[str, List[Tuple[str, float]]]:
        """Compute temporal proximity edges."""
        logger.info("Computing temporal edges...")
        
        # Sort blocks by timestamp
        sorted_blocks = sorted(blocks, key=lambda x: x.get('created_at', 0))
        
        edges = {}
        edge_count = 0
        
        for i, block_a in enumerate(sorted_blocks):
            block_id_a = str(block_a['block_index'])
            timestamp_a = block_a.get('created_at', 0)
            
            if block_id_a not in edges:
                edges[block_id_a] = []
            
            # Look for nearby blocks in time
            for j in range(max(0, i-10), min(len(sorted_blocks), i+11)):
                if i == j:
                    continue
                    
                block_b = sorted_blocks[j]
                block_id_b = str(block_b['block_index'])
                timestamp_b = block_b.get('created_at', 0)
                
                time_gap = abs(timestamp_a - timestamp_b)
                if time_gap <= max_time_gap:
                    # Temporal weight decreases with time gap
                    temporal_weight = max(0.0, 1.0 - (time_gap / max_time_gap))
                    
                    if temporal_weight > 0.1:  # Minimum threshold
                        if block_id_b not in edges:
                            edges[block_id_b] = []
                            
                        edges[block_id_a].append((block_id_b, temporal_weight))
                        edges[block_id_b].append((block_id_a, temporal_weight))
                        edge_count += 2
        
        # Sort and limit
        for block_id in edges:
            edges[block_id].sort(key=lambda x: -x[1])
            edges[block_id] = edges[block_id][:16]  # Limit to top 16
        
        logger.info(f"Created {edge_count} temporal edges")
        return edges
    
    def compute_cooccurrence_edges(self, blocks: List[Dict]) -> Dict[str, List[Tuple[str, float]]]:
        """Compute co-occurrence edges based on shared tags/keywords."""
        logger.info("Computing co-occurrence edges...")
        
        # Group blocks by tags
        tag_to_blocks = {}
        for block in blocks:
            block_id = str(block['block_index'])
            tags = block.get('tags', [])
            keywords = block.get('keywords', [])
            
            # Combine tags and keywords
            all_terms = set(tags + keywords)
            
            for term in all_terms:
                if term not in tag_to_blocks:
                    tag_to_blocks[term] = []
                tag_to_blocks[term].append(block_id)
        
        # Build co-occurrence edges
        edges = {}
        edge_count = 0
        
        for term, block_ids in tag_to_blocks.items():
            if len(block_ids) < 2:
                continue
                
            # Connect all pairs sharing this term
            for i, block_a in enumerate(block_ids):
                if block_a not in edges:
                    edges[block_a] = []
                    
                for j in range(i + 1, len(block_ids)):
                    block_b = block_ids[j]
                    if block_b not in edges:
                        edges[block_b] = []
                    
                    # Co-occurrence weight based on term frequency
                    cooccur_weight = min(1.0, 1.0 / len(block_ids))
                    
                    edges[block_a].append((block_b, cooccur_weight))
                    edges[block_b].append((block_a, cooccur_weight))
                    edge_count += 2
        
        # Aggregate and sort
        for block_id in edges:
            # Aggregate weights for same target
            weight_map = {}
            for target, weight in edges[block_id]:
                weight_map[target] = weight_map.get(target, 0) + weight
            
            edges[block_id] = [(target, weight) for target, weight in weight_map.items()]
            edges[block_id].sort(key=lambda x: -x[1])
            edges[block_id] = edges[block_id][:16]  # Limit to top 16
        
        logger.info(f"Created {edge_count} co-occurrence edges")
        return edges
    
    def merge_edges(self, sim_edges: Dict, temp_edges: Dict, cooccur_edges: Dict) -> Dict[str, List[Tuple[str, float]]]:
        """Merge three types of edges with alpha/beta/gamma weights."""
        logger.info("Merging edge types...")
        
        all_nodes = set(sim_edges.keys()) | set(temp_edges.keys()) | set(cooccur_edges.keys())
        merged_edges = {}
        
        for node in all_nodes:
            weight_map = {}
            
            # Add similarity edges
            for target, weight in sim_edges.get(node, []):
                weight_map[target] = weight_map.get(target, 0) + self.alpha * weight
            
            # Add temporal edges  
            for target, weight in temp_edges.get(node, []):
                weight_map[target] = weight_map.get(target, 0) + self.beta * weight
            
            # Add co-occurrence edges
            for target, weight in cooccur_edges.get(node, []):
                weight_map[target] = weight_map.get(target, 0) + self.gamma * weight
            
            # Convert to sorted list
            merged_edges[node] = [(target, weight) for target, weight in weight_map.items()]
            merged_edges[node].sort(key=lambda x: -x[1])
            merged_edges[node] = merged_edges[node][:32]  # Final limit
        
        total_edges = sum(len(neighbors) for neighbors in merged_edges.values())
        logger.info(f"Merged to {total_edges} total edges")
        
        return merged_edges
    
    def bootstrap_graph(self, output_path: str, theta: float = 0.35, kmax: int = 32) -> GraphIndex:
        """Bootstrap complete graph index."""
        logger.info("Starting graph bootstrap process...")
        start_time = time.time()
        
        # Load all blocks
        blocks = self.get_all_blocks()
        if not blocks:
            raise ValueError("No blocks found to bootstrap graph")
        
        # Compute different edge types
        sim_edges = self.compute_similarity_edges(blocks, threshold=0.3)
        temp_edges = self.compute_temporal_edges(blocks, max_time_gap=3600)
        cooccur_edges = self.compute_cooccurrence_edges(blocks)
        
        # Merge edges
        final_edges = self.merge_edges(sim_edges, temp_edges, cooccur_edges)
        
        # Create graph index
        graph = GraphIndex(theta=theta, kmax=kmax)
        
        # Add all edges to graph
        for node, neighbors in final_edges.items():
            graph.upsert_edges(node, neighbors)
        
        # Save to file
        graph.save_snapshot(Path(output_path))
        
        # Log statistics
        stats = graph.get_stats()
        elapsed = time.time() - start_time
        
        logger.info(f"Bootstrap completed in {elapsed:.2f}s")
        logger.info(f"Graph stats: {stats['node_count']} nodes, {stats['edge_count']} edges")
        logger.info(f"Average degree: {stats['avg_degree']:.2f}")
        
        return graph
    
    def initialize_anchors(self, anchor_path: str, blocks: List[Dict]) -> AnchorManager:
        """Initialize anchor slots with top-accessed blocks."""
        logger.info("Initializing anchor slots...")
        
        # Sort blocks by some activity metric (e.g., recent creation or importance)
        sorted_blocks = sorted(blocks, key=lambda x: x.get('created_at', 0), reverse=True)
        
        # Create anchor manager
        anchor_manager = AnchorManager(Path(anchor_path))
        
        if len(sorted_blocks) >= 3:
            # Initialize slots with recent blocks
            for i, slot in enumerate(['A', 'B', 'C']):
                if i < len(sorted_blocks):
                    block = sorted_blocks[i]
                    block_id = str(block['block_index'])
                    embedding = np.array(block['embedding'])
                    
                    anchor_manager.move_anchor(slot, block_id, embedding)
                    logger.info(f"Initialized slot {slot} with block {block_id}")
        
        return anchor_manager


def main():
    """Main bootstrap script entry point."""
    parser = argparse.ArgumentParser(description='Bootstrap Greeum Graph Index')
    parser.add_argument('--db-path', default='data/memory.db', help='Database path')
    parser.add_argument('--graph-output', default='data/graph_snapshot.jsonl', help='Graph output path')
    parser.add_argument('--anchor-output', default='data/anchors.json', help='Anchor output path')
    parser.add_argument('--alpha', type=float, default=0.7, help='Similarity weight')
    parser.add_argument('--beta', type=float, default=0.2, help='Temporal weight')
    parser.add_argument('--gamma', type=float, default=0.1, help='Co-occurrence weight')
    parser.add_argument('--theta', type=float, default=0.35, help='Edge weight threshold')
    parser.add_argument('--kmax', type=int, default=32, help='Max neighbors per node')
    
    args = parser.parse_args()
    
    try:
        # Create bootstrapper
        bootstrapper = GraphBootstrapper(
            db_path=args.db_path,
            alpha=args.alpha,
            beta=args.beta,
            gamma=args.gamma
        )
        
        # Bootstrap graph
        graph = bootstrapper.bootstrap_graph(
            output_path=args.graph_output,
            theta=args.theta,
            kmax=args.kmax
        )
        
        # Initialize anchors
        blocks = bootstrapper.get_all_blocks()
        anchor_manager = bootstrapper.initialize_anchors(args.anchor_output, blocks)
        
        logger.info("Bootstrap process completed successfully!")
        logger.info(f"Graph saved to: {args.graph_output}")
        logger.info(f"Anchors saved to: {args.anchor_output}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Bootstrap failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())