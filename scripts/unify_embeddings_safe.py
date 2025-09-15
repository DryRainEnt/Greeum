#!/usr/bin/env python3
"""
Safely unify embeddings by copying database first
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import numpy as np
import shutil
from datetime import datetime
from greeum.embedding_models import SimpleEmbeddingModel
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def unify_embeddings():
    """Unify all embeddings to 768D in a copy of the database"""

    # Paths
    original_db = os.path.expanduser('~/.greeum/memory.db')
    temp_db = os.path.expanduser('~/.greeum/memory_unified.db')
    backup_db = os.path.expanduser(f'~/.greeum/memory_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')

    logger.info(f"📋 Copying database to work on...")
    shutil.copy2(original_db, temp_db)

    # Work on the copy
    conn = sqlite3.connect(temp_db)
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
        os.remove(temp_db)
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
    logger.info("\n📊 Final embedding dimensions in new DB:")
    for dim, count in cursor.fetchall():
        logger.info(f"  {dim or 'NULL'}D: {count} blocks")

    conn.close()

    # Create backup and swap files
    logger.info(f"\n💾 Creating backup at: {backup_db}")
    shutil.copy2(original_db, backup_db)

    logger.info("🔄 Swapping database files...")
    os.rename(temp_db, original_db)

    logger.info("\n🎉 Embedding unification complete! MCP server may need restart.")

if __name__ == "__main__":
    unify_embeddings()