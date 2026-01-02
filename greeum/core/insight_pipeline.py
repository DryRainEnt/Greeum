"""
Insight Pipeline for Greeum v5.0
3-Stage accuracy pipeline for memory storage

Flow:
1. Hybrid Search로 후보 추림 (Vector + BM25)
2. 확실한 케이스 빠른 처리 (유사도 > 0.85 AND 시간 < 5분 → LLM 스킵)
3. 불확실한 케이스 → LLM 최종 판단

Design principle: 정확도 최우선. 시간은 "힌트", 최종 판단은 LLM.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Thresholds for auto-attach (skip LLM)
AUTO_ATTACH_SIMILARITY = 0.85  # 85% similarity
AUTO_ATTACH_TIME_SECONDS = 300  # 5 minutes


@dataclass
class InsightCandidate:
    """Candidate block for insight attachment"""
    block_index: int
    block_hash: str
    content: str
    project: str
    similarity: float
    timestamp: str
    time_ago_seconds: float


@dataclass
class PipelineResult:
    """Result of insight pipeline processing"""
    action: str  # "attach", "new_context", "filtered"
    target_block_hash: Optional[str] = None
    target_block_index: Optional[int] = None
    project: Optional[str] = None
    confidence: float = 0.0
    reasoning: Optional[str] = None
    pipeline_stage: int = 0  # 1, 2, or 3
    llm_used: bool = False
    candidates_count: int = 0
    elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "target_block_hash": self.target_block_hash,
            "target_block_index": self.target_block_index,
            "project": self.project,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "pipeline_stage": self.pipeline_stage,
            "llm_used": self.llm_used,
            "candidates_count": self.candidates_count,
            "elapsed_ms": self.elapsed_ms
        }


class InsightPipeline:
    """
    3-Stage pipeline for accurate insight storage.

    Stage 1: Hybrid Search
        - Find top candidates using Vector + BM25

    Stage 2: Auto-Attach (Fast Path)
        - If best candidate has similarity > 0.85 AND time < 5 min
        - Skip LLM and attach directly

    Stage 3: LLM Decision
        - For uncertain cases, use LLM with full context
        - LLM sees candidates + time info and decides
    """

    def __init__(
        self,
        hybrid_search,
        context_classifier=None,
        project_anchor_manager=None,
        auto_attach_similarity: float = AUTO_ATTACH_SIMILARITY,
        auto_attach_time: float = AUTO_ATTACH_TIME_SECONDS
    ):
        """
        Initialize InsightPipeline.

        Args:
            hybrid_search: HybridGraphSearch instance
            context_classifier: ContextClassifier instance (for LLM calls)
            project_anchor_manager: ProjectAnchorManager instance
            auto_attach_similarity: Threshold for auto-attach (default: 0.85)
            auto_attach_time: Time threshold in seconds (default: 300)
        """
        self.hybrid_search = hybrid_search
        self.context_classifier = context_classifier
        self.anchor_manager = project_anchor_manager
        self.auto_attach_similarity = auto_attach_similarity
        self.auto_attach_time = auto_attach_time

        # Metrics
        self.metrics = {
            "total_processed": 0,
            "stage1_only": 0,
            "stage2_auto_attach": 0,
            "stage3_llm_used": 0,
            "new_contexts": 0,
            "avg_elapsed_ms": 0.0
        }

    def process(
        self,
        content: str,
        project: Optional[str] = None,
        embedding: Optional[Any] = None,
        force_llm: bool = False
    ) -> PipelineResult:
        """
        Process insight through the 3-stage pipeline.

        Args:
            content: Insight content to store
            project: Project name (optional)
            embedding: Pre-computed embedding (optional)
            force_llm: Force LLM decision even if auto-attach conditions met

        Returns:
            PipelineResult with storage decision
        """
        start_time = time.time()
        self.metrics["total_processed"] += 1

        # Get anchor for search
        anchor_hash = None
        if self.anchor_manager and project:
            anchor_hash = self.anchor_manager.get_anchor(project)

        # === Stage 1: Hybrid Search ===
        candidates = self._stage1_hybrid_search(
            content, embedding, anchor_hash, project
        )

        if not candidates:
            # No candidates - create new context
            elapsed_ms = (time.time() - start_time) * 1000
            self.metrics["new_contexts"] += 1
            return PipelineResult(
                action="new_context",
                project=project,
                confidence=1.0,
                reasoning="No similar blocks found - creating new context",
                pipeline_stage=1,
                llm_used=False,
                candidates_count=0,
                elapsed_ms=elapsed_ms
            )

        # Get time since last activity
        time_since_last = self._get_time_since_last_activity(project)

        # === Stage 2: Auto-Attach Check ===
        if not force_llm:
            auto_result = self._stage2_auto_attach(
                candidates, time_since_last
            )
            if auto_result:
                elapsed_ms = (time.time() - start_time) * 1000
                auto_result.elapsed_ms = elapsed_ms
                auto_result.candidates_count = len(candidates)
                self.metrics["stage2_auto_attach"] += 1
                self._update_avg_elapsed(elapsed_ms)
                return auto_result

        # === Stage 3: LLM Decision ===
        result = self._stage3_llm_decision(
            content, candidates, time_since_last, project
        )

        elapsed_ms = (time.time() - start_time) * 1000
        result.elapsed_ms = elapsed_ms
        result.candidates_count = len(candidates)
        self.metrics["stage3_llm_used"] += 1
        self._update_avg_elapsed(elapsed_ms)

        if result.action == "new_context":
            self.metrics["new_contexts"] += 1

        return result

    def _stage1_hybrid_search(
        self,
        content: str,
        embedding: Optional[Any],
        anchor_hash: Optional[str],
        project: Optional[str]
    ) -> List[InsightCandidate]:
        """Stage 1: Find candidates using Hybrid Search."""

        import numpy as np
        query_embedding = None
        if embedding is not None:
            query_embedding = np.array(embedding, dtype=np.float32)

        results, _ = self.hybrid_search.search(
            query=content,
            query_embedding=query_embedding,
            anchor_hash=anchor_hash,
            project=project,
            limit=10,
            threshold=0.1  # Low threshold to get more candidates
        )

        now = datetime.now()
        candidates = []

        for r in results:
            # Calculate time ago
            try:
                block_time = datetime.fromisoformat(r.timestamp.replace('Z', '+00:00'))
                time_ago = (now - block_time.replace(tzinfo=None)).total_seconds()
            except:
                time_ago = float('inf')

            candidates.append(InsightCandidate(
                block_index=r.block_index,
                block_hash=r.block_hash,
                content=r.content,
                project=r.project or project,
                similarity=r.hybrid_score,
                timestamp=r.timestamp,
                time_ago_seconds=time_ago
            ))

        return candidates

    def _stage2_auto_attach(
        self,
        candidates: List[InsightCandidate],
        time_since_last: float
    ) -> Optional[PipelineResult]:
        """
        Stage 2: Auto-attach if conditions are very clear.

        Conditions for auto-attach (skip LLM):
        - Best candidate similarity > 0.85
        - Time since last activity < 5 minutes
        """
        if not candidates:
            return None

        best = candidates[0]

        # Check auto-attach conditions
        if (best.similarity >= self.auto_attach_similarity and
            time_since_last < self.auto_attach_time):

            return PipelineResult(
                action="attach",
                target_block_hash=best.block_hash,
                target_block_index=best.block_index,
                project=best.project,
                confidence=best.similarity,
                reasoning=(
                    f"Auto-attached: similarity {best.similarity:.2%} > {self.auto_attach_similarity:.0%} "
                    f"AND time {time_since_last:.0f}s < {self.auto_attach_time}s"
                ),
                pipeline_stage=2,
                llm_used=False
            )

        return None

    def _stage3_llm_decision(
        self,
        content: str,
        candidates: List[InsightCandidate],
        time_since_last: float,
        project: Optional[str]
    ) -> PipelineResult:
        """
        Stage 3: Use LLM for uncertain cases.

        LLM receives:
        - New content
        - Top candidates with similarity and time info
        - Current project context
        """

        # If no classifier available, use heuristic
        if not self.context_classifier or not self.context_classifier.is_available():
            return self._heuristic_decision(candidates, time_since_last, project)

        # Build prompt with time context
        prompt = self._build_llm_prompt(content, candidates, time_since_last, project)

        try:
            # Use existing classifier's LLM call capability
            result = self.context_classifier.classify(content, context_hint=prompt)

            if result.create_new_branch:
                return PipelineResult(
                    action="new_context",
                    project=project,
                    confidence=result.confidence,
                    reasoning=result.reasoning or "LLM decided new context",
                    pipeline_stage=3,
                    llm_used=True
                )
            else:
                # Find the target block from classifier result
                target_hash = result.target_block_id
                target_index = None

                # Match to our candidates
                for c in candidates:
                    if c.block_hash == target_hash:
                        target_index = c.block_index
                        break

                # If no match, use best candidate
                if target_hash is None and candidates:
                    target_hash = candidates[0].block_hash
                    target_index = candidates[0].block_index

                return PipelineResult(
                    action="attach",
                    target_block_hash=target_hash,
                    target_block_index=target_index,
                    project=result.branch_id or project,
                    confidence=result.confidence,
                    reasoning=result.reasoning or "LLM selected existing branch",
                    pipeline_stage=3,
                    llm_used=True
                )

        except Exception as e:
            logger.warning(f"LLM decision failed, using heuristic: {e}")
            return self._heuristic_decision(candidates, time_since_last, project)

    def _heuristic_decision(
        self,
        candidates: List[InsightCandidate],
        time_since_last: float,
        project: Optional[str]
    ) -> PipelineResult:
        """Fallback heuristic when LLM is unavailable."""

        if not candidates:
            return PipelineResult(
                action="new_context",
                project=project,
                confidence=0.5,
                reasoning="No candidates - heuristic: create new context",
                pipeline_stage=3,
                llm_used=False
            )

        best = candidates[0]

        # Heuristic: attach if similarity > 0.5 or time < 30 min
        if best.similarity > 0.5 or time_since_last < 1800:
            return PipelineResult(
                action="attach",
                target_block_hash=best.block_hash,
                target_block_index=best.block_index,
                project=best.project,
                confidence=best.similarity,
                reasoning=f"Heuristic: similarity {best.similarity:.2%}, time {time_since_last:.0f}s",
                pipeline_stage=3,
                llm_used=False
            )
        else:
            return PipelineResult(
                action="new_context",
                project=project,
                confidence=0.6,
                reasoning=f"Heuristic: low similarity {best.similarity:.2%} and long time {time_since_last:.0f}s",
                pipeline_stage=3,
                llm_used=False
            )

    def _build_llm_prompt(
        self,
        content: str,
        candidates: List[InsightCandidate],
        time_since_last: float,
        project: Optional[str]
    ) -> str:
        """Build context hint for LLM with time information."""

        lines = []

        if project:
            lines.append(f"Current project: {project}")

        lines.append(f"Time since last activity: {self._format_time(time_since_last)}")
        lines.append("")
        lines.append("Top candidates (Hybrid Search):")

        for i, c in enumerate(candidates[:5], 1):
            time_str = self._format_time(c.time_ago_seconds)
            lines.append(
                f"  {i}. [{c.project or 'unknown'}] "
                f"\"{c.content[:60]}...\" "
                f"(similarity: {c.similarity:.2%}, {time_str} ago)"
            )

        lines.append("")
        lines.append("Decision guidelines:")
        lines.append("- Time proximity alone doesn't mean same context")
        lines.append("- High similarity with old content may still be same context")
        lines.append("- Different topics = different context, even if recent")

        return "\n".join(lines)

    def _format_time(self, seconds: float) -> str:
        """Format seconds into human readable string."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.0f}m"
        elif seconds < 86400:
            return f"{seconds/3600:.1f}h"
        else:
            return f"{seconds/86400:.1f}d"

    def _get_time_since_last_activity(self, project: Optional[str]) -> float:
        """Get seconds since last activity in project."""

        if not self.anchor_manager or not project:
            return float('inf')

        try:
            # Get anchor's last update time
            cursor = self.anchor_manager.db_manager.conn.cursor()
            cursor.execute("""
                SELECT last_updated FROM project_anchors WHERE project_name = ?
            """, (project,))
            row = cursor.fetchone()

            if row and row[0]:
                last_time = datetime.fromisoformat(row[0])
                return (datetime.now() - last_time).total_seconds()
        except Exception as e:
            logger.debug(f"Could not get last activity time: {e}")

        return float('inf')

    def _update_avg_elapsed(self, elapsed_ms: float) -> None:
        """Update running average of elapsed time."""
        n = self.metrics["total_processed"]
        if n == 0:
            return
        self.metrics["avg_elapsed_ms"] = (
            self.metrics["avg_elapsed_ms"] * (n - 1) + elapsed_ms
        ) / n

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        total = self.metrics["total_processed"]
        return {
            **self.metrics,
            "stage2_rate": self.metrics["stage2_auto_attach"] / total if total else 0,
            "stage3_rate": self.metrics["stage3_llm_used"] / total if total else 0,
            "new_context_rate": self.metrics["new_contexts"] / total if total else 0
        }


