import os

import cohere

from application.agent.state import AgentState
from application.tools.tailvy_tool import search_web as tavily_search
from application.vector_store.faiss_store import store


def search_web(state: AgentState) -> dict:
    results = tavily_search(state["query"], max_results=state.get("max_results", 5))
    return {
        "search_results": results,
        "steps": [f"Searched web for: '{state['query']}' — {len(results)} results found"],
    }


def retrieve_docs(state: AgentState) -> dict:
    docs = store.query(state["query"], k=5)
    return {
        "retrieved_docs": docs,
        "steps": [f"Retrieved {len(docs)} documents from vector store"],
    }


def generate_answer(state: AgentState) -> dict:
    co = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))
    model = os.getenv("COHERE_LLM_MODEL", "command-a-03-2025")

    web_context = "\n\n".join(
        f"[Web] {r['title']}\n{r['content']}" for r in state.get("search_results", [])
    )

    doc_context = "\n\n".join(
        f"[Stored] ({d.source})\n{d.text}" for d in state.get("retrieved_docs", [])
    )

    context = "\n\n---\n\n".join(filter(None, [web_context, doc_context]))

    prompt = (
        f"You are a research assistant. Use the context below to answer the question thoroughly.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {state['query']}\n\n"
        f"Answer:"
    )

    response = co.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    answer = response.message.content[0].text
    return {
        "answer": answer,
        "steps": ["Generated answer using Cohere"],
    }
