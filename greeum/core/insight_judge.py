"""
Unified LLM-based Insight & Branch Judge for Greeum (v5.0)

Combines InsightFilter + ContextClassifier into a single LLM call.
Determines:
1. Is this content worth storing? (insight value)
2. Which branch should it go to? (context classification)

This eliminates pattern-based filtering and provides more accurate,
context-aware decisions.
"""

import logging
import os
import requests
from typing import Optional, Dict, Any, List, Tuple, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class JudgmentResult:
    """Result of unified insight + branch judgment"""
    # Insight judgment
    is_insight: bool
    insight_confidence: float
    insight_reason: Optional[str] = None

    # Branch classification
    branch_id: Optional[str] = None
    create_new_branch: bool = False
    branch_confidence: float = 0.0
    branch_reason: Optional[str] = None
    target_block_id: Optional[str] = None

    # Metadata
    skip_storage: bool = False  # True if content should not be stored
    categories: List[str] = None  # e.g., ["problem_solving", "configuration"]

    def __post_init__(self):
        if self.categories is None:
            self.categories = []
        # If not an insight, skip storage
        if not self.is_insight:
            self.skip_storage = True


@dataclass
class SimilarBlock:
    """Similar block from existing memory"""
    block_index: int
    content: str
    branch_id: str
    similarity: float
    block_hash: Optional[str] = None


