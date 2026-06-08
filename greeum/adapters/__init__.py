"""Framework adapters for Greeum.

Each submodule wraps Greeum's search/memory APIs in the interface expected by a
popular AI framework, so Greeum can drop into existing pipelines without
custom glue:

- ``greeum.adapters.langchain``      — ``GreeumRetriever`` (LangChain ``BaseRetriever``)
- ``greeum.adapters.llamaindex``     — ``GreeumRetriever`` (LlamaIndex ``BaseRetriever``)
- ``greeum.adapters.anthropic_memory`` — ``AnthropicMemoryHandler`` (Anthropic ``memory_20250818`` tool)

Frameworks are optional dependencies. Each submodule imports its framework at
module top and raises a clear ``ImportError`` (with install hint) if the
framework is not installed. The adapter modules are otherwise independent —
``import greeum.adapters.langchain`` does not require LlamaIndex etc.

Install per-adapter:
    pip install greeum[langchain]
    pip install greeum[llamaindex]
    pip install greeum[anthropic]
"""
from __future__ import annotations

__all__: list[str] = [
    # submodule names — explicit re-export deferred to avoid hard deps on
    # optional frameworks at the package import boundary.
    "langchain",
    "llamaindex",
    "anthropic_memory",
]
