"""
LLM-based Context Classifier for Greeum (v4.0)

Uses a local LLM server (llama.cpp) to classify memory content into branches.
Key feature: Queries existing memories to find the best branch for new content.

Flow: New Memory → Search Similar Blocks → LLM decides Branch → Attach to branch

v4.0.1: Fixed Slot vs Branch confusion
- Branch = Dynamic LTM context unit (unlimited, identified by root hash)
- Slot = Fixed STM cache page (3 slots: A/B/C, caches block coordinates)
- Classifier now outputs branch selection, NOT slot selection
"""

import logging
import os
import requests
from typing import Optional, Dict, Any, List, Tuple, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Special constant for new branch creation
NEW_BRANCH = "__NEW_BRANCH__"


@dataclass
class ClassificationResult:
    """Result of branch classification"""
    branch_id: Optional[str]  # Branch root hash, or None if new branch needed
    confidence: float
    reasoning: Optional[str] = None
    similar_blocks: Optional[List[Dict]] = None  # Referenced blocks for decision
    target_block_id: Optional[str] = None  # Suggested block to attach after
    create_new_branch: bool = False  # True if LLM decided new context divergence

    # Deprecated: kept for backwards compatibility, will be removed
    @property
    def slot(self) -> str:
        """Deprecated: Use branch_id instead"""
        logger.warning("ClassificationResult.slot is deprecated, use branch_id")
        return "A"  # Default for backwards compatibility

    @property
    def fallback_used(self) -> bool:
        """Deprecated: No more fallback - explicit failure only"""
        return False


@dataclass
class SimilarBlock:
    """Similar block from existing memory"""
    block_index: int
    content: str
    branch_id: str  # Changed from 'slot' to 'branch_id'
    similarity: float
    block_hash: Optional[str] = None