class InsightJudge:
    """
    Unified LLM-based judge for insight value and branch classification.

    Single LLM call determines:
    1. Whether content is worth storing (insight vs noise)
    2. Which branch it belongs to (or if new branch needed)

    Benefits:
    - No pattern maintenance required
    - Context-aware decisions
    - Single LLM call for efficiency
    - Consistent judgment criteria
    """

    DEFAULT_LLM_URL = "http://127.0.0.1:8080"
    DEFAULT_TIMEOUT = 5.0

    SYSTEM_PROMPT = """You are a developer memory assistant. Your job is to:
1. Decide if content is worth storing (valuable insight vs noise)
2. If worth storing, decide which memory branch it belongs to

INSIGHT CRITERIA - Store if ANY of these apply:
- Bug fixes or problem solutions (even short: "버그 수정함", "fixed bug")
- Root cause analysis ("원인: X", "because of X")
- Technical warnings/caveats ("주의:", "warning:", "rate limit")
- Configuration or setup notes
- Performance findings
- Technical decisions with rationale
- Lessons learned, discoveries

IMPORTANT: Short sentences CAN be insights!
- "버그 수정함" → YES (indicates bug fix)
- "fixed the auth bug" → YES (documents fix)
- "원인: 환경변수 미설정" → YES (root cause)
- "주의: rate limit 있음" → YES (warning/caveat)

DO NOT STORE (noise) - ONLY these:
- Pure acknowledgments without technical content: "네", "알겠습니다", "ok"
- Pure greetings: "안녕하세요", "hello"
- Pure casual chat: "날씨 좋다", "점심 뭐 먹지"
- Emoticons only: "ㅋㅋ", "ㅎㅎ"
- Single meaningless words

BRANCH DECISION:
- If content relates to existing branch examples, use that branch
- If completely new topic/project, create new branch
- Related topics should stay in same branch

Respond in this EXACT format:
INSIGHT: YES/NO
REASON: <brief reason>
BRANCH: EXISTING:<branch_id>/NEW_BRANCH/NONE
BRANCH_REASON: <why this branch>
CATEGORIES: problem_solving, decision, config, learning, warning, optimization, debugging, root_cause

Examples of INSIGHT=YES:
- "버그 수정함" → YES (bug fix noted)
- "fixed auth bug" → YES (fix documented)
- "배포 실패 원인: 환경변수" → YES (root cause analysis)
- "주의: API rate limit" → YES (technical warning)
- "PostgreSQL 인덱스로 3배 향상" → YES (performance insight)

Examples of INSIGHT=NO:
- "네" → NO (pure acknowledgment)
- "알겠습니다" → NO (pure acknowledgment)
- "오늘 날씨 좋다" → NO (casual chat)
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
        Initialize the InsightJudge.

        Args:
            llm_url: URL of the llama-server
            timeout: Request timeout in seconds
            enabled: Whether to use LLM classification
            search_func: Function to search similar blocks
            db_manager: Database manager for direct queries
        """
        self.llm_url = llm_url or os.environ.get(
            "GREEUM_LLM_URL", self.DEFAULT_LLM_URL
        )
        self.timeout = timeout
        self.enabled = enabled
        self._available: Optional[bool] = None

        self.search_func = search_func
        self.db_manager = db_manager

        # Stats
        self.stats = {
            "total_judged": 0,
            "insights_found": 0,
            "noise_filtered": 0,
            "new_branches": 0,
            "existing_branches": 0,
        }

    def set_search_func(self, search_func: Callable) -> None:
        """Set the search function for finding similar blocks."""
        self.search_func = search_func

    def set_db_manager(self, db_manager: Any) -> None:
        """Set the database manager."""
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

        return self._available

    def judge(
        self,
        content: str,
        context_hint: Optional[str] = None,
    ) -> JudgmentResult:
        """
        Judge content for insight value and branch classification.

        Args:
            content: The content to judge
            context_hint: Optional hint about current context

        Returns:
            JudgmentResult with insight and branch decisions
        """
        self.stats["total_judged"] += 1

        # Quick filter for obviously short content
        if len(content.strip()) < 5:
            self.stats["noise_filtered"] += 1
            return JudgmentResult(
                is_insight=False,
                insight_confidence=1.0,
                insight_reason="Content too short",
                skip_storage=True
            )

        # Check LLM availability - NO FALLBACK, explicit failure
        if not self.is_available():
            raise RuntimeError(
                f"LLM server unavailable at {self.llm_url}. "
                "Cannot judge content without LLM."
            )

        # Search for similar blocks
        similar_blocks = self._search_similar(content)
        grouped_blocks = self._group_by_branch(similar_blocks)

        # Build prompt and call LLM
        try:
            result = self._llm_judge(content, grouped_blocks, context_hint)

            # Update stats
            if result.is_insight:
                self.stats["insights_found"] += 1
                if result.create_new_branch:
                    self.stats["new_branches"] += 1
                else:
                    self.stats["existing_branches"] += 1
            else:
                self.stats["noise_filtered"] += 1

            return result

        except Exception as e:
            # NO FALLBACK - explicit failure
            logger.error(f"LLM judge failed: {e}")
            raise RuntimeError(f"LLM judgment failed: {e}") from e

    def _search_similar(self, content: str, limit: int = 5) -> List[SimilarBlock]:
        """Search for similar existing blocks."""
        if not self.search_func:
            return []

        try:
            results = self.search_func(content, limit)
            blocks = []
            for r in results:
                blocks.append(SimilarBlock(
                    block_index=r.get("block_index", 0),
                    content=r.get("context", r.get("content", ""))[:100],
                    branch_id=r.get("branch_id", r.get("_branch", "unknown")),
                    similarity=r.get("similarity", r.get("_score", 0.5)),
                    block_hash=r.get("hash", r.get("block_hash"))
                ))
            return blocks
        except Exception as e:
            logger.warning(f"Search failed: {e}")
            return []

    def _group_by_branch(self, blocks: List[SimilarBlock]) -> Dict[str, List[SimilarBlock]]:
        """Group similar blocks by their branch ID."""
        grouped: Dict[str, List[SimilarBlock]] = {}
        for block in blocks:
            if block.branch_id not in grouped:
                grouped[block.branch_id] = []
            grouped[block.branch_id].append(block)
        return grouped

    def _build_prompt(
        self,
        content: str,
        grouped_blocks: Dict[str, List[SimilarBlock]],
        context_hint: Optional[str] = None,
    ) -> str:
        """Build the user prompt with few-shot examples."""
        parts = []

        if context_hint:
            parts.append(f"[Current context: {context_hint}]")

        if grouped_blocks:
            parts.append("EXISTING MEMORY BRANCHES:")
            for branch_id, blocks in grouped_blocks.items():
                parts.append(f"\n--- Branch: {branch_id[:12]}... ---")
                for block in blocks[:2]:  # Show up to 2 examples per branch
                    parts.append(f"  • {block.content}")
        else:
            parts.append("No existing memory branches found.")

        parts.append(f"\nNEW CONTENT TO JUDGE:\n{content}")
        parts.append("\nProvide your judgment:")

        return "\n".join(parts)

    def _llm_judge(
        self,
        content: str,
        grouped_blocks: Dict[str, List[SimilarBlock]],
        context_hint: Optional[str] = None,
    ) -> JudgmentResult:
        """Call LLM to judge content."""
        user_message = self._build_prompt(content, grouped_blocks, context_hint)

        payload = {
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": 200,
            "temperature": 0,
            "stop": ["---", "\n\n\n"]
        }

        resp = requests.post(
            f"{self.llm_url}/v1/chat/completions",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()

        data = resp.json()
        response_text = data["choices"][0]["message"]["content"].strip()

        return self._parse_response(response_text, grouped_blocks)

    def _parse_response(
        self,
        response: str,
        grouped_blocks: Dict[str, List[SimilarBlock]],
    ) -> JudgmentResult:
        """Parse LLM response into JudgmentResult."""
        lines = response.strip().split("\n")

        is_insight = False
        insight_reason = None
        branch_id = None
        create_new_branch = False
        branch_reason = None
        categories = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.upper().startswith("INSIGHT:"):
                value = line[8:].strip().upper()
                is_insight = value in ("YES", "TRUE", "1")

            elif line.upper().startswith("REASON:"):
                insight_reason = line[7:].strip()

            elif line.upper().startswith("BRANCH:"):
                value = line[7:].strip()
                if value.upper().startswith("EXISTING:"):
                    partial_id = value[9:].strip()
                    # Match to full branch ID
                    for full_id in grouped_blocks.keys():
                        if full_id.startswith(partial_id) or partial_id in full_id:
                            branch_id = full_id
                            break
                    if not branch_id and grouped_blocks:
                        # Use most similar branch
                        branch_id = max(
                            grouped_blocks.keys(),
                            key=lambda b: sum(blk.similarity for blk in grouped_blocks[b])
                        )
                elif value.upper().startswith("NEW_BRANCH"):
                    create_new_branch = True
                elif value.upper() == "NONE":
                    pass  # Not storing

            elif line.upper().startswith("BRANCH_REASON:"):
                branch_reason = line[14:].strip()

            elif line.upper().startswith("CATEGORIES:"):
                cats = line[11:].strip()
                if cats:
                    categories = [c.strip() for c in cats.split(",") if c.strip()]

        # Find target block for attachment
        target_block = None
        if branch_id and branch_id in grouped_blocks:
            best_block = max(grouped_blocks[branch_id], key=lambda b: b.similarity)
            target_block = best_block.block_hash

        return JudgmentResult(
            is_insight=is_insight,
            insight_confidence=0.9 if is_insight else 0.85,
            insight_reason=insight_reason,
            branch_id=branch_id,
            create_new_branch=create_new_branch,
            branch_confidence=0.9 if branch_id or create_new_branch else 0.5,
            branch_reason=branch_reason,
            target_block_id=target_block,
            categories=categories,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get judgment statistics."""
        total = self.stats["total_judged"]
        return {
            **self.stats,
            "insight_rate": self.stats["insights_found"] / total if total > 0 else 0,
            "noise_rate": self.stats["noise_filtered"] / total if total > 0 else 0,
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self.stats = {
            "total_judged": 0,
            "insights_found": 0,
            "noise_filtered": 0,
            "new_branches": 0,
            "existing_branches": 0,
        }


# Singleton instance
_judge_instance: Optional[InsightJudge] = None


def get_insight_judge(
    llm_url: Optional[str] = None,
    search_func: Optional[Callable] = None,
    db_manager: Optional[Any] = None,
) -> InsightJudge:
    """Get or create the singleton InsightJudge instance."""
    global _judge_instance

    if _judge_instance is None:
        _judge_instance = InsightJudge(
            llm_url=llm_url,
        )

    if search_func:
        _judge_instance.set_search_func(search_func)
    if db_manager:
        _judge_instance.set_db_manager(db_manager)

    return _judge_instance


@dataclass
class StoreResult:
    """Result of store_with_judgment operation"""
    stored: bool
    block_index: Optional[int] = None
    block_hash: Optional[str] = None
    branch_id: Optional[str] = None
    is_new_branch: bool = False
    judgment: Optional[JudgmentResult] = None
    error: Optional[str] = None


def store_with_judgment(
    content: str,
    block_manager: Any,
    importance: float = 0.5,
    keywords: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    context_hint: Optional[str] = None,
    judge: Optional[InsightJudge] = None,
) -> StoreResult:
    """
    Judge content and store if it's an insight.

    Single function that:
    1. Calls InsightJudge to determine if content is worth storing
    2. If YES, stores to appropriate branch via BlockManager
    3. If NO, returns without storing

    NO FALLBACK - raises exception on LLM failure.

    Args:
        content: Content to judge and potentially store
        block_manager: BlockManager instance for storage
        importance: Importance score (0.0-1.0)
        keywords: Optional keywords (auto-extracted if not provided)
        tags: Optional tags
        context_hint: Optional context hint for judgment
        judge: Optional InsightJudge instance (uses singleton if not provided)

    Returns:
        StoreResult with storage outcome

    Raises:
        RuntimeError: If LLM is unavailable or judgment fails
    """
    from ..text_utils import process_user_input, generate_simple_embedding

    # Get or create judge
    if judge is None:
        judge = get_insight_judge()
        # Set up search function from block_manager if available
        if hasattr(block_manager, 'search'):
            judge.set_search_func(
                lambda q, limit: block_manager.search(q, limit=limit)
            )

    # Judge the content (raises on failure - no fallback)
    judgment = judge.judge(content, context_hint=context_hint)

    # If not an insight, don't store
    if not judgment.is_insight:
        logger.info(f"Content filtered: {judgment.insight_reason}")
        return StoreResult(
            stored=False,
            judgment=judgment,
            error=None
        )

    # Process content for storage
    processed = process_user_input(content)

    final_keywords = keywords or processed.get("keywords", [])
    final_tags = tags or []

    # Add judgment categories as tags
    if judgment.categories:
        final_tags.extend([f"insight:{cat}" for cat in judgment.categories])

    embedding = processed.get("embedding") or generate_simple_embedding(content)

    # Determine storage parameters
    storage_kwargs = {
        "context": content,
        "keywords": final_keywords,
        "tags": final_tags,
        "embedding": embedding,
        "importance": importance,
        "metadata": {
            "insight_reason": judgment.insight_reason,
            "branch_reason": judgment.branch_reason,
            "categories": judgment.categories,
            "judged_by": "InsightJudge",
        }
    }

    # Handle branch selection
    if judgment.create_new_branch:
        # New branch will be created by BlockManager
        logger.info("Creating new branch for insight")
    elif judgment.branch_id:
        # Use existing branch
        storage_kwargs["metadata"]["target_branch"] = judgment.branch_id
        if judgment.target_block_id:
            storage_kwargs["metadata"]["target_block"] = judgment.target_block_id
        logger.info(f"Storing to existing branch: {judgment.branch_id[:12]}...")

    # Store the block
    try:
        block = block_manager.add_block(**storage_kwargs)

        if block:
            return StoreResult(
                stored=True,
                block_index=block.get("block_index"),
                block_hash=block.get("hash"),
                branch_id=judgment.branch_id,
                is_new_branch=judgment.create_new_branch,
                judgment=judgment,
            )
        else:
            return StoreResult(
                stored=False,
                judgment=judgment,
                error="BlockManager.add_block returned None"
            )

    except Exception as e:
        logger.error(f"Failed to store block: {e}")
        raise RuntimeError(f"Storage failed: {e}") from e
