"""Block context gathering for judicial deliberation."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .db import ConsolidatorDB

logger = logging.getLogger(__name__)


@dataclass
class AssociationInfo:
    """Summary of a neighboring association."""
    association_type: str
    strength: float
    neighbor_block: Optional[int]
    content_summary: str


@dataclass
class BlockContext:
    """Full context for a single block, used as evidence in deliberation."""
    block_index: int
    content: str
    keywords: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    importance: float = 0.5
    timestamp: str = ""
    slot: Optional[str] = None
    associations: List[AssociationInfo] = field(default_factory=list)


class ContextGatherer:
    """Gathers block context including content and neighbor associations."""

    def __init__(self, db: ConsolidatorDB, max_neighbors: int = 5) -> None:
        self.db = db
        self.max_neighbors = max_neighbors

    def gather(self, block_index: int) -> Optional[BlockContext]:
        """Gather full context for a block."""
        block = self.db.get_block_content(block_index)
        if not block:
            logger.warning("Block #%d not found", block_index)
            return None

        # Gather neighbor associations
        associations: List[AssociationInfo] = []
        node_id = self.db.get_node_id_for_block(block_index)
        if node_id:
            raw_assocs = self.db.get_node_associations_with_content(node_id, self.max_neighbors)
            for a in raw_assocs:
                associations.append(AssociationInfo(
                    association_type=a["association_type"],
                    strength=a["strength"],
                    neighbor_block=a["neighbor_block"],
                    content_summary=a["content_summary"],
                ))

        return BlockContext(
            block_index=block["block_index"],
            content=block["context"],
            keywords=block["keywords"],
            tags=block["tags"],
            importance=block["importance"],
            timestamp=block["timestamp"],
            slot=block["slot"],
            associations=associations,
        )
