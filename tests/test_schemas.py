import pytest
from pydantic import ValidationError
from application.models.schemas import (
    AddDocumentRequest,
    AddDocumentResponse,
    HealthResponse,
    ResearchRequest,
    ResearchResponse,
    SourceDocument,
)


class TestResearchRequest:
    def test_valid_request(self):
        req = ResearchRequest(query="What is AI?")
        assert req.query == "What is AI?"
        assert req.max_results == 5  # default

    def test_custom_max_results(self):
        req = ResearchRequest(query="test", max_results=10)
        assert req.max_results == 10

    def test_empty_query_fails(self):
        with pytest.raises(ValidationError):
            ResearchRequest(query="")

    def test_max_results_above_20_fails(self):
        with pytest.raises(ValidationError):
            ResearchRequest(query="test", max_results=21)

    def test_max_results_below_1_fails(self):
        with pytest.raises(ValidationError):
            ResearchRequest(query="test", max_results=0)


class TestAddDocumentRequest:
    def test_valid_document(self):
        doc = AddDocumentRequest(text="Some content")
        assert doc.text == "Some content"
        assert doc.source == "manual"  # default
        assert doc.metadata == {}

    def test_empty_text_fails(self):
        with pytest.raises(ValidationError):
            AddDocumentRequest(text="")

    def test_custom_source_and_metadata(self):
        doc = AddDocumentRequest(text="content", source="https://example.com", metadata={"key": "val"})
        assert doc.source == "https://example.com"
        assert doc.metadata == {"key": "val"}


class TestSourceDocument:
    def test_valid_source_document(self):
        doc = SourceDocument(text="text", source="url", score=0.95)
        assert doc.score == 0.95
        assert doc.metadata == {}


class TestHealthResponse:
    def test_valid_health_response(self):
        resp = HealthResponse(status="healthy", vector_store_size=42)
        assert resp.status == "healthy"
        assert resp.vector_store_size == 42


class TestAddDocumentResponse:
    def test_valid_response(self):
        resp = AddDocumentResponse(success=True, faiss_id=7, source="manual")
        assert resp.faiss_id == 7
        assert resp.success is True
