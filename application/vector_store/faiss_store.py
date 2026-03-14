import os
import pickle
from pathlib import Path
from typing import Any

import cohere
import faiss
import numpy as np

from application.models.schemas import SourceDocument

EMBED_MODEL = "embed-english-v3.0"
EMBED_DIM = 1024
INDEX_PATH = Path("data/faiss.index")
META_PATH = Path("data/faiss_meta.pkl")


class FAISSStore:
    def __init__(self):
        self._co = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))
        self._index = faiss.IndexFlatIP(EMBED_DIM)
        self._metadata: dict[int, dict[str, Any]] = {}

        if INDEX_PATH.exists() and META_PATH.exists():
            self._load()

    def _embed(self, texts: list[str], input_type: str = "search_document") -> np.ndarray:
        response = self._co.embed(
            texts=texts,
            model=EMBED_MODEL,
            input_type=input_type,
            embedding_types=["float"],
        )
        vecs = np.array(response.embeddings.float_, dtype=np.float32)
        faiss.normalize_L2(vecs)
        return vecs

    def add_documents(
        self,
        texts: list[str],
        sources: list[str],
        metadata: list[dict] | None = None,
    ) -> list[int]:
        vecs = self._embed(texts, input_type="search_document")
        start_id = self._index.ntotal
        self._index.add(vecs)
        ids = list(range(start_id, self._index.ntotal))

        for i, fid in enumerate(ids):
            self._metadata[fid] = {
                "text": texts[i],
                "source": sources[i],
                **(metadata[i] if metadata else {}),
            }

        self._save()
        return ids

    def query(self, text: str, k: int = 5) -> list[SourceDocument]:
        if self._index.ntotal == 0:
            return []

        vec = self._embed([text], input_type="search_query")
        scores, indices = self._index.search(vec, min(k, self._index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            meta = self._metadata[int(idx)]
            results.append(
                SourceDocument(
                    text=meta["text"],
                    source=meta.get("source", "unknown"),
                    score=float(score),
                    metadata={k: v for k, v in meta.items() if k not in ("text", "source")},
                )
            )
        return results

    @property
    def size(self) -> int:
        return self._index.ntotal

    def _save(self):
        INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(INDEX_PATH))
        with open(META_PATH, "wb") as f:
            pickle.dump(self._metadata, f)

    def _load(self):
        self._index = faiss.read_index(str(INDEX_PATH))
        with open(META_PATH, "rb") as f:
            self._metadata = pickle.load(f)


store = FAISSStore()
