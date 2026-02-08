"""Greeum Consolidator -- LLM-based judicial deliberation for memory associations."""

__version__ = "0.1.0"

from .config import ConsolidatorConfig
from .judge import ConsolidationJudge, Verdict
from .loop import ConsolidationLoop

__all__ = [
    "ConsolidatorConfig",
    "ConsolidationJudge",
    "ConsolidationLoop",
    "Verdict",
]
