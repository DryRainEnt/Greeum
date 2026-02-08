"""Consolidator configuration with environment variable support."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConsolidatorConfig:
    """Configuration for the Greeum Consolidator process."""

    db_path: str = ""
    ollama_url: str = "http://localhost:11434"
    model: str = "qwen2.5:7b"
    llm_timeout: float = 60.0
    busy_timeout_ms: int = 30_000
    min_cosine_similarity: float = 0.3
    batch_size: int = 20
    daemon_interval: int = 60
    max_neighbors: int = 5
    ollama_gpu: str = "0"
    embedding_device: str = "cuda:1"

    @classmethod
    def from_env(cls) -> ConsolidatorConfig:
        """Create config from environment variables."""
        db_path = cls._resolve_db_path()
        return cls(
            db_path=db_path,
            ollama_url=os.getenv("GREEUM_OLLAMA_URL", "http://localhost:11434"),
            model=os.getenv("GREEUM_CONSOLIDATOR_MODEL", "qwen2.5:7b"),
            llm_timeout=float(os.getenv("GREEUM_CONSOLIDATOR_LLM_TIMEOUT", "60.0")),
            busy_timeout_ms=int(os.getenv("GREEUM_CONSOLIDATOR_BUSY_TIMEOUT_MS", "30000")),
            min_cosine_similarity=float(os.getenv("GREEUM_CONSOLIDATOR_MIN_SIM", "0.3")),
            batch_size=int(os.getenv("GREEUM_CONSOLIDATOR_BATCH_SIZE", "20")),
            daemon_interval=int(os.getenv("GREEUM_CONSOLIDATOR_INTERVAL", "60")),
            max_neighbors=int(os.getenv("GREEUM_CONSOLIDATOR_MAX_NEIGHBORS", "5")),
            ollama_gpu=os.getenv("GREEUM_CONSOLIDATOR_GPU", "0"),
            embedding_device=os.getenv("GREEUM_CONSOLIDATOR_EMBEDDING_DEVICE", "cuda:1"),
        )

    @staticmethod
    def _resolve_db_path() -> str:
        """Resolve database path: GREEUM_DATA_DIR → ~/.greeum/memory.db."""
        env_dir = os.environ.get("GREEUM_DATA_DIR")
        if env_dir:
            direct = os.path.join(env_dir, "memory.db")
            if os.path.exists(direct):
                return direct
            sub = os.path.join(env_dir, "data", "memory.db")
            if os.path.exists(sub):
                return sub
            return direct

        home = Path.home() / ".greeum" / "memory.db"
        return str(home)
