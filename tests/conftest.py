import importlib.machinery
import importlib.util
import os
import sys
import types
from pathlib import Path
from typing import Optional

# Ensure repository root and tests package are importable
workspace_root = Path(__file__).resolve().parents[1]
tests_root = Path(__file__).resolve().parent
for path in (str(workspace_root), str(tests_root)):
    if path not in sys.path:
        sys.path.insert(0, path)

# Force HOME to a writable location inside the repository to satisfy cache writes
os.environ["HOME"] = str(workspace_root)

if importlib.util.find_spec("sentence_transformers") is None:
    import numpy as np

    stub_module = types.ModuleType("sentence_transformers")
    stub_module.__spec__ = importlib.machinery.ModuleSpec("sentence_transformers", loader=None)

    class _StubSentenceTransformer:
        is_stub = True

        def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_folder: Optional[str] = None):
            self.model_name = model_name
            self.cache_folder = cache_folder
            self._dimension = 768

        def get_sentence_embedding_dimension(self) -> int:
            return self._dimension

        def encode(self, texts, convert_to_numpy: bool = False):
            def _encode(text: str):
                seed = abs(hash(text)) % 1_000_000
                vector = [((seed + i) % 100) / 100.0 for i in range(self._dimension)]
                if convert_to_numpy:
                    return np.array(vector, dtype=float)
                return vector

            if isinstance(texts, str):
                return _encode(texts)
            return [_encode(t) for t in texts]

    stub_module.SentenceTransformer = _StubSentenceTransformer
    sys.modules["sentence_transformers"] = stub_module
