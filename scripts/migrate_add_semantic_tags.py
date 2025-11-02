#!/usr/bin/env python3
"""
Greeum v3.1: Batch Semantic Tagging for Existing Memories
기존 메모리 블록에 semantic tags 일괄 추가
"""

import sys
import logging
from pathlib import Path
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from greeum.core.database_manager import DatabaseManager
from greeum.core.semantic_tagging import SemanticTagger

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_semantic_tags(data_dir: str, dry_run: bool = False, batch_size: int = 100):
    """
    기존 메모리 블록에 semantic tags 추가

    Args:
        data_dir: 데이터 디렉토리 경로
        dry_run: True면 실제 저장 안함 (미리보기)
        batch_size: 배치 처리 크기
    """
    logger.info(f"Starting semantic tagging migration: {data_dir}")

    # Initialize components
    db_path = Path(data_dir) / "memory.db"
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return

    db_manager = DatabaseManager(connection_string=str(db_path))
    tagger = SemanticTagger(db_manager)

    # Get all blocks without tags
    cursor = db_manager.conn.cursor()

    # Check how many blocks need tagging
    cursor.execute("""
        SELECT COUNT(DISTINCT b.block_index)
        FROM blocks b
        LEFT JOIN memory_tags mt ON b.block_index = mt.memory_id
        WHERE mt.memory_id IS NULL
    """)
    total_untagged = cursor.fetchone()[0]

    logger.info(f"Found {total_untagged} blocks without tags")

    if total_untagged == 0:
        logger.info("All blocks already tagged!")
        return

    # Process in batches
    cursor.execute("""
        SELECT b.block_index, b.context, b.timestamp
        FROM blocks b
        LEFT JOIN memory_tags mt ON b.block_index = mt.memory_id
        WHERE mt.memory_id IS NULL
        ORDER BY b.block_index
    """)

    blocks_to_tag = cursor.fetchall()

    stats = {
        'total': len(blocks_to_tag),
        'tagged': 0,
        'categories': {},
        'activities': {},
        'domains': set()
    }

    logger.info(f"Processing {stats['total']} blocks...")

    # Process with progress bar
    for block_index, context, timestamp in tqdm(blocks_to_tag, desc="Tagging"):
        try:
            # Generate tags
            tags = tagger.quick_tag(context)

            # Update stats
            stats['categories'][tags.category] = stats['categories'].get(tags.category, 0) + 1
            stats['activities'][tags.activity] = stats['activities'].get(tags.activity, 0) + 1
            stats['domains'].update(tags.domains)

            if dry_run:
                # Just preview
                logger.debug(f"[DRY RUN] Block {block_index}: {tags.category}/{tags.activity} + {tags.domains}")
            else:
                # Save to DB
                tagger.save_tags(block_index, tags)
                stats['tagged'] += 1

        except Exception as e:
            logger.error(f"Failed to tag block {block_index}: {e}")
            continue

    # Print summary
    logger.info("=" * 60)
    logger.info("Migration Summary")
    logger.info("=" * 60)
    logger.info(f"Total blocks processed: {stats['total']}")
    logger.info(f"Successfully tagged: {stats['tagged']}")
    logger.info("")
    logger.info("Category distribution:")
    for cat, count in sorted(stats['categories'].items(), key=lambda x: -x[1]):
        logger.info(f"  {cat}: {count}")
    logger.info("")
    logger.info("Activity distribution:")
    for act, count in sorted(stats['activities'].items(), key=lambda x: -x[1]):
        logger.info(f"  {act}: {count}")
    logger.info("")
    logger.info(f"Total unique domains: {len(stats['domains'])}")
    logger.info(f"Domains: {', '.join(sorted(stats['domains'])[:20])}...")
    logger.info("=" * 60)

    # Run tag consolidation
    if not dry_run:
        logger.info("Running tag consolidation...")
        tagger.consolidate_tags()
        logger.info("Consolidation complete!")

    db_manager.conn.close()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Add semantic tags to existing memory blocks"
    )
    parser.add_argument(
        '--data-dir',
        default='~/.greeum',
        help='Data directory path (default: ~/.greeum)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview without saving'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch processing size'
    )

    args = parser.parse_args()

    data_dir = Path(args.data_dir).expanduser()

    if args.dry_run:
        logger.info("=== DRY RUN MODE ===")

    migrate_semantic_tags(
        str(data_dir),
        dry_run=args.dry_run,
        batch_size=args.batch_size
    )


if __name__ == '__main__':
    main()
