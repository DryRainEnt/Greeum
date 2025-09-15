#!/usr/bin/env python3
"""
Unify all embeddings to 768D using SimpleEmbeddingModel
Quick fix for dimension mismatch in v3.1.0rc5
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import numpy as np
from greeum.embedding_models import SimpleEmbeddingModel
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def unify_embeddings():
    """Unify all embeddings to 768D"""

    # Connect to database with immediate transaction for exclusive access
    db_path = os.path.expanduser('~/.greeum/memory.db')
    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")  # Use WAL mode to avoid locks
    conn.execute("PRAGMA busy_timeout=30000")  # Wait up to 30 seconds
    cursor = conn.cursor()

    # Create 768D embedding model
    model = SimpleEmbeddingModel(dimension=768)

    # Get blocks that need re-embedding
    cursor.execute("""
        SELECT b.block_index, b.context
        FROM blocks b
        LEFT JOIN block_embeddings be ON b.block_index = be.block_index
        WHERE be.embedding_dim != 768 OR be.embedding_dim IS NULL
        ORDER BY b.block_index
    """)

    blocks_to_update = cursor.fetchall()
    total = len(blocks_to_update)

    logger.info(f"📊 Found {total} blocks needing re-embedding to 768D")

    if total == 0:
        logger.info("✅ All embeddings already unified!")
        return

    # Update each block
    updated = 0
    for block_index, context in blocks_to_update:
        try:
            # Generate 768D embedding
            embedding = model.encode(context or "")
            embedding_array = np.array(embedding, dtype=np.float32)

            # Update or insert embedding
            cursor.execute("""
                INSERT OR REPLACE INTO block_embeddings
                (block_index, embedding, embedding_model, embedding_dim)
                VALUES (?, ?, ?, ?)
            """, (
                block_index,
                embedding_array.tobytes(),
                'simple',
                768
            ))

            updated += 1
            if updated % 50 == 0:
                logger.info(f"  Progress: {updated}/{total} blocks updated...")

        except Exception as e:
            logger.error(f"  ❌ Error updating block {block_index}: {e}")

    # Commit changes
    conn.commit()

    # Verify results
    cursor.execute("""
        SELECT embedding_dim, COUNT(*)
        FROM block_embeddings
        GROUP BY embedding_dim
    """)

    logger.info(f"\n✅ Successfully updated {updated}/{total} embeddings!")
    logger.info("\n📊 Final embedding dimensions:")
    for dim, count in cursor.fetchall():
        logger.info(f"  {dim or 'NULL'}D: {count} blocks")

    conn.close()
    logger.info("\n🎉 Embedding unification complete!")

if __name__ == "__main__":
    unify_embeddings()