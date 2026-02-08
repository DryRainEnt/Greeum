"""Judicial deliberation prompts for memory association."""

from __future__ import annotations

from .context_gatherer import BlockContext

SYSTEM_PROMPT = """\
You are a Memory Association Judge in the Greeum memory system.
Like a court deliberation, carefully examine the evidence and render a verdict:

1. EVIDENCE REVIEW: Read both memory blocks and their existing connections.
2. CONTEXT ANALYSIS: Understand the full context through each block's neighbors.
3. DELIBERATION: Reason whether a meaningful connection exists.
4. VERDICT: Decide on connection, type, and strength.

Connection types:
- semantic: shared meaning, topic, or concept
- causal: one event/fact leads to or causes another
- temporal: time-related proximity or sequence
- entity: shared entities (people, places, projects, tools)

Strength: 0.3-1.0 (do NOT connect if below 0.3)

Rejection criteria:
- Superficial similarity only (e.g., both mention common words)
- Already sufficiently connected through neighbors
- Coincidental co-occurrence without meaningful relation

Response format (EXACTLY these lines):
VERDICT: CONNECT or REJECT
TYPE: semantic/causal/temporal/entity
STRENGTH: 0.0-1.0
REASONING: 2-3 sentences explaining your decision"""


def build_deliberation_prompt(
    ctx_a: BlockContext,
    ctx_b: BlockContext,
    cosine_similarity: float,
) -> str:
    """Build the user prompt for a pair deliberation."""
    parts = [f"COSINE SIMILARITY: {cosine_similarity:.3f}", ""]

    for label, ctx in [("A", ctx_a), ("B", ctx_b)]:
        parts.append("=" * 50)
        parts.append(f"MEMORY BLOCK {label} (#{ctx.block_index})")
        parts.append(f"Timestamp: {ctx.timestamp}")
        if ctx.keywords:
            parts.append(f"Keywords: {', '.join(ctx.keywords)}")
        if ctx.tags:
            parts.append(f"Tags: {', '.join(ctx.tags)}")
        parts.append(f"Importance: {ctx.importance:.2f}")
        if ctx.slot:
            parts.append(f"Slot: {ctx.slot}")
        parts.append(f"Content: {ctx.content}")

        if ctx.associations:
            parts.append(f"\nBlock {label}'s existing connections ({len(ctx.associations)}):")
            for assoc in ctx.associations:
                block_ref = f"Block #{assoc.neighbor_block}" if assoc.neighbor_block is not None else "unknown"
                parts.append(
                    f"  - [{assoc.association_type}, str={assoc.strength:.2f}] "
                    f"{block_ref}: {assoc.content_summary}"
                )
        else:
            parts.append(f"\nBlock {label} has no existing connections.")

    parts.append("=" * 50)
    parts.append("\nBased on the evidence above, render your verdict.")

    return "\n".join(parts)
