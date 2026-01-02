"""
Insight Filter for Greeum v5.0
Filters content to identify valuable insights worth storing

Design principle: 모든 내용 저장 (X) → 인사이트만 선별 저장 (O)

Insight patterns:
- Problem solutions ("해결했다", "fix", "solved")
- Decision rationale ("선택한 이유", "decided", "chose")
- Configuration changes ("설정", "config", "setup")
- Lessons learned ("배웠다", "learned", "realized")
- Warnings/caveats ("주의", "warning", "careful")
"""

import re
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple, Pattern

logger = logging.getLogger(__name__)


@dataclass
class FilterResult:
    """Result of insight filtering"""
    is_insight: bool
    confidence: float
    matched_pattern: Optional[str] = None
    reason: Optional[str] = None


class InsightFilter:
    """
    Pattern-based filter to identify valuable insights.

    Filters out:
    - Simple greetings
    - Short confirmations
    - Low-value content

    Keeps:
    - Problem solutions
    - Decision rationales
    - Configuration details
    - Lessons learned
    """

    # Insight patterns (Korean + English)
    INSIGHT_PATTERNS: List[Tuple[str, str]] = [
        # Problem solving
        (r"해결[했됐하]", "problem_solved_ko"),
        (r"고[쳤침치]", "fixed_ko"),
        (r"수정[했한]", "modified_ko"),
        (r"[Ff]ix(ed)?", "fix_en"),
        (r"[Ss]olv(ed|ing)", "solve_en"),
        (r"[Rr]esolv(ed|ing)", "resolve_en"),

        # Decision making
        (r"선택[했한].*이유", "decision_reason_ko"),
        (r"결정[했한]", "decided_ko"),
        (r"[Dd]ecid(ed|ing)", "decide_en"),
        (r"[Cc]hos(e|en)", "chose_en"),
        (r"[Ss]elect(ed|ing)", "select_en"),
        (r"이유는", "reason_ko"),

        # Configuration/Setup
        (r"설정[했한]", "configured_ko"),
        (r"구성[했한]", "composed_ko"),
        (r"[Cc]onfig(ur)?", "config_en"),
        (r"[Ss]etup", "setup_en"),
        (r"[Ii]nstall(ed)?", "install_en"),

        # Learning
        (r"배[웠움운]", "learned_ko"),
        (r"알게.*됐", "realized_ko"),
        (r"[Ll]earn(ed|ing)", "learn_en"),
        (r"[Rr]ealiz(ed|ing)", "realize_en"),
        (r"[Dd]iscover(ed)?", "discover_en"),

        # Warnings/Caveats
        (r"주의.*해야", "caution_ko"),
        (r"조심", "careful_ko"),
        (r"[Ww]arn(ing)?", "warning_en"),
        (r"[Cc]aution", "caution_en"),
        (r"[Cc]areful", "careful_en"),
        (r"[Nn]ote:", "note_en"),

        # Implementation
        (r"구현[했한]", "implemented_ko"),
        (r"적용[했한]", "applied_ko"),
        (r"[Ii]mplement(ed)?", "implement_en"),
        (r"[Aa]ppl(ied|y)", "apply_en"),
        (r"[Cc]reat(ed|ing)", "create_en"),

        # Error handling
        (r"에러.*발생", "error_occurred_ko"),
        (r"오류.*해결", "error_fixed_ko"),
        (r"[Ee]rror", "error_en"),
        (r"[Bb]ug", "bug_en"),
        (r"[Ii]ssue", "issue_en"),

        # Performance
        (r"최적화", "optimized_ko"),
        (r"성능.*개선", "performance_ko"),
        (r"[Oo]ptimiz", "optimize_en"),
        (r"[Pp]erformance", "performance_en"),
        (r"[Ii]mprov(ed|ing)", "improve_en"),
    ]

    # Skip patterns (low-value content)
    SKIP_PATTERNS: List[Tuple[str, str]] = [
        (r"^안녕", "greeting_ko"),
        (r"^네[,.\s]", "confirm_ko"),
        (r"^알겠[습어]", "understood_ko"),
        (r"^감사", "thanks_ko"),
        (r"^ㅇㅋ", "ok_ko"),
        (r"^[Hh]ello", "hello_en"),
        (r"^[Hh]i[,.\s]", "hi_en"),
        (r"^[Oo]k[,.\s]?$", "ok_en"),
        (r"^[Yy]es[,.\s]?$", "yes_en"),
        (r"^[Nn]o[,.\s]?$", "no_en"),
        (r"^[Tt]hanks?", "thanks_en"),
        (r"^[Ss]ure[,.\s]?$", "sure_en"),
        (r"^[Gg]ot it", "got_it_en"),
    ]

    MIN_CONTENT_LENGTH = 20  # Minimum characters for insight
    MIN_WORD_COUNT = 3  # Minimum words for insight

    def __init__(
        self,
        min_length: int = MIN_CONTENT_LENGTH,
        min_words: int = MIN_WORD_COUNT,
        custom_patterns: Optional[List[Tuple[str, str]]] = None
    ):
        """
        Initialize InsightFilter.

        Args:
            min_length: Minimum content length
            min_words: Minimum word count
            custom_patterns: Additional insight patterns
        """
        self.min_length = min_length
        self.min_words = min_words

        # Compile patterns
        self.insight_patterns: List[Tuple[Pattern, str]] = [
            (re.compile(p, re.IGNORECASE), name)
            for p, name in self.INSIGHT_PATTERNS
        ]

        self.skip_patterns: List[Tuple[Pattern, str]] = [
            (re.compile(p, re.IGNORECASE), name)
            for p, name in self.SKIP_PATTERNS
        ]

        # Add custom patterns
        if custom_patterns:
            for pattern, name in custom_patterns:
                self.insight_patterns.append(
                    (re.compile(pattern, re.IGNORECASE), name)
                )

        # Metrics
        self.metrics = {
            "total_checked": 0,
            "passed": 0,
            "filtered_short": 0,
            "filtered_skip_pattern": 0,
            "passed_pattern_match": 0,
            "passed_length_only": 0
        }

    def filter(self, content: str, force: bool = False) -> FilterResult:
        """
        Check if content is a valuable insight.

        Args:
            content: Content to check
            force: If True, skip filtering and always pass

        Returns:
            FilterResult with decision
        """
        self.metrics["total_checked"] += 1

        # Force pass
        if force:
            self.metrics["passed"] += 1
            return FilterResult(
                is_insight=True,
                confidence=1.0,
                reason="forced"
            )

        content = content.strip()

        # Length check
        if len(content) < self.min_length:
            self.metrics["filtered_short"] += 1
            return FilterResult(
                is_insight=False,
                confidence=0.9,
                reason=f"too short ({len(content)} < {self.min_length})"
            )

        # Word count check
        words = content.split()
        if len(words) < self.min_words:
            self.metrics["filtered_short"] += 1
            return FilterResult(
                is_insight=False,
                confidence=0.9,
                reason=f"too few words ({len(words)} < {self.min_words})"
            )

        # Skip pattern check
        for pattern, name in self.skip_patterns:
            if pattern.search(content):
                self.metrics["filtered_skip_pattern"] += 1
                return FilterResult(
                    is_insight=False,
                    confidence=0.85,
                    matched_pattern=name,
                    reason=f"skip pattern matched: {name}"
                )

        # Insight pattern check
        for pattern, name in self.insight_patterns:
            if pattern.search(content):
                self.metrics["passed"] += 1
                self.metrics["passed_pattern_match"] += 1
                return FilterResult(
                    is_insight=True,
                    confidence=0.9,
                    matched_pattern=name,
                    reason=f"insight pattern matched: {name}"
                )

        # Default: pass if content is substantial enough
        if len(content) >= self.min_length * 2:
            self.metrics["passed"] += 1
            self.metrics["passed_length_only"] += 1
            return FilterResult(
                is_insight=True,
                confidence=0.6,
                reason="substantial content length"
            )

        # Moderate length, no clear pattern - still pass with lower confidence
        self.metrics["passed"] += 1
        return FilterResult(
            is_insight=True,
            confidence=0.5,
            reason="default pass - moderate content"
        )

    def is_insight(self, content: str) -> bool:
        """Simple boolean check if content is insight."""
        return self.filter(content).is_insight

    def add_pattern(self, pattern: str, name: str) -> None:
        """Add a custom insight pattern."""
        self.insight_patterns.append(
            (re.compile(pattern, re.IGNORECASE), name)
        )

    def add_skip_pattern(self, pattern: str, name: str) -> None:
        """Add a custom skip pattern."""
        self.skip_patterns.append(
            (re.compile(pattern, re.IGNORECASE), name)
        )

    def get_stats(self) -> dict:
        """Get filter statistics."""
        total = self.metrics["total_checked"]
        return {
            **self.metrics,
            "pass_rate": self.metrics["passed"] / total if total else 0,
            "pattern_match_rate": self.metrics["passed_pattern_match"] / self.metrics["passed"]
                if self.metrics["passed"] else 0
        }

    def reset_stats(self) -> None:
        """Reset metrics."""
        for key in self.metrics:
            self.metrics[key] = 0


# Convenience function
def is_insight(content: str, min_length: int = 20) -> bool:
    """
    Quick check if content is worth storing as insight.

    Args:
        content: Content to check
        min_length: Minimum length threshold

    Returns:
        True if content appears to be valuable insight
    """
    filter_instance = InsightFilter(min_length=min_length)
    return filter_instance.is_insight(content)