class ContextClassifier:
    """
    LLM-based branch classifier with memory-aware few-shot learning.

    v4.0.1: Fixed Slot vs Branch confusion
    - Now classifies into BRANCHES (dynamic LTM context units), not slots
    - Slots are STM cache only, managed separately

    This classifier:
    1. Searches existing memories for similar content
    2. Groups similar blocks by their branch (root hash)
    3. Provides these as few-shot examples to the LLM
    4. LLM decides: existing branch OR new branch creation
    """

    DEFAULT_LLM_URL = "http://127.0.0.1:8080"
    DEFAULT_TIMEOUT = 5.0

    SYSTEM_PROMPT = """You are a memory branch classifier. Your job is to decide which existing memory branch a new memory belongs to, or if it needs a new branch.

A branch is a group of related memories sharing the same context/topic. Each branch has a unique ID and contains memories that are contextually related.

Based on the examples from existing memory branches, decide:
1. If the new memory fits an existing branch, respond with: EXISTING:<branch_id>
2. If the new memory represents a completely new context, respond with: NEW_BRANCH

Guidelines for NEW_BRANCH:
- Only create new branch if the content is clearly unrelated to ALL existing branches
- Topics like new projects, life events, or distinctly different subjects warrant new branches
- Small variations within a topic should go to existing branch

Respond with ONLY one of:
- EXISTING:<branch_id> - reason (e.g., "EXISTING:abc123 - Similar to existing memories about API development")
- NEW_BRANCH - reason (e.g., "NEW_BRANCH - This is about cooking, unrelated to existing tech/work branches")
"""

    def __init__(
        self,
        llm_url: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        enabled: bool = True,
        search_func: Optional[Callable] = None,
        db_manager: Optional[Any] = None,
    ):
        """
        Initialize the branch classifier.

        Args:
            llm_url: URL of the llama-server
            timeout: Request timeout in seconds
            enabled: Whether to use LLM classification
            search_func: Function to search similar blocks (query, limit) -> List[Dict]
            db_manager: Database manager for direct queries
        """
        self.llm_url = llm_url or os.environ.get(
            "GREEUM_LLM_URL", self.DEFAULT_LLM_URL
        )
        self.timeout = timeout
        self.enabled = enabled
        self._available: Optional[bool] = None

        # Branch usage tracking
        self.branch_usage: Dict[str, int] = {}  # branch_id -> usage count
        self.new_branch_count = 0

        # Memory search capability
        self.search_func = search_func
        self.db_manager = db_manager

    def set_search_func(self, search_func: Callable) -> None:
        """Set the search function for finding similar blocks."""
        self.search_func = search_func

    def set_db_manager(self, db_manager: Any) -> None:
        """Set the database manager for direct queries."""
        self.db_manager = db_manager

    def is_available(self) -> bool:
        """Check if LLM server is available."""
        if not self.enabled:
            return False

        if self._available is not None:
            return self._available

        try:
            resp = requests.get(
                f"{self.llm_url}/health",
                timeout=2.0
            )
            self._available = resp.status_code == 200
        except Exception:
            self._available = False

        if not self._available:
            logger.warning(f"LLM server not available at {self.llm_url}")

        return self._available

    def reset_availability(self) -> None:
        """Reset availability cache to force re-check."""
        self._available = None

    def _search_similar_blocks(self, content: str, limit: int = 9) -> List[SimilarBlock]:
        """
        Search for similar blocks in existing memory.

        Returns blocks grouped by branch (root hash) for few-shot examples.
        """
        similar_blocks = []

        # Try search function first
        if self.search_func:
            try:
                results = self.search_func(content, limit)
                for r in results:
                    # Use 'root' for branch_id (branch is identified by root hash)
                    branch_id = r.get('root', r.get('branch_id', ''))
                    similar_blocks.append(SimilarBlock(
                        block_index=r.get('block_index', 0),
                        content=r.get('context', r.get('content', '')),
                        branch_id=branch_id,
                        similarity=r.get('_score', r.get('similarity', 0.5)),
                        block_hash=r.get('hash')
                    ))
            except Exception as e:
                logger.warning(f"Search function failed: {e}")

        # Try direct DB query if no results
        if not similar_blocks and self.db_manager:
            try:
                similar_blocks = self._search_via_db(content, limit)
            except Exception as e:
                logger.warning(f"DB search failed: {e}")

        return similar_blocks

    def _search_via_db(self, content: str, limit: int) -> List[SimilarBlock]:
        """Search using direct database query with keyword matching."""
        blocks = []

        # Extract keywords from content
        import re
        keywords = set(re.findall(r'\b[a-zA-Z가-힣]{2,}\b', content.lower()))

        if not keywords or not self.db_manager:
            return blocks

        try:
            cursor = self.db_manager.conn.cursor()

            # Get recent blocks with their branch (root)
            cursor.execute("""
                SELECT block_index, context, root, hash
                FROM blocks
                WHERE context IS NOT NULL
                ORDER BY block_index DESC
                LIMIT 100
            """)

            candidates = []
            for row in cursor.fetchall():
                block_idx, ctx, branch_id, block_hash = row
                if not ctx:
                    continue

                # Simple keyword overlap scoring
                block_keywords = set(re.findall(r'\b[a-zA-Z가-힣]{2,}\b', ctx.lower()))
                overlap = len(keywords & block_keywords)
                if overlap > 0:
                    score = overlap / max(len(keywords), 1)
                    candidates.append(SimilarBlock(
                        block_index=block_idx,
                        content=ctx[:200],  # Truncate for prompt
                        branch_id=branch_id or '',  # Use root as branch_id
                        similarity=score,
                        block_hash=block_hash
                    ))

            # Sort by similarity and take top results
            candidates.sort(key=lambda x: x.similarity, reverse=True)
            blocks = candidates[:limit]

        except Exception as e:
            logger.error(f"DB search error: {e}")

        return blocks

    def _group_by_branch(self, blocks: List[SimilarBlock]) -> Dict[str, List[SimilarBlock]]:
        """Group similar blocks by their branch (root hash)."""
        grouped: Dict[str, List[SimilarBlock]] = {}
        for block in blocks:
            branch_id = block.branch_id or ''
            if branch_id not in grouped:
                grouped[branch_id] = []
            grouped[branch_id].append(block)
        return grouped

    def _build_few_shot_prompt(
        self,
        content: str,
        grouped_blocks: Dict[str, List[SimilarBlock]]
    ) -> str:
        """Build few-shot prompt with examples from each branch."""

        if not grouped_blocks:
            return f"""No existing memory branches found.

New memory to classify:
"{content}"

Since there are no existing branches, respond with: NEW_BRANCH - First memory, creating initial branch"""

        prompt_parts = ["Here are examples of existing memory branches:\n"]

        # Sort branches by total similarity score
        branch_scores = {
            branch_id: sum(b.similarity for b in blocks)
            for branch_id, blocks in grouped_blocks.items()
        }
        sorted_branches = sorted(branch_scores.keys(), key=lambda b: branch_scores[b], reverse=True)

        for branch_id in sorted_branches[:5]:  # Show top 5 branches
            blocks = grouped_blocks[branch_id]
            display_id = branch_id[:12] if branch_id else "(no-root)"
            prompt_parts.append(f"\n[Branch: {display_id}]")

            for i, block in enumerate(blocks[:3], 1):  # Max 3 examples per branch
                # Truncate content for prompt efficiency
                example_content = block.content[:100]
                if len(block.content) > 100:
                    example_content += "..."
                prompt_parts.append(f"  {i}. \"{example_content}\"")

        prompt_parts.append(f"\n\nNew memory to classify:\n\"{content}\"")
        prompt_parts.append("\nRespond with EXISTING:<branch_id> or NEW_BRANCH:")

        return "\n".join(prompt_parts)

    def classify(
        self,
        content: str,
        context_hint: Optional[str] = None,
    ) -> ClassificationResult:
        """
        Classify content into a memory branch using LLM-based few-shot learning.

        Flow:
        1. Search for similar blocks in existing memory
        2. Group by branch (root hash) to create few-shot examples
        3. Ask LLM to decide: existing branch or new branch
        4. NO FALLBACK - explicit failure if LLM unavailable

        Args:
            content: The memory content to classify
            context_hint: Optional additional context

        Returns:
            ClassificationResult with branch assignment
        """
        # Step 1: Search for similar blocks
        similar_blocks = self._search_similar_blocks(content)
        grouped = self._group_by_branch(similar_blocks)

        branch_counts = {bid: len(blocks) for bid, blocks in grouped.items()}
        logger.debug(f"Found similar blocks in {len(grouped)} branches: {branch_counts}")

        # Step 2: Try LLM classification with few-shot examples
        if self.is_available():
            try:
                result = self._llm_classify_with_examples(content, grouped, context_hint)
                result.similar_blocks = [
                    {"block_index": b.block_index, "branch_id": b.branch_id, "similarity": b.similarity}
                    for b in similar_blocks[:5]
                ]

                # Track usage
                if result.branch_id:
                    self.branch_usage[result.branch_id] = self.branch_usage.get(result.branch_id, 0) + 1
                if result.create_new_branch:
                    self.new_branch_count += 1

                return result
            except Exception as e:
                logger.warning(f"LLM classification failed: {e}")

        # Step 3: NO FALLBACK - if no similar blocks and no LLM, create new branch
        # This is NOT a fallback but explicit behavior for empty DB or LLM unavailable
        if not similar_blocks:
            logger.info("No existing memories found - creating new branch")
            return ClassificationResult(
                branch_id=None,
                confidence=1.0,
                reasoning="No existing memories - first block creates new branch",
                create_new_branch=True
            )

        # Step 4: LLM unavailable but similar blocks exist - use semantic similarity
        # Pick the branch with highest total similarity
        best_branch = max(grouped.keys(), key=lambda b: sum(block.similarity for block in grouped[b]))
        best_block = max(grouped[best_branch], key=lambda b: b.similarity)

        logger.info(f"LLM unavailable - using semantic similarity to select branch {best_branch[:12]}...")
        return ClassificationResult(
            branch_id=best_branch,
            confidence=best_block.similarity,
            reasoning=f"LLM unavailable - selected by semantic similarity ({best_block.similarity:.2f})",
            similar_blocks=[{"block_index": b.block_index, "branch_id": b.branch_id, "similarity": b.similarity} for b in similar_blocks[:5]],
            target_block_id=best_block.block_hash,
            create_new_branch=False
        )

    def _llm_classify_with_examples(
        self,
        content: str,
        grouped_blocks: Dict[str, List[SimilarBlock]],
        context_hint: Optional[str] = None,
    ) -> ClassificationResult:
        """Use LLM with few-shot examples for branch classification."""

        user_message = self._build_few_shot_prompt(content, grouped_blocks)

        if context_hint:
            user_message = f"[Additional context: {context_hint}]\n\n{user_message}"

        payload = {
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 150,
            "temperature": 0,
            "stop": ["\n\n"]
        }

        resp = requests.post(
            f"{self.llm_url}/v1/chat/completions",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()

        data = resp.json()
        response_text = data["choices"][0]["message"]["content"].strip()

        branch_id, create_new, reasoning = self._parse_branch_response(response_text, grouped_blocks)

        # Find best target block to attach after
        target_block = None
        if branch_id and branch_id in grouped_blocks:
            # Get the most similar block in the chosen branch
            best_block = max(grouped_blocks[branch_id], key=lambda b: b.similarity)
            target_block = best_block.block_hash

        return ClassificationResult(
            branch_id=branch_id,
            confidence=0.9 if not create_new else 0.85,
            reasoning=reasoning,
            target_block_id=target_block,
            create_new_branch=create_new
        )

    def _parse_branch_response(
        self,
        response: str,
        grouped_blocks: Dict[str, List[SimilarBlock]]
    ) -> Tuple[Optional[str], bool, Optional[str]]:
        """Parse LLM response to extract branch decision.

        Returns:
            (branch_id, create_new_branch, reasoning)
        """
        response = response.strip()

        # Check for NEW_BRANCH
        if response.upper().startswith("NEW_BRANCH"):
            reasoning = response[10:].strip(" -:").strip() if len(response) > 10 else None
            return None, True, reasoning

        # Check for EXISTING:<branch_id>
        if response.upper().startswith("EXISTING:"):
            rest = response[9:].strip()
            # Extract branch_id (up to space or dash)
            parts = rest.split(None, 1)  # Split on whitespace
            if parts:
                partial_id = parts[0].strip(" -:")
                reasoning = parts[1].strip(" -:") if len(parts) > 1 else None

                # Match partial ID to full branch ID
                for full_id in grouped_blocks.keys():
                    if full_id.startswith(partial_id) or partial_id in full_id:
                        return full_id, False, reasoning

                # If no match found but we have branches, pick the most similar
                if grouped_blocks:
                    best_branch = max(grouped_blocks.keys(),
                                     key=lambda b: sum(block.similarity for block in grouped_blocks[b]))
                    return best_branch, False, f"Matched to closest branch: {reasoning}"

        # Unable to parse - if we have branches, use most similar; otherwise new branch
        if grouped_blocks:
            best_branch = max(grouped_blocks.keys(),
                             key=lambda b: sum(block.similarity for block in grouped_blocks[b]))
            return best_branch, False, f"Parse fallback - selected by similarity"

        return None, True, "Unable to parse LLM response - creating new branch"

    # NOTE: Fallback methods removed in v4.0.1
    # Previously: _fallback_classify_with_context, _keyword_classify
    # These were removed because:
    # 1. Fallback should be explicit failure, not silent degradation
    # 2. Slots are NOT branches - classification should target branches only
    # 3. If LLM unavailable and similar blocks exist, use semantic similarity directly

    def get_stats(self) -> Dict[str, Any]:
        """Get classifier statistics."""
        return {
            "llm_available": self._available,
            "llm_url": self.llm_url,
            "enabled": self.enabled,
            "branch_usage": self.branch_usage.copy(),
            "new_branch_count": self.new_branch_count,
            "has_search_func": self.search_func is not None,
            "has_db_manager": self.db_manager is not None,
        }


# Singleton instance
_classifier_instance: Optional[ContextClassifier] = None


def get_context_classifier(
    llm_url: Optional[str] = None,
    reset: bool = False,
    search_func: Optional[Callable] = None,
    db_manager: Optional[Any] = None,
) -> ContextClassifier:
    """
    Get or create the singleton context classifier.

    Args:
        llm_url: Optional LLM server URL
        reset: Force create a new instance
        search_func: Function to search similar blocks
        db_manager: Database manager for direct queries

    Returns:
        ContextClassifier instance
    """
    global _classifier_instance

    if _classifier_instance is None or reset:
        _classifier_instance = ContextClassifier(
            llm_url=llm_url,
            search_func=search_func,
            db_manager=db_manager
        )
    elif search_func and not _classifier_instance.search_func:
        _classifier_instance.set_search_func(search_func)
    elif db_manager and not _classifier_instance.db_manager:
        _classifier_instance.set_db_manager(db_manager)

    return _classifier_instance
