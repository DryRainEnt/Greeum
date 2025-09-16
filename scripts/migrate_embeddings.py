#!/usr/bin/env python3
"""
임베딩 마이그레이션 스크립트
SimpleEmbeddingModel (random) → SentenceTransformer (semantic)

Usage:
    python scripts/migrate_embeddings.py [--db-path path/to/memory.db] [--dry-run]
"""

import sys
import os
import time
import argparse
import sqlite3
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from greeum.core.database_manager import DatabaseManager
from greeum.embedding_models import init_sentence_transformer, embedding_registry


def get_old_embeddings_count(db_manager: DatabaseManager) -> int:
    """Count blocks with old embedding model"""
    cursor = db_manager.conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM block_embeddings
        WHERE embedding_model IN ('simple_hash_768', 'default', 'simple', 'simple_768')
           OR embedding_model IS NULL
           OR embedding_model NOT LIKE 'st_%'
    """)
    return cursor.fetchone()[0]


def get_blocks_to_migrate(db_manager: DatabaseManager, limit: int = 100, skip_indices: set = None) -> List[Dict[str, Any]]:
    """Get blocks that need migration"""
    cursor = db_manager.conn.cursor()

    # Build query with optional exclusion
    if skip_indices:
        placeholders = ','.join('?' * len(skip_indices))
        query = f"""
            SELECT b.block_index, b.context, e.embedding_model, e.embedding_dim
            FROM blocks b
            LEFT JOIN block_embeddings e ON b.block_index = e.block_index
            WHERE (e.embedding_model IN ('simple_hash_768', 'default', 'simple', 'simple_768')
               OR e.embedding_model IS NULL
               OR e.embedding_model NOT LIKE 'st_%')
               AND b.block_index NOT IN ({placeholders})
            ORDER BY b.block_index
            LIMIT ?
        """
        params = list(skip_indices) + [limit]
    else:
        query = """
            SELECT b.block_index, b.context, e.embedding_model, e.embedding_dim
            FROM blocks b
            LEFT JOIN block_embeddings e ON b.block_index = e.block_index
            WHERE e.embedding_model IN ('simple_hash_768', 'default', 'simple', 'simple_768')
               OR e.embedding_model IS NULL
               OR e.embedding_model NOT LIKE 'st_%'
            ORDER BY b.block_index
            LIMIT ?
        """
        params = [limit]

    cursor.execute(query, params)

    blocks = []
    for row in cursor.fetchall():
        blocks.append({
            'block_index': row[0],
            'context': row[1],
            'old_model': row[2] or 'unknown',
            'old_dim': row[3] or 0
        })
    return blocks


def migrate_batch(db_manager: DatabaseManager, blocks: List[Dict], model_name: str, dry_run: bool = False) -> int:
    """Migrate a batch of blocks"""
    if not blocks:
        return 0

    # Extract contexts
    contexts = [block['context'] for block in blocks]

    # Batch encode
    print(f"  Encoding {len(contexts)} texts...")
    from greeum.embedding_models import get_embedding

    embeddings = []
    for context in contexts:
        embeddings.append(get_embedding(context))

    if dry_run:
        print(f"  [DRY RUN] Would update {len(blocks)} blocks")
        # In dry-run mode, we still need to track processed blocks
        # to avoid infinite loop
        return len(blocks)

    # Update database
    cursor = db_manager.conn.cursor()
    updated = 0

    for block, embedding in zip(blocks, embeddings):
        if embedding:
            # Convert to numpy array and then to bytes
            emb_array = np.array(embedding, dtype=np.float32)

            cursor.execute("""
                UPDATE block_embeddings
                SET embedding = ?,
                    embedding_model = ?,
                    embedding_dim = ?
                WHERE block_index = ?
            """, (
                emb_array.tobytes(),
                model_name,
                len(embedding),
                block['block_index']
            ))

            updated += 1

    db_manager.conn.commit()
    return updated


def main():
    parser = argparse.ArgumentParser(description='Migrate embeddings to SentenceTransformer')
    parser.add_argument('--db-path', type=str, help='Path to database file')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for migration')
    parser.add_argument('--dry-run', action='store_true', help='Simulate migration without changes')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Find database
    if args.db_path:
        db_path = args.db_path
    else:
        # Try default locations
        candidates = [
            'data/memory.db',
            os.path.expanduser('~/.greeum/memory.db'),
            'memory.db'
        ]
        db_path = None
        for candidate in candidates:
            if os.path.exists(candidate):
                db_path = candidate
                break

        if not db_path:
            print("❌ No database found. Specify --db-path")
            sys.exit(1)

    print(f"📂 Database: {db_path}")

    # Initialize
    db_manager = DatabaseManager(db_path)

    # Check current state
    total_old = get_old_embeddings_count(db_manager)

    if total_old == 0:
        print("✅ No blocks need migration. All embeddings are up to date.")
        return 0

    print(f"📊 Found {total_old} blocks with old embeddings")

    # Initialize SentenceTransformer
    print("\n🔄 Initializing SentenceTransformer model...")
    try:
        model = init_sentence_transformer()
        model_name = model.get_model_name()
        print(f"✅ Model loaded: {model_name}")
        print(f"   Dimension: {model.get_dimension()} (actual: {model.get_actual_dimension()})")
    except Exception as e:
        print(f"❌ Failed to initialize model: {e}")
        print("\nPlease install sentence-transformers:")
        print("  pip install sentence-transformers")
        return 1

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made")

    # Migration loop
    print("\n🚀 Starting migration...")
    start_time = time.time()
    total_migrated = 0
    batch_num = 0
    processed_indices = set()  # Track processed blocks in dry-run mode

    while True:
        batch_num += 1

        # Get next batch, skipping already processed blocks
        blocks = get_blocks_to_migrate(db_manager, args.batch_size, processed_indices if args.dry_run else None)
        if not blocks:
            break

        print(f"\n📦 Batch {batch_num}:")
        print(f"  Processing blocks {blocks[0]['block_index']} to {blocks[-1]['block_index']}")

        if args.verbose:
            for block in blocks[:3]:  # Show first 3
                print(f"    #{block['block_index']}: {block['context'][:50]}... [{block['old_model']}]")
            if len(blocks) > 3:
                print(f"    ... and {len(blocks) - 3} more")

        # Track processed blocks in dry-run mode
        if args.dry_run:
            for block in blocks:
                processed_indices.add(block['block_index'])

        # Migrate batch
        migrated = migrate_batch(db_manager, blocks, model_name, args.dry_run)
        total_migrated += migrated

        # Progress
        progress = (total_migrated / total_old) * 100
        print(f"  Progress: {total_migrated}/{total_old} ({progress:.1f}%)")

        # Estimate time
        elapsed = time.time() - start_time
        if total_migrated > 0:
            rate = total_migrated / elapsed
            remaining = (total_old - total_migrated) / rate
            print(f"  Rate: {rate:.1f} blocks/sec, ETA: {remaining:.0f}s")

    # Summary
    elapsed = time.time() - start_time
    print(f"\n✅ Migration completed!")
    print(f"   Total blocks: {total_migrated}")
    print(f"   Time taken: {elapsed:.1f}s")
    print(f"   Average: {total_migrated/elapsed:.1f} blocks/sec")

    if not args.dry_run:
        # Verify
        remaining = get_old_embeddings_count(db_manager)
        if remaining > 0:
            print(f"\n⚠️  Warning: {remaining} blocks still have old embeddings")
        else:
            print(f"\n🎉 All embeddings successfully migrated to {model_name}!")

    return 0


if __name__ == '__main__':
    sys.exit(main())