"""Consolidation judge — orchestrates deliberation and parses verdicts."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from .candidates import CandidatePair
from .context_gatherer import ContextGatherer
from .llm_client import LLMResponse, OllamaClient
from .prompts import SYSTEM_PROMPT, build_deliberation_prompt

logger = logging.getLogger(__name__)

VALID_TYPES = {"semantic", "causal", "temporal", "entity"}


@dataclass
class Verdict:
    """Parsed verdict from the LLM judge."""
    connect: bool
    connection_type: Optional[str] = None
    strength: Optional[float] = None
    reasoning: str = ""
    raw_response: str = ""
    llm_response: Optional[LLMResponse] = None


class ConsolidationJudge:
    """Orchestrates context gathering → prompt → LLM call → verdict parsing."""

    def __init__(self, gatherer: ContextGatherer, llm: OllamaClient) -> None:
        self.gatherer = gatherer
        self.llm = llm

    def deliberate(self, pair: CandidatePair) -> Verdict:
        """Run judicial deliberation for a candidate pair."""
        ctx_a = self.gatherer.gather(pair.block_a)
        ctx_b = self.gatherer.gather(pair.block_b)

        if not ctx_a or not ctx_b:
            return Verdict(
                connect=False,
                reasoning=f"Could not load context for blocks #{pair.block_a} and/or #{pair.block_b}",
            )

        user_prompt = build_deliberation_prompt(ctx_a, ctx_b, pair.cosine_similarity)
        llm_resp = self.llm.chat(SYSTEM_PROMPT, user_prompt)
        return self._parse_verdict(llm_resp)

    @staticmethod
    def _parse_verdict(llm_resp: LLMResponse) -> Verdict:
        """Parse structured verdict from LLM response text."""
        text = llm_resp.content
        lines = text.strip().split("\n")

        connect = False
        connection_type: Optional[str] = None
        strength: Optional[float] = None
        reasoning = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            upper = line.upper()

            if upper.startswith("VERDICT:"):
                value = line[len("VERDICT:"):].strip().upper()
                connect = value in ("CONNECT", "YES", "TRUE")

            elif upper.startswith("TYPE:"):
                value = line[len("TYPE:"):].strip().lower()
                if value in VALID_TYPES:
                    connection_type = value

            elif upper.startswith("STRENGTH:"):
                try:
                    value = line[len("STRENGTH:"):].strip()
                    strength = float(value)
                    strength = max(0.0, min(1.0, strength))
                except ValueError:
                    pass

            elif upper.startswith("REASONING:"):
                reasoning = line[len("REASONING:"):].strip()

        # If connected but no type, default to semantic
        if connect and not connection_type:
            connection_type = "semantic"

        # If connected but strength too low, reject
        if connect and strength is not None and strength < 0.3:
            connect = False
            reasoning = f"Strength {strength:.2f} below threshold 0.3. " + reasoning

        return Verdict(
            connect=connect,
            connection_type=connection_type,
            strength=strength,
            reasoning=reasoning,
            raw_response=text,
            llm_response=llm_resp,
        )
