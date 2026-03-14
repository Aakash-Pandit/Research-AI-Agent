from typing import Any
from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Research question to investigate")
    max_results: int = Field(default=5, ge=1, le=20, description="Max web search results to fetch")


class AddDocumentRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Document text to embed and store")
    source: str = Field(default="manual", description="Origin of the document (e.g. URL, filename)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extra metadata to attach")


class SourceDocument(BaseModel):
    text: str
    source: str
    score: float = Field(description="Cosine similarity score (0–1, higher = more relevant)")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResearchResponse(BaseModel):
    query: str
    answer: str
    sources: list[SourceDocument] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list, description="Agent reasoning steps")


class AddDocumentResponse(BaseModel):
    success: bool
    faiss_id: int
    source: str


class HealthResponse(BaseModel):
    status: str
    vector_store_size: int = Field(description="Number of documents indexed in FAISS")
