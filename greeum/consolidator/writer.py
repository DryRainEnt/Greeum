"""Association writer — records consolidator-created connections."""

from __future__ import annotations

import logging
from typing import Optional

from .db import ConsolidatorDB
from .judge import Verdict

logger = logging.getLogger(__name__)


class AssociationWriter:
    """Writes new associations discovered by the consolidator."""

    def __init__(self, db: ConsolidatorDB) -> None:
        self.db = db

    def write(
        self,
        block_a: int,
        block_b: int,
        verdict: Verdict,
    ) -> Optional[str]:
        """Create an association between two blocks based on the verdict.

        Returns the association_id if created, None if skipped.
        """
        if not verdict.connect:
            return None

        # Get or create block content for nodes
        content_a = self.db.get_block_content(block_a)
        content_b = self.db.get_block_content(block_b)

        if not content_a or not content_b:
            logger.warning("Cannot write association: missing block content for #%d and/or #%d", block_a, block_b)
            return None

        # Ensure memory_nodes exist
        node_a = self.db.create_node_if_needed(block_a, content_a["context"])
        node_b = self.db.create_node_if_needed(block_b, content_b["context"])

        # Check if association already exists
        if self.db.association_exists(node_a, node_b):
            logger.debug("Association already exists between %s and %s, skipping", node_a, node_b)
            return None

        # Create the association
        metadata = {
            "source": "consolidator",
            "reasoning": verdict.reasoning,
        }
        if verdict.llm_response:
            metadata["llm_model"] = verdict.llm_response.model

        association_id = self.db.create_association(
            source_node_id=node_a,
            target_node_id=node_b,
            association_type=verdict.connection_type or "semantic",
            strength=verdict.strength or 0.5,
            metadata=metadata,
        )

        logger.info(
            "Created association %s: Block #%d <-> #%d (%s, %.2f)",
            association_id, block_a, block_b,
            verdict.connection_type, verdict.strength or 0.5,
        )
        return association_id