def store_insight(
    content: str,
    pipeline: InsightPipeline,
    block_manager,
    project: Optional[str] = None,
    embedding: Optional[Any] = None,
    importance: float = 0.5
) -> Dict[str, Any]:
    """
    High-level function to store an insight using the 3-stage pipeline.

    Args:
        content: Insight content
        pipeline: InsightPipeline instance
        block_manager: BlockManager instance
        project: Project name
        embedding: Pre-computed embedding
        importance: Importance score

    Returns:
        Storage result with block info
    """
    # Process through pipeline
    result = pipeline.process(content, project, embedding)

    if result.action == "filtered":
        return {
            "stored": False,
            "reason": result.reasoning,
            "pipeline_result": result.to_dict()
        }

    # Prepare block data
    before_hash = result.target_block_hash if result.action == "attach" else None

    # Store the block
    try:
        block_index = block_manager.add_block(
            content=content,
            importance=importance,
            before=before_hash,
            root=project
        )

        # Update anchor if anchor manager available
        if pipeline.anchor_manager and project:
            new_block = block_manager.get_block(block_index)
            if new_block:
                pipeline.anchor_manager.set_anchor(
                    project,
                    new_block.get("hash", ""),
                    block_index
                )

        return {
            "stored": True,
            "block_index": block_index,
            "action": result.action,
            "project": project,
            "pipeline_result": result.to_dict()
        }

    except Exception as e:
        logger.error(f"Failed to store insight: {e}")
        return {
            "stored": False,
            "error": str(e),
            "pipeline_result": result.to_dict()
        }
