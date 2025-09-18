"""Compatibility helpers for anyio across versions."""

from __future__ import annotations

import sys
import types
from typing import Type

try:
    import anyio
except ImportError as exc:  # pragma: no cover - enforced by caller before import
    raise ImportError(
        "anyio is required. Install with: pip install anyio>=3.0"
    ) from exc


def _resolve_cancelled_error() -> Type[BaseException]:
    cancel_cls = getattr(anyio, "CancelledError", None)
    if isinstance(cancel_cls, type):
        return cancel_cls

    get_cls = getattr(anyio, "get_cancelled_exc_class", None)
    if callable(get_cls):
        try:
            cancel_cls = get_cls()
        except Exception:  # pragma: no cover - guard against buggy backends
            cancel_cls = None
        else:
            if isinstance(cancel_cls, type):
                return cancel_cls

    class cancel_cls(BaseException):
        """Fallback CancelledError compatible with BaseException."""

        pass

    return cancel_cls


def _resolve_end_of_stream() -> Type[BaseException]:
    eos_cls = getattr(anyio, "EndOfStream", None)
    if isinstance(eos_cls, type):
        return eos_cls

    class eos_cls(Exception):
        """Fallback EndOfStream compatible with Exception."""

        pass

    return eos_cls


CancelledError = _resolve_cancelled_error()
EndOfStream = _resolve_end_of_stream()


def ensure_anyio_exceptions_module() -> None:
    """Ensure ``anyio.exceptions`` exists with required attributes.

    Older anyio builds may not expose the ``exceptions`` module attribute.
    We provide a lightweight shim so imports and attribute access succeed.
    """

    existing = getattr(anyio, "exceptions", None)
    if isinstance(existing, types.ModuleType):
        if not hasattr(existing, "CancelledError"):
            setattr(existing, "CancelledError", CancelledError)
        if not hasattr(existing, "EndOfStream"):
            setattr(existing, "EndOfStream", EndOfStream)
        sys.modules.setdefault("anyio.exceptions", existing)
        return

    shim = types.ModuleType("anyio.exceptions")
    shim.CancelledError = CancelledError
    shim.EndOfStream = EndOfStream
    anyio.exceptions = shim  # type: ignore[attr-defined]
    sys.modules["anyio.exceptions"] = shim


ensure_anyio_exceptions_module()

__all__ = ["CancelledError", "EndOfStream", "ensure_anyio_exceptions_module"]
