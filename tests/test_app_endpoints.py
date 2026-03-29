import pytest
from unittest.mock import MagicMock, patch

from application.models.schemas import SourceDocument


class TestRootEndpoint:
    def test_root_returns_200(self, client_anon):
        resp = client_anon.get("/")
        assert resp.status_code == 200

    def test_root_contains_version(self, client_anon):
        resp = client_anon.get("/")
        assert "version" in resp.json()


class TestHealthEndpoint:
    def test_health_returns_healthy(self, client_anon):
        resp = client_anon.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_health_returns_vector_store_size(self, client_anon):
        resp = client_anon.get("/health")
        assert "vector_store_size" in resp.json()


class TestDocumentsEndpoint:
    def test_add_document_requires_auth(self, client_anon):
        resp = client_anon.post("/documents", json={"text": "hello"})
        assert resp.status_code == 401

    def test_add_document_success(self, client_admin):
        with patch("application.app.store") as mock_store:
            mock_store.add_documents.return_value = [0]
            resp = client_admin.post(
                "/documents",
                json={"text": "some content", "source": "manual"},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["faiss_id"] == 0

    def test_add_document_returns_source(self, client_admin):
        with patch("application.app.store") as mock_store:
            mock_store.add_documents.return_value = [3]
            resp = client_admin.post(
                "/documents",
                json={"text": "content", "source": "https://example.com"},
            )
        assert resp.json()["source"] == "https://example.com"

    def test_clear_documents_requires_auth(self, client_anon):
        resp = client_anon.delete("/documents")
        assert resp.status_code == 401

    def test_clear_documents_success(self, client_admin):
        with patch("application.app.store") as mock_store:
            mock_store.clear.return_value = None
            resp = client_admin.delete("/documents")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_clear_documents_calls_store_clear(self, client_admin):
        with patch("application.app.store") as mock_store:
            mock_store.clear.return_value = None
            client_admin.delete("/documents")
        mock_store.clear.assert_called_once()


class TestResearchEndpoint:
    def test_research_requires_auth(self, client_anon):
        resp = client_anon.post("/research", json={"query": "test"})
        assert resp.status_code == 401

    def test_research_returns_answer(self, client_admin):
        fake_result = {
            "query": "What is AI?",
            "answer": "AI is artificial intelligence.",
            "retrieved_docs": [],
            "steps": ["step1"],
        }
        with patch("application.app.agent") as mock_agent:
            mock_agent.invoke.return_value = fake_result
            resp = client_admin.post("/research", json={"query": "What is AI?"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["answer"] == "AI is artificial intelligence."
        assert body["query"] == "What is AI?"
