"""Tests for the v5.4 ST default model swap (minilm → multilingual-e5-small).

Two layers:
1. Pure-class tests that verify ``DEFAULT_ST_MODEL`` and ``_determine_query_prefix``
   logic without loading the model. These always run.
2. End-to-end encode tests that load the actual model and verify prefix is
   applied. Skipped when the model is not cached locally and there is no network
   to download it.
"""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from greeum.embedding_models import (
    DEFAULT_ST_MODEL,
    SentenceTransformerModel,
    _determine_query_prefix,
)


class TestDefaultModelChanged(unittest.TestCase):
    """The v5.4 swap landed in the module-level constant."""

    def test_default_constant_is_e5_small(self):
        self.assertEqual(DEFAULT_ST_MODEL, "intfloat/multilingual-e5-small")

    def test_constructor_uses_default(self):
        m = SentenceTransformerModel()
        self.assertEqual(m.model_name, "intfloat/multilingual-e5-small")

    def test_constructor_respects_override(self):
        m = SentenceTransformerModel(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.assertEqual(m.model_name, "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


class TestQueryPrefixDetection(unittest.TestCase):
    """``_determine_query_prefix`` smart default + env override."""

    def setUp(self):
        # Make sure no env override leaks in from the surrounding shell.
        self._saved = os.environ.pop("GREEUM_ST_QUERY_PREFIX", None)

    def tearDown(self):
        if self._saved is not None:
            os.environ["GREEUM_ST_QUERY_PREFIX"] = self._saved

    def test_e5_small_gets_query_prefix(self):
        self.assertEqual(_determine_query_prefix("intfloat/multilingual-e5-small"), "query: ")

    def test_e5_base_gets_query_prefix(self):
        self.assertEqual(_determine_query_prefix("intfloat/e5-base-v2"), "query: ")

    def test_minilm_gets_no_prefix(self):
        self.assertEqual(
            _determine_query_prefix("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"),
            "",
        )

    def test_all_minilm_gets_no_prefix(self):
        self.assertEqual(_determine_query_prefix("sentence-transformers/all-MiniLM-L6-v2"), "")

    def test_env_override_force_prefix(self):
        with patch.dict(os.environ, {"GREEUM_ST_QUERY_PREFIX": "custom: "}, clear=False):
            self.assertEqual(_determine_query_prefix("anything/model"), "custom: ")

    def test_env_override_disable_with_empty_string(self):
        with patch.dict(os.environ, {"GREEUM_ST_QUERY_PREFIX": ""}, clear=False):
            # Even an e5 model gets no prefix when env explicitly empty.
            self.assertEqual(_determine_query_prefix("intfloat/multilingual-e5-small"), "")


class TestSentenceTransformerModelHasPrefixAttr(unittest.TestCase):
    """The wiring on the class itself — without loading the model."""

    def test_default_model_carries_query_prefix(self):
        m = SentenceTransformerModel()
        self.assertEqual(m.query_prefix, "query: ")

    def test_minilm_carries_empty_prefix(self):
        m = SentenceTransformerModel(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.assertEqual(m.query_prefix, "")


def _e5_cached_locally() -> bool:
    """Best-effort check: e5-small weights present in the HF cache."""
    from pathlib import Path
    cache = Path.home() / ".cache" / "huggingface" / "hub" / "models--intfloat--multilingual-e5-small"
    return cache.exists() and any(cache.rglob("*.safetensors")) or any(cache.rglob("pytorch_model.bin"))


@unittest.skipUnless(_e5_cached_locally(), "e5-small not in HF cache; skipping real-encode test")
class TestRealEncodeAppliesPrefix(unittest.TestCase):
    """Verify the encode path produces different vectors when prefix is on vs off
    — proves the prefix actually reaches the underlying model.
    """

    def test_prefix_changes_embedding(self):
        from greeum.embedding_models import SentenceTransformerModel
        # With prefix (default)
        m_pref = SentenceTransformerModel()
        v_pref = m_pref.encode("hybrid retrieval test")

        # Without prefix (env-disabled)
        with patch.dict(os.environ, {"GREEUM_ST_QUERY_PREFIX": ""}, clear=False):
            m_no = SentenceTransformerModel()
            v_no = m_no.encode("hybrid retrieval test")

        # Both 768-dim padded
        self.assertEqual(len(v_pref), 768)
        self.assertEqual(len(v_no), 768)
        # And distinguishable (e5 model responds to the prefix)
        import math
        # Cosine distance between the two should be > 0 (not identical vectors).
        dot = sum(a * b for a, b in zip(v_pref, v_no))
        n1 = math.sqrt(sum(a * a for a in v_pref))
        n2 = math.sqrt(sum(b * b for b in v_no))
        cos = dot / (n1 * n2 + 1e-9)
        # Same content + same model + same dim → very similar but the prefix
        # should perturb the output enough to NOT be ≈ 1.0.
        self.assertLess(cos, 0.999, f"prefix had no effect on the vector (cos={cos:.4f})")


if __name__ == "__main__":
    unittest.main()
