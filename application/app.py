import logging
import os

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from application.agent.graph import agent
from application.logger import logger
from application.models.schemas import (
    AddDocumentRequest,
    AddDocumentResponse,
    HealthResponse,
    ResearchRequest,
    ResearchResponse,
)
from application.vector_store.faiss_store import store
from auth.dependencies import require_authenticated_user

logging.getLogger("onnxruntime").setLevel(logging.ERROR)

app = FastAPI(
    title="Research AI Agent API",
    description="API for Research AI Agent powered by LangGraph, Cohere, FAISS, and Tavily",
    version="1.0.0",
    dependencies=[Depends(require_authenticated_user)],
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
async def research(request: Request, payload: ResearchRequest):
    user_id = request.user.user_id
    email = request.user._display_name
    logger.info(
        "Research query received",
        extra={"user_id": user_id, "email": email, "query": payload.query},
    )
    try:
        result = await run_in_threadpool(agent.invoke, {
            "query": payload.query,
            "max_results": payload.max_results,
            "search_results": [],
            "retrieved_docs": [],
            "steps": [],
            "answer": "",
        })
    except Exception as e:
        logger.error("Research query failed", extra={"user_id": user_id, "email": email, "error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

    logger.info("Research query completed", extra={"user_id": user_id, "email": email, "query": payload.query})
    return ResearchResponse(
        query=result["query"],
        answer=result["answer"],
        sources=result.get("retrieved_docs", []),
        steps=result.get("steps", []),
    )


@app.delete("/documents", summary="Clear all documents from vector store")
async def clear_documents(request: Request):
    user_id = request.user.user_id
    email = request.user._display_name
    logger.warning("Vector store cleared", extra={"user_id": user_id, "email": email})
    try:
        store.clear()
    except Exception as e:
        logger.error("Failed to clear vector store", extra={"user_id": user_id, "email": email, "error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))
    return {"success": True, "message": "Vector store cleared"}


@app.post("/documents", response_model=AddDocumentResponse)
async def add_document(request: Request, payload: AddDocumentRequest):
    user_id = request.user.user_id
    email = request.user._display_name
    logger.info(
        "Document added to vector store",
        extra={"user_id": user_id, "email": email, "source": payload.source},
    )
    try:
        ids = store.add_documents(
            texts=[payload.text],
            sources=[payload.source],
            metadata=[payload.metadata],
        )
    except Exception as e:
        logger.error("Failed to add document", extra={"user_id": user_id, "email": email, "error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

    return AddDocumentResponse(
        success=True,
        faiss_id=ids[0],
        source=payload.source,
    )
