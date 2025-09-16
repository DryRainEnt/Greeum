#!/usr/bin/env python3
"""
Direct embedding migration script - works with block_embeddings table
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


def get_embeddings_to_migrate(db_manager: DatabaseManager, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Get embeddings that need migration directly from block_embeddings table"""
    cursor = db_manager.conn.cursor()

    # Get block_embeddings entries that need migration
    cursor.execute("""
        SELECT be.block_index, be.embedding_model, be.embedding_dim,
               COALESCE(b.context, '') as context
        FROM block_embeddings be
        LEFT JOIN blocks b ON be.block_index = b.block_index
        WHERE be.embedding_model IN ('simple_hash_768', 'default', 'simple', 'simple_768')
           OR be.embedding_model IS NULL
           OR (be.embedding_model NOT LIKE 'st_%' AND be.embedding_model IS NOT NULL)
        ORDER BY be.block_index
        LIMIT ? OFFSET ?
    """, (limit, offset))

    entries = []
    for row in cursor.fetchall():
        entries.append({
            'block_index': row[0],
            'old_model': row[1] or 'unknown',
            'old_dim': row[2] or 0,
            'context': row[3] or f"Block #{row[0]}"  # Use block index as fallback
        })
    return entries


def migrate_batch_direct(db_manager: DatabaseManager, entries: List[Dict], model_name: str, dry_run: bool = False) -> int:
    """Migrate a batch of embeddings directly"""
    if not entries:
        return 0

    # Extract contexts
    contexts = [entry['context'] for entry in entries]

    # Batch encode
    print(f"  Encoding {len(contexts)} texts...")
    from greeum.embedding_models import get_embedding

    embeddings = []
    for context in contexts:
        embeddings.append(get_embedding(context))

    if dry_run:
        print(f"  [DRY RUN] Would update {len(entries)} embeddings")
        return len(entries)

    # Update database
    cursor = db_manager.conn.cursor()
    updated = 0

    for entry, embedding in zip(entries, embeddings):
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
                entry['block_index']
            ))

            updated += 1

    db_manager.conn.commit()
    return updated


def main():
    parser = argparse.ArgumentParser(description='Direct migration of embeddings')
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

    # Count total to migrate
    cursor = db_manager.conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM block_embeddings
        WHERE embedding_model IN ('simple_hash_768', 'default', 'simple', 'simple_768')
           OR embedding_model IS NULL
           OR (embedding_model NOT LIKE 'st_%' AND embedding_model IS NOT NULL)
    """)
    total_to_migrate = cursor.fetchone()[0]

    if total_to_migrate == 0:
        print("✅ No embeddings need migration. All are up to date.")
        return 0

    print(f"📊 Found {total_to_migrate} embeddings to migrate")

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
    offset = 0

    while True:
        batch_num += 1

        # Get next batch
        entries = get_embeddings_to_migrate(db_manager, args.batch_size, offset)
        if not entries:
            break

        print(f"\n📦 Batch {batch_num}:")
        print(f"  Processing indices {entries[0]['block_index']} to {entries[-1]['block_index']}")

        if args.verbose:
            for entry in entries[:3]:  # Show first 3
                context_preview = entry['context'][:50] if entry['context'] else "N/A"
                print(f"    #{entry['block_index']}: {context_preview}... [{entry['old_model']}]")
            if len(entries) > 3:
                print(f"    ... and {len(entries) - 3} more")

        # Migrate batch
        migrated = migrate_batch_direct(db_manager, entries, model_name, args.dry_run)
        total_migrated += migrated
        offset += args.batch_size

        # Progress
        progress = (total_migrated / total_to_migrate) * 100
        print(f"  Progress: {total_migrated}/{total_to_migrate} ({progress:.1f}%)")

        # Estimate time
        elapsed = time.time() - start_time
        if total_migrated > 0:
            rate = total_migrated / elapsed
            remaining = (total_to_migrate - total_migrated) / rate
            print(f"  Rate: {rate:.1f} embeddings/sec, ETA: {remaining:.0f}s")

    # Summary
    elapsed = time.time() - start_time
    print(f"\n✅ Migration completed!")
    print(f"   Total embeddings: {total_migrated}")
    print(f"   Time taken: {elapsed:.1f}s")
    if elapsed > 0:
        print(f"   Average: {total_migrated/elapsed:.1f} embeddings/sec")

    if not args.dry_run:
        # Verify
        cursor.execute("""
            SELECT COUNT(*)
            FROM block_embeddings
            WHERE embedding_model IN ('simple_hash_768', 'default', 'simple', 'simple_768')
               OR embedding_model IS NULL
               OR (embedding_model NOT LIKE 'st_%' AND embedding_model IS NOT NULL)
        """)
        remaining = cursor.fetchone()[0]
        if remaining > 0:
            print(f"\n⚠️  Warning: {remaining} embeddings still have old models")
        else:
            print(f"\n🎉 All embeddings successfully migrated to {model_name}!")

    return 0


if __name__ == '__main__':
    sys.exit(main())