"""Main processing loop for the consolidator."""

from __future__ import annotations

import logging
import signal
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from .candidates import CandidatePair, select_candidates
from .config import ConsolidatorConfig
from .context_gatherer import ContextGatherer
from .db import ConsolidatorDB
from .judge import ConsolidationJudge, Verdict
from .llm_client import OllamaClient
from .state import ComparisonRecord, StateManager
from .writer import AssociationWriter

logger = logging.getLogger(__name__)


@dataclass
class ConsolidationReport:
    """Summary of a consolidation run."""
    total_candidates: int = 0
    processed: int = 0
    connected: int = 0
    rejected: int = 0
    deferred: int = 0
    errors: int = 0
    total_latency_ms: int = 0
    verdicts: List[dict] = field(default_factory=list)

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.processed if self.processed else 0.0

    def summary(self) -> str:
        lines = [
            f"Consolidation Report:",
            f"  Candidates: {self.total_candidates}",
            f"  Processed:  {self.processed}",
            f"  Connected:  {self.connected}",
            f"  Rejected:   {self.rejected}",
            f"  Deferred:   {self.deferred}",
            f"  Errors:     {self.errors}",
            f"  Avg latency: {self.avg_latency_ms:.0f}ms",
        ]
        return "\n".join(lines)


class ConsolidationLoop:
    """Orchestrates batch and daemon consolidation."""

    def __init__(self, config: ConsolidatorConfig) -> None:
        self.config = config
        self.db = ConsolidatorDB(config.db_path, config.busy_timeout_ms)
        self.state = StateManager(self.db)
        self.gatherer = ContextGatherer(self.db, config.max_neighbors)
        self.llm = OllamaClient(config.ollama_url, config.model, config.llm_timeout)
        self.judge = ConsolidationJudge(self.gatherer, self.llm)
        self.writer = AssociationWriter(self.db)
        self._shutdown = False

    def _drain_queue(self, max_pairs: int) -> List[CandidatePair]:
        """Select candidate pairs from the consolidation_queue (incremental mode).

        For each pending block in the queue, find its top similar neighbours
        from the embedding matrix and return them as CandidatePair objects.
        """
        import sqlite3

        # Recover stale 'processing' blocks (stuck from a previous crash)
        try:
            self.db._execute_write(
                "UPDATE consolidation_queue SET status = 'pending' WHERE status = 'processing'"
            )
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            pass  # Table may not exist yet

        # Atomic SELECT + UPDATE inside a single BEGIN IMMEDIATE transaction
        try:
            with self.db._write_tx() as conn:
                cur = conn.execute(
                    "SELECT block_index FROM consolidation_queue WHERE status = 'pending' ORDER BY id LIMIT ?",
                    (max_pairs,),
                )
                pending = [row[0] for row in cur.fetchall()]
                if pending:
                    ph = ",".join("?" for _ in pending)
                    conn.execute(
                        f"UPDATE consolidation_queue SET status = 'processing' WHERE block_index IN ({ph})",
                        tuple(pending),
                    )
        except sqlite3.OperationalError:
            return []  # Table may not exist yet

        if not pending:
            return []

        logger.info("Queue has %d pending blocks for incremental consolidation", len(pending))

        # Load all embeddings and find similar pairs for the pending blocks
        import numpy as np
        raw = self.db.get_all_embeddings()
        if len(raw) < 2:
            self._mark_queue_done(pending)
            return []

        idx_to_pos = {idx: i for i, (idx, _) in enumerate(raw)}
        block_indices = [idx for idx, _ in raw]
        embeddings = np.stack([emb for _, emb in raw])
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        normalized = embeddings / norms

        compared_set = self.state.load_compared_set()
        connected_set = self.db.get_existing_association_pairs()
        exclude_set = compared_set | connected_set

        candidates: List[CandidatePair] = []
        for bi in pending:
            if bi not in idx_to_pos:
                continue
            pos = idx_to_pos[bi]
            sims = normalized[pos] @ normalized.T
            for j in range(len(block_indices)):
                if j == pos:
                    continue
                sim = float(sims[j])
                if sim < self.config.min_cosine_similarity:
                    continue
                a, b = min(bi, block_indices[j]), max(bi, block_indices[j])
                if (a, b) in exclude_set:
                    continue
                candidates.append(CandidatePair(block_a=a, block_b=b, cosine_similarity=sim))
                exclude_set.add((a, b))

        candidates.sort(key=lambda c: c.cosine_similarity, reverse=True)
        result = candidates[:max_pairs]
        logger.info("Queue-based selection: %d pairs from %d pending blocks", len(result), len(pending))

        self._mark_queue_done(pending)
        return result

    def _mark_queue_done(self, block_indices: List[int]) -> None:
        """Mark queue entries as done in a single transaction."""
        if not block_indices:
            return
        try:
            with self.db._write_tx() as conn:
                ph = ",".join("?" for _ in block_indices)
                conn.execute(
                    f"UPDATE consolidation_queue SET status = 'done' WHERE block_index IN ({ph})",
                    tuple(block_indices),
                )
        except Exception as e:
            logger.warning("Failed to mark queue entries as done: %s", e)

    def run_once(self, max_pairs: Optional[int] = None) -> ConsolidationReport:
        """Run a single consolidation batch.

        Args:
            max_pairs: Override config batch_size for this run.
        """
        report = ConsolidationReport()
        effective_max = max_pairs or self.config.batch_size

        # 1. Check LLM availability
        if not self.llm.is_available():
            logger.error("LLM not available at %s", self.config.ollama_url)
            raise RuntimeError(f"LLM unavailable at {self.config.ollama_url}")

        # v5.3.0: Try queue-based incremental mode first
        candidates = self._drain_queue(effective_max)

        # 2. Fall back to full candidate selection if queue is empty
        if not candidates:
            candidates = select_candidates(
                self.db,
                self.state,
                min_cosine_similarity=self.config.min_cosine_similarity,
                max_pairs=effective_max,
            )
        report.total_candidates = len(candidates)

        if not candidates:
            logger.info("No candidate pairs to process")
            return report

        logger.info("Processing %d candidate pairs", len(candidates))

        # 3. Process each pair
        for i, pair in enumerate(candidates):
            if self._shutdown:
                logger.info("Shutdown requested, stopping after %d pairs", i)
                break

            result = self._process_pair(pair, report)
            logger.info(
                "[%d/%d] Block #%d <-> #%d: %s",
                i + 1, len(candidates),
                pair.block_a, pair.block_b,
                result,
            )

        logger.info(report.summary())
        return report

    def _process_pair(self, pair: CandidatePair, report: ConsolidationReport) -> str:
        """Process a single candidate pair. Returns verdict string."""
        now = datetime.now().isoformat()

        try:
            verdict = self.judge.deliberate(pair)
        except Exception as exc:
            logger.warning("LLM error for #%d <-> #%d: %s", pair.block_a, pair.block_b, exc)
            self.state.record_comparison(ComparisonRecord(
                block_a=min(pair.block_a, pair.block_b),
                block_b=max(pair.block_a, pair.block_b),
                cosine_similarity=pair.cosine_similarity,
                verdict="deferred",
                connection_type=None,
                strength=None,
                justification=str(exc),
                association_id=None,
                llm_model=self.config.model,
                prompt_tokens=None,
                completion_tokens=None,
                latency_ms=None,
                compared_at=now,
            ))
            report.deferred += 1
            report.processed += 1
            return "deferred (error)"

        # Determine verdict string
        if verdict.connect:
            verdict_str = "connected"
        else:
            verdict_str = "rejected"

        # Write association if connected
        association_id = None
        if verdict.connect:
            try:
                association_id = self.writer.write(pair.block_a, pair.block_b, verdict)
                if association_id:
                    report.connected += 1
                else:
                    # Already existed or failed
                    verdict_str = "rejected"
                    report.rejected += 1
            except Exception as exc:
                logger.warning("Write error for #%d <-> #%d: %s", pair.block_a, pair.block_b, exc)
                verdict_str = "error"
                report.errors += 1
        else:
            report.rejected += 1

        # Record state
        llm_resp = verdict.llm_response
        self.state.record_comparison(ComparisonRecord(
            block_a=min(pair.block_a, pair.block_b),
            block_b=max(pair.block_a, pair.block_b),
            cosine_similarity=pair.cosine_similarity,
            verdict=verdict_str,
            connection_type=verdict.connection_type,
            strength=verdict.strength,
            justification=verdict.reasoning,
            association_id=association_id,
            llm_model=llm_resp.model if llm_resp else None,
            prompt_tokens=llm_resp.prompt_tokens if llm_resp else None,
            completion_tokens=llm_resp.completion_tokens if llm_resp else None,
            latency_ms=llm_resp.latency_ms if llm_resp else None,
            compared_at=now,
        ))

        if llm_resp:
            report.total_latency_ms += llm_resp.latency_ms
        report.processed += 1

        report.verdicts.append({
            "block_a": pair.block_a,
            "block_b": pair.block_b,
            "cosine_sim": pair.cosine_similarity,
            "verdict": verdict_str,
            "type": verdict.connection_type,
            "strength": verdict.strength,
        })

        return verdict_str

    def run_daemon(self, interval: Optional[int] = None, batch_size: Optional[int] = None) -> None:
        """Run as a daemon, processing batches at regular intervals."""
        effective_interval = interval or self.config.daemon_interval
        effective_batch = batch_size or self.config.batch_size

        # Handle graceful shutdown
        def _signal_handler(signum, frame):
            logger.info("Received signal %d, shutting down gracefully...", signum)
            self._shutdown = True

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)

        logger.info("Starting consolidation daemon (interval=%ds, batch=%d)", effective_interval, effective_batch)

        while not self._shutdown:
            try:
                report = self.run_once(max_pairs=effective_batch)

                if report.total_candidates == 0:
                    # No candidates — wait longer
                    wait = effective_interval * 3
                    logger.info("No candidates, sleeping %ds", wait)
                    self._sleep(wait)
                else:
                    self._sleep(effective_interval)

            except RuntimeError as exc:
                logger.error("Runtime error: %s, retrying in %ds", exc, effective_interval * 2)
                self._sleep(effective_interval * 2)
            except Exception as exc:
                logger.exception("Unexpected error: %s", exc)
                self._sleep(effective_interval)

        logger.info("Daemon stopped")

    def _sleep(self, seconds: int) -> None:
        """Interruptible sleep."""
        for _ in range(seconds):
            if self._shutdown:
                break
            time.sleep(1)

    def close(self) -> None:
        """Clean up resources."""
        self.db.close()
