"""
CLI commands for branch merge operations
"""

import click
from typing import Optional
from greeum.core.block_manager import BlockManager
from greeum.core.database_manager import DatabaseManager
from greeum.core.merge_engine import MergeEngine
import json


@click.group()
def merge():
    """Branch merge management commands"""
    pass


@merge.command()
@click.option('--slot-i', '-i', required=True, help='First slot to merge (A/B/C)')
@click.option('--slot-j', '-j', required=True, help='Second slot to merge (A/B/C)')
@click.option('--dry-run', is_flag=True, help='Simulate merge without applying')
@click.option('--db-path', default='data/memory.db', help='Database path')
def evaluate(slot_i: str, slot_j: str, dry_run: bool, db_path: str):
    """Evaluate merge between two slots"""
    
    db_manager = DatabaseManager(connection_string=db_path)
    merge_engine = MergeEngine(db_manager=db_manager)
    
    # Get block data for both slots
    from greeum.core.stm_manager import STMManager
    stm = STMManager(db_manager)
    
    head_i = stm.get_active_head(slot_i)
    head_j = stm.get_active_head(slot_j)
    
    if not head_i or not head_j:
        click.echo(f"❌ Cannot evaluate merge: missing heads for slots {slot_i} or {slot_j}")
        return
        
    # Get block data
    block_manager = BlockManager(db_manager)
    block_i = block_manager._get_block_by_hash(head_i)
    block_j = block_manager._get_block_by_hash(head_j)
    
    if not block_i or not block_j:
        click.echo("❌ Failed to retrieve block data")
        return
        
    # Check same root requirement
    if block_i.get('root') != block_j.get('root'):
        click.echo(f"❌ Cannot merge: different roots ({block_i.get('root')} vs {block_j.get('root')})")
        return
        
    # Calculate merge score
    try:
        merge_score = merge_engine.calculate_merge_score(block_i, block_j)
        
        click.echo(f"\n📊 Merge Score Analysis")
        click.echo(f"{'='*40}")
        click.echo(f"Total Score: {merge_score.total:.3f}")
        click.echo(f"\nComponents:")
        for component, value in merge_score.components.items():
            click.echo(f"  • {component}: {value:.3f}")
            
        # Record for EMA tracking
        merge_engine.record_similarity(slot_i, slot_j, merge_score.total)
        
        # Evaluate merge
        result = merge_engine.evaluate_merge(slot_i, slot_j, dry_run=dry_run)
        
        click.echo(f"\n🎯 Merge Decision")
        click.echo(f"{'='*40}")
        click.echo(f"Should Merge: {'✅ Yes' if result.should_merge else '❌ No'}")
        click.echo(f"Reason: {result.reason}")
        click.echo(f"Mode: {'🔍 Dry Run' if dry_run else '⚡ Live'}")
        
        if result.should_merge and not dry_run:
            # Apply merge
            checkpoint = merge_engine.apply_merge(slot_i, slot_j)
            click.echo(f"\n✅ Merge Applied!")
            click.echo(f"Checkpoint ID: {checkpoint.id}")
            click.echo(f"Reversible: {'Yes (5 min window)' if checkpoint.reversible else 'No'}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@merge.command()
@click.argument('checkpoint_id')
@click.option('--db-path', default='data/memory.db', help='Database path')
def undo(checkpoint_id: str, db_path: str):
    """Undo a merge checkpoint"""
    
    db_manager = DatabaseManager(connection_string=db_path)
    block_manager = BlockManager(db_manager)
    
    success = block_manager.undo_merge(checkpoint_id)
    
    if success:
        click.echo(f"✅ Successfully undone checkpoint {checkpoint_id}")
    else:
        click.echo(f"❌ Failed to undo checkpoint {checkpoint_id}")
        click.echo("Possible reasons:")
        click.echo("  • Checkpoint not found")
        click.echo("  • Outside 5-minute undo window")
        click.echo("  • Already undone")


@merge.command()
@click.option('--db-path', default='data/memory.db', help='Database path')
def status(db_path: str):
    """Show merge engine status"""
    
    db_manager = DatabaseManager(connection_string=db_path)
    merge_engine = MergeEngine(db_manager=db_manager)
    
    click.echo(f"\n🔄 Merge Engine Status")
    click.echo(f"{'='*40}")
    
    # Cooldown status
    if merge_engine.cooldown.is_in_cooldown():
        remaining = merge_engine.cooldown.time_remaining()
        click.echo(f"Cooldown: ⏱️ Active ({remaining:.0f}s remaining)")
    else:
        click.echo(f"Cooldown: ✅ Ready")
        
    # EMA trackers
    click.echo(f"\nEMA Trackers:")
    if merge_engine.ema_trackers:
        for (slot_i, slot_j), tracker in merge_engine.ema_trackers.items():
            click.echo(f"  • {slot_i}↔{slot_j}: {tracker.current_value:.3f} (history: {len(tracker.history)})")
    else:
        click.echo("  No active trackers")
        
    # Recent checkpoints
    click.echo(f"\nRecent Checkpoints:")
    if merge_engine.checkpoints:
        for cp in merge_engine.checkpoints[-5:]:  # Show last 5
            status = "❌ Undone" if cp.undone else "✅ Active"
            click.echo(f"  • {cp.id[:8]}... ({cp.slot_i}↔{cp.slot_j}): {status}")
    else:
        click.echo("  No checkpoints")


def register_commands(cli):
    """Register merge commands with main CLI"""
    cli.add_command(merge)