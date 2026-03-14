# Research AI Agent

An autonomous research assistant that combines real-time web search with a persistent vector memory. Given a question, it searches the web via Tavily, retrieves relevant documents from a FAISS vector store, and synthesizes a comprehensive answer using Cohere's LLM — all orchestrated by a LangGraph agent graph.

---

## How It Works

```
User Query
    │
    ▼
[search_web]  ──── Tavily searches the live web
    │
    ▼
[retrieve_docs] ── FAISS queries embedded documents in memory
    │
    ▼
[generate_answer] ─ Cohere synthesizes web + memory context into a final answer
    │
    ▼
Response (answer + sources + reasoning steps)
```

The agent always runs all three steps in sequence. Web results provide fresh information; the vector store provides domain knowledge you've explicitly added over time.

---

## Tech Stack

| Component | Purpose |
|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) | Agent graph orchestration |
| [Cohere](https://cohere.com) | Embeddings (`embed-english-v3.0`) + LLM (`command-a-03-2025`) |
| [FAISS](https://github.com/facebookresearch/faiss) | Local vector store for document retrieval |
| [Tavily](https://tavily.com) | Real-time web search API |
| [FastAPI](https://fastapi.tiangolo.com) | REST API layer |
| Docker | Containerised deployment |

---

## Project Structure

```
Research-AI-Agent/
├── application/
│   ├── agent/
│   │   ├── state.py          # LangGraph AgentState definition
│   │   ├── nodes.py          # search_web, retrieve_docs, generate_answer
│   │   └── graph.py          # Compiled StateGraph
│   ├── vector_store/
│   │   └── faiss_store.py    # FAISS index + Cohere embeddings wrapper
│   ├── tools/
│   │   └── tailvy_tool.py    # Tavily search wrapper
│   ├── models/
│   │   └── schemas.py        # Pydantic request/response models
│   └── app.py                # FastAPI app + route handlers
├── compose/
│   └── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── main.py
└── .env
```

---

## Prerequisites

- Python 3.11+
- A [Cohere API key](https://dashboard.cohere.com/)
- A [Tavily API key](https://app.tavily.com/)

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/your-username/Research-AI-Agent.git
cd Research-AI-Agent
pip install -r requirements.txt
```

### 2. Configure environment

Copy the example and fill in your keys:

```bash
cp .env.example .env
```

```env
API_PORT=8000
COHERE_API_KEY=your-cohere-api-key
COHERE_LLM_MODEL=command-a-03-2025
TAILVY_API_KEY=your-tavily-api-key
```

### 3. Run locally

```bash
uvicorn main:app --reload
```

### 4. Run with Docker

```bash
make start        # docker-compose up
make stop         # docker-compose down
make rebuild      # stop → build → start
```

API will be available at `http://localhost:8000`.

---

## API Reference

### `GET /health`
Returns server status and the number of documents currently indexed in FAISS.

```json
{
  "status": "healthy",
  "vector_store_size": 42
}
```

---

### `POST /research`
Run the full agent pipeline on a research question.

**Request:**
```json
{
  "query": "What are the latest advancements in quantum computing?",
  "max_results": 5
}
```

**Response:**
```json
{
  "query": "What are the latest advancements in quantum computing?",
  "answer": "...",
  "sources": [
    {
      "text": "...",
      "source": "https://...",
      "score": 0.91,
      "metadata": {}
    }
  ],
  "steps": [
    "Searched web for: 'What are the latest advancements in quantum computing?' — 5 results found",
    "Retrieved 3 documents from vector store",
    "Generated answer using Cohere"
  ]
}
```

---

### `POST /documents`
Add a document to the FAISS vector store. The text is embedded via Cohere and persisted to disk so it is available in all future `/research` calls.

**Request:**
```json
{
  "text": "Quantum entanglement allows particles to be correlated regardless of distance.",
  "source": "https://en.wikipedia.org/wiki/Quantum_entanglement",
  "metadata": {
    "topic": "quantum physics"
  }
}
```

**Response:**
```json
{
  "success": true,
  "faiss_id": 0,
  "source": "https://en.wikipedia.org/wiki/Quantum_entanglement"
}
```

Interactive docs available at `http://localhost:8000/docs`.

---

## Use Cases

**Academic research** — Ask complex questions and get answers grounded in both live web results and your own curated document library.

**Competitive intelligence** — Ingest product pages, reports, and articles via `/documents`, then query across all of them with natural language.

**Knowledge base Q&A** — Build a private knowledge base by adding internal documents, then use `/research` to query it alongside current web data.

**News summarisation** — Run research queries on current events; Tavily fetches live results and Cohere synthesises a concise summary.

**Developer research assistant** — Add documentation pages or Stack Overflow answers to the vector store, then ask questions that draw on both stored knowledge and fresh search results.

---

## How FAISS Is Used

FAISS stores only vectors, not text. This project pairs it with a metadata dictionary keyed by FAISS integer ID:

- **Index type:** `IndexFlatIP` (inner product) — equivalent to cosine similarity after L2 normalisation
- **Embeddings:** Cohere `embed-english-v3.0` (1024 dimensions)
- **Normalisation:** vectors are L2-normalised before add and query so scores are in the range 0–1
- **Persistence:** index saved to `data/faiss.index`, metadata to `data/faiss_meta.pkl` — both loaded on startup if present

