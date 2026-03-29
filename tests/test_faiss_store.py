import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from application.vector_store.faiss_store import FAISSStore, EMBED_DIM


def make_fake_embed(n: int = 1) -> np.ndarray:
    """Return L2-normalised random vectors of shape (n, EMBED_DIM)."""
    vecs = np.random.rand(n, EMBED_DIM).astype(np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return vecs / norms


@pytest.fixture
def store(tmp_path, monkeypatch):
    # Redirect disk paths to a fresh temp dir so _load is never triggered
    monkeypatch.setattr("application.vector_store.faiss_store.INDEX_PATH", tmp_path / "faiss.index")
    monkeypatch.setattr("application.vector_store.faiss_store.META_PATH", tmp_path / "faiss_meta.pkl")
    with patch("application.vector_store.faiss_store.cohere.ClientV2"):
        s = FAISSStore()
    # Prevent disk writes during the test
    s._save = lambda: None
    return s


@pytest.fixture
def store_with_docs(store):
    with patch.object(store, "_embed", return_value=make_fake_embed(2)):
        store.add_documents(
            texts=["doc one content", "doc two content"],
            sources=["src1", "src2"],
        )
    return store


class TestFAISSStoreInit:
    def test_empty_store_has_zero_size(self, store):
        assert store.size == 0

    def test_metadata_starts_empty(self, store):
        assert store._metadata == {}


class TestAddDocuments:
    def test_returns_list_of_ids(self, store):
        with patch.object(store, "_embed", return_value=make_fake_embed(1)):
            ids = store.add_documents(texts=["hello world"], sources=["test"])
        assert ids == [0]

    def test_size_increases_after_add(self, store):
        with patch.object(store, "_embed", return_value=make_fake_embed(2)):
            store.add_documents(texts=["a", "b"], sources=["s1", "s2"])
        assert store.size == 2

    def test_metadata_stored_correctly(self, store):
        with patch.object(store, "_embed", return_value=make_fake_embed(1)):
            store.add_documents(
                texts=["test text"],
                sources=["my_source"],
                metadata=[{"key": "value"}],
            )
        assert store._metadata[0]["text"] == "test text"
        assert store._metadata[0]["source"] == "my_source"
        assert store._metadata[0]["key"] == "value"

    def test_ids_are_sequential(self, store):
        with patch.object(store, "_embed", return_value=make_fake_embed(3)):
            ids = store.add_documents(texts=["a", "b", "c"], sources=["s"] * 3)
        assert ids == [0, 1, 2]


class TestQuery:
    def test_empty_store_returns_empty_list(self, store):
        with patch.object(store, "_embed", return_value=make_fake_embed(1)):
            results = store.query("some query")
        assert results == []

    def test_query_returns_source_documents(self, store_with_docs):
        with patch.object(store_with_docs, "_embed", return_value=make_fake_embed(1)):
            results = store_with_docs.query("search query", k=2)
        assert len(results) == 2
        assert all(hasattr(r, "text") for r in results)
        assert all(hasattr(r, "source") for r in results)
        assert all(hasattr(r, "score") for r in results)

    def test_query_respects_k_limit(self, store_with_docs):
        with patch.object(store_with_docs, "_embed", return_value=make_fake_embed(1)):
            results = store_with_docs.query("query", k=1)
        assert len(results) == 1


class TestClear:
    def test_clear_resets_size_to_zero(self, store_with_docs):
        assert store_with_docs.size == 2
        store_with_docs.clear()
        assert store_with_docs.size == 0

    def test_clear_resets_metadata(self, store_with_docs):
        store_with_docs.clear()
        assert store_with_docs._metadata == {}
