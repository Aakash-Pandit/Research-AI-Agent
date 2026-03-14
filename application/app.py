import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from application.agent.graph import agent
from application.models.schemas import (
    AddDocumentRequest,
    AddDocumentResponse,
    HealthResponse,
    ResearchRequest,
    ResearchResponse,
)
from application.vector_store.faiss_store import store

logging.getLogger("onnxruntime").setLevel(logging.ERROR)

app = FastAPI(
    title="Research AI Agent API",
    description="API for Research AI Agent powered by LangGraph, Cohere, FAISS, and Tavily",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Research AI Agent API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        vector_store_size=store.size,
    )


@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest):
    try:
        result = await run_in_threadpool(agent.invoke, {
            "query": request.query,
            "max_results": request.max_results,
            "search_results": [],
            "retrieved_docs": [],
            "steps": [],
            "answer": "",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ResearchResponse(
        query=result["query"],
        answer=result["answer"],
        sources=result.get("retrieved_docs", []),
        steps=result.get("steps", []),
    )


@app.post("/documents", response_model=AddDocumentResponse)
async def add_document(request: AddDocumentRequest):
    try:
        ids = store.add_documents(
            texts=[request.text],
            sources=[request.source],
            metadata=[request.metadata],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return AddDocumentResponse(
        success=True,
        faiss_id=ids[0],
        source=request.source,
    )
