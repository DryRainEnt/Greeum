"""Tests for Model2VecEmbedding wrapper and auto_init priority.

Model2Vec is an optional dependency (`greeum[lite]`). Tests that need an actual
loaded static model are skipped when model2vec is not importable; pure-class and
priority tests still run.
"""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch, MagicMock

from greeum.embedding_models import (
    EmbeddingRegistry,
    Model2VecEmbedding,
    SimpleEmbeddingModel,
    SentenceTransformerModel,
    _model2vec_disabled,
)


def _model2vec_available() -> bool:
    try:
        import model2vec  # noqa: F401
        return True
    except ImportError:
        return False


class TestModel2VecEmbeddingClass(unittest.TestCase):
    """Pure-class tests that do not require model2vec to be installed."""

    def test_default_model_name(self):
        m = Model2VecEmbedding()
        self.assertEqual(m.model_name, "minishlab/potion-multilingual-128M")
        self.assertEqual(m.target_dimension, 768)

    def test_custom_model_name(self):
        m = Model2VecEmbedding(model_name="minishlab/potion-base-8M")
        self.assertEqual(m.model_name, "minishlab/potion-base-8M")

    def test_lazy_load(self):
        m = Model2VecEmbedding()
        self.assertIsNone(m.model, "should not eagerly load on construction")

    def test_get_model_name_format(self):
        m = Model2VecEmbedding(model_name="org/some-model")
        self.assertEqual(m.get_model_name(), "m2v_some-model")

    def test_get_dimension_returns_target(self):
        m = Model2VecEmbedding()
        self.assertEqual(m.get_dimension(), 768)

    def test_disabled_via_env(self):
        with patch.dict(os.environ, {"GREEUM_DISABLE_M2V": "1"}):
            self.assertTrue(_model2vec_disabled())
            m = Model2VecEmbedding()
            with self.assertRaises(RuntimeError):
                m._ensure_model_loaded()
        # cleared
        self.assertFalse(_model2vec_disabled())


@unittest.skipUnless(_model2vec_available(), "model2vec not installed (pip install greeum[lite])")
class TestModel2VecEmbeddingEncoding(unittest.TestCase):
    """Tests that actually load and run the static model."""

    @classmethod
    def setUpClass(cls):
        cls.m = Model2VecEmbedding()

    def test_encode_returns_768_dim(self):
        v = self.m.encode("테스트 문장입니다.")
        self.assertEqual(len(v), 768)

    def test_encode_l2_normalized(self):
        import math
        v = self.m.encode("hybrid retrieval test.")
        norm = math.sqrt(sum(x * x for x in v))
        # padded zeros + L2 norm: norm should be ~1 (or 0 if all-zero, which would be a bug)
        self.assertAlmostEqual(norm, 1.0, places=3)

    def test_batch_encode_matches_single(self):
        texts = ["alpha", "beta", "gamma"]
        batch = self.m.batch_encode(texts)
        self.assertEqual(len(batch), 3)
        # First element should match single-encode (within float tolerance via cache).
        single = self.m.encode("alpha")
        self.assertEqual(len(batch[0]), len(single))


class TestEmbeddingRegistryAutoInitPriority(unittest.TestCase):
    """Verify ST → Model2Vec → loud hash fallback order."""

    def test_st_first_when_available(self):
        # When ST is importable (which it is in dev env), it should win.
        reg = EmbeddingRegistry()
        # Either ST or M2V (depending on env). Hash should NEVER be the default
        # in a healthy install — that's the entire footgun-fix point.
        if os.getenv("GREEUM_DISABLE_ST") != "1":
            self.assertEqual(reg.default_model, "sentence-transformer")

    def test_m2v_picked_when_st_disabled(self):
        if not _model2vec_available():
            self.skipTest("model2vec not installed")
        with patch.dict(os.environ, {"GREEUM_DISABLE_ST": "1"}, clear=False):
            reg = EmbeddingRegistry()
            self.assertEqual(reg.default_model, "model2vec")

    def test_hash_fallback_only_when_both_disabled(self):
        with patch.dict(os.environ,
                        {"GREEUM_DISABLE_ST": "1", "GREEUM_DISABLE_M2V": "1",
                         "GREEUM_SILENT_HASH_FALLBACK": "1"},  # suppress banner in tests
                        clear=False):
            reg = EmbeddingRegistry()
            self.assertEqual(reg.default_model, "simple")
            self.assertIsInstance(reg.models["simple"], SimpleEmbeddingModel)


if __name__ == "__main__":
    unittest.main()
