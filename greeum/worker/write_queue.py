"""Async write queue utilities for the worker daemon."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Callable, Generic, Optional, TypeVar

T = TypeVar("T")

logger = logging.getLogger("greeum.worker.queue")


class AsyncWriteQueue(Generic[T]):
    """Serialize blocking write operations behind an asyncio-aware lock."""

    def __init__(self, label: str = "default", warn_threshold: Optional[float] = None) -> None:
        self._lock = asyncio.Lock()
        self._label = label
        if warn_threshold is None:
            env_value = os.getenv("GREEUM_WORKER_QUEUE_WARN", "15")
            try:
                warn_threshold = float(env_value)
            except ValueError:
                warn_threshold = 15.0
        self._warn_threshold = max(warn_threshold, 0.0)

    async def run(self, func: Callable[[], T]) -> T:
        """Run *func* under the queue lock, offloading to the default executor."""
        if not callable(func):  # pragma: no cover - defensive
            raise TypeError("func must be callable")

        start = time.perf_counter()
        async with self._lock:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, func)
        elapsed = time.perf_counter() - start

        if self._warn_threshold and elapsed > self._warn_threshold:
            logger.warning(
                "AsyncWriteQueue[%s] operation took %.2fs (threshold %.2fs)",
                self._label,
                elapsed,
                self._warn_threshold,
            )

        return result


__all__ = ["AsyncWriteQueue"]
