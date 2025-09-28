"""
Simplified Usage Analytics Module (Stub)

This is a minimal implementation to prevent import errors.
The original complex analytics has been removed.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .stm_anchor_store import get_anchor_store

logger = logging.getLogger(__name__)


class UsageAnalytics:
    """Simplified usage analytics stub"""
    
    def __init__(self, db_manager=None):
        """Initialize analytics (no-op)"""
        self.db_manager = db_manager
        self.enabled = False  # Analytics disabled by default
        
    def log_search(self, query: str, results_count: int, duration_ms: float):
        """Log search event (no-op)"""
        if self.enabled:
            logger.debug(f"Search: {query[:20]}... ({results_count} results, {duration_ms}ms)")
    
    def log_memory_add(self, block_id: int, importance: float):
        """Log memory addition (no-op)"""
        if self.enabled:
            logger.debug(f"Memory added: Block #{block_id}")
    
    def log_operation(self, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """Log generic operation (no-op)"""
        if self.enabled:
            logger.debug(f"Operation: {operation}")
    
    def get_analytics_data(self, days: int = 7, report_type: str = 'usage') -> Dict[str, Any]:
        """Get analytics data (returns empty structure)"""
        return {
            'period_days': days,
            'report_type': report_type,
            'total_operations': 0,
            'total_searches': 0,
            'total_memories': 0,
            'average_search_time': 0.0,
            'memory_growth_rate': 0.0,
            'timestamp': datetime.now().isoformat()
        }

    def get_usage_report(self, days: int = 7, report_type: str = 'usage') -> Dict[str, Any]:
        """Get usage report - alias for get_analytics_data"""
        return self.get_analytics_data(days, report_type)

    def generate_system_report(self, days: int = 7) -> str:
        """Generate human-readable snapshot of slots, branches, and recent activity."""

        if not self.db_manager:
            return "No database manager configured; analytics unavailable."

        conn = getattr(self.db_manager, "conn", None)
        if conn is None and hasattr(self.db_manager, "_get_connection"):
            try:
                conn = self.db_manager._get_connection()
            except Exception:
                conn = None

        if conn is None:
            return "Unable to access database connection for analytics."

        cursor = conn.cursor()

        # Slot overview -------------------------------------------------
        slot_lines = []
        slot_branch_map = {}
        try:
            anchor_store = get_anchor_store()
            slots = anchor_store.get_slots() if anchor_store else {}
        except Exception:
            slots = {}

        for slot_name in sorted(slots.keys()):
            slot = slots[slot_name]
            anchor_hash = getattr(slot, "anchor_block", None)
            branch_label = ""
            context_snippet = "(no anchor)"
            last_seen = getattr(slot, "last_seen", 0)
            block_index = None

            if anchor_hash:
                cursor.execute(
                    "SELECT block_index, context, root, timestamp FROM blocks WHERE hash = ? LIMIT 1",
                    (anchor_hash,),
                )
                row = cursor.fetchone()
                if row:
                    block_index, context, root, timestamp = row
                    branch_label = root or "default"
                    slot_branch_map.setdefault(branch_label, set()).add(slot_name)
                    context_snippet = _shorten(context)
                    if timestamp:
                        last_seen = timestamp

            slot_lines.append(
                f"- {slot_name}: block {block_index if block_index is not None else 'n/a'}"
                f" | branch {branch_label or 'default'}"
                f" | {context_snippet}"
                f" | last-seen {format_timestamp(last_seen)}"
            )

        if not slot_lines:
            slot_lines.append("- No anchors configured. Use `greeum anchors set` to pin active branches.")

        # Branch overview -----------------------------------------------
        cursor.execute(
            """
            SELECT root, COUNT(*), MIN(timestamp), MAX(timestamp)
            FROM blocks
            GROUP BY root
            ORDER BY MAX(timestamp) DESC
            LIMIT 12
            """
        )

        branch_lines = []
        for root, count, first_ts, last_ts in cursor.fetchall():
            branch_key = root or "default"
            cursor.execute(
                """
                SELECT block_index, context FROM blocks
                WHERE (? IS NULL AND (root IS NULL OR root = ''))
                   OR root = ?
                ORDER BY block_index DESC
                LIMIT 1
                """,
                (root, root),
            )
            latest_row = cursor.fetchone()
            latest_idx = latest_row[0] if latest_row else None
            latest_ctx = _shorten(latest_row[1]) if latest_row else ""
            slots_for_branch = ''.join(sorted(slot_branch_map.get(branch_key, [])))
            slot_marker = f" [{slots_for_branch}]" if slots_for_branch else ""

            branch_lines.append(
                f"• {branch_key[:10]}{slot_marker} — {count} memories"
                f" (from {format_timestamp(first_ts)} to {format_timestamp(last_ts)})\n"
                f"  last #{latest_idx if latest_idx is not None else 'n/a'}: {latest_ctx}"
            )

        if not branch_lines:
            branch_lines.append("• No branches found yet. New memories will establish branch roots automatically.")

        # Usage summary -------------------------------------------------
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()

        cursor.execute(
            "SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM blocks WHERE timestamp >= ?",
            (cutoff_iso,),
        )
        recent_count, recent_first, recent_last = cursor.fetchone()

        cursor.execute("SELECT COUNT(*), MAX(block_index), MAX(timestamp) FROM blocks")
        total_count, latest_index, latest_timestamp = cursor.fetchone()

        avg_per_day = (recent_count / days) if days > 0 else recent_count

        usage_lines = [
            f"- Total memories: {total_count or 0}",
            f"- New memories (last {days} days): {recent_count or 0} (avg {avg_per_day:.2f}/day)",
            f"- Recent activity: {format_timestamp(recent_first)} → {format_timestamp(recent_last)}",
            f"- Latest block: #{latest_index if latest_index is not None else 'n/a'} at {format_timestamp(latest_timestamp)}",
        ]

        report_lines = [
            "=== Slot Overview ===",
            *slot_lines,
            "",
            "=== Branch Overview (recent) ===",
            *branch_lines,
            "",
            f"=== Usage (last {days} days) ===",
            *usage_lines,
        ]

        return "\n".join(report_lines)
    
    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get quality metrics (returns empty structure)"""
        return {
            'duplicate_rate': 0.0,
            'average_quality_score': 1.0,
            'promotion_success_rate': 1.0,
            'error_rate': 0.0
        }
    
    def track_slots_operation(self, operation: str, slot_name: str = None, **kwargs):
        """Track slots operation (no-op stub)"""
        if self.enabled:
            logger.debug(f"Slots operation: {operation} on {slot_name}")
    
    def log_quality_metrics(self, content_length: int, quality_score: float, quality_level: str,
                           original_importance: float, adjusted_importance: float, 
                           is_duplicate: bool = False, similarity_score: float = 0.0, 
                           suggestions_count: int = 0):
        """Log quality metrics (no-op stub)"""
        if self.enabled:
            logger.debug(f"Quality metrics: length={content_length}, score={quality_score}, level={quality_level}")
    
    def log_event(self, event_type: str, tool_name: str = None, metadata: Optional[Dict[str, Any]] = None,
                  duration_ms: float = None, success: bool = True, error_message: str = None,
                  session_id: str = None):
        """Log event (no-op stub) - Added to fix missing method error"""
        if self.enabled:
            logger.debug(f"Event: {event_type} - {tool_name}")
        return True

    def track_ai_intent(self, intent: str = None, confidence: float = 0.5, metadata: Optional[Dict[str, Any]] = None,
                       input_content: str = None, predicted_intent: str = None, predicted_slot: str = None,
                       actual_slot_used: str = None, importance_score: float = None, context_metadata: Optional[Dict[str, Any]] = None, **kwargs):
        """Track AI intent (no-op stub) - Added for slots functionality"""
        if self.enabled:
            intent_to_log = intent or predicted_intent or "unknown"
            logger.debug(f"AI Intent: {intent_to_log} (confidence: {confidence})")
        return True

    def close(self):
        """Close analytics (no-op)"""
        pass


def _shorten(text: Optional[str], length: int = 80) -> str:
    if not text:
        return ""
    single_line = " ".join(str(text).split())
    return single_line[:length] + ("…" if len(single_line) > length else "")


def format_timestamp(value: Optional[Any]) -> str:
    if not value:
        return "n/a"
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value)).strftime("%Y-%m-%d")
    try:
        return str(value)[:19]
    except Exception:
        return "n/a"
