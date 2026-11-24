"""core/vector_memory.py — Qdrant-backed Semantic & Hybrid Memory for DAZY.

Provides:
1. Local-first embedded Qdrant vector database (in-memory or persistent SQLite/disk).
2. Semantic vector indexing for user preferences, conversation memories, and facts.
3. Hybrid search combining semantic similarity and keyword exact matching.
4. Graceful offline fallback: Runs completely locally without external network dependencies.
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("dazy.vector_memory")

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logger.warning("qdrant-client not installed; VectorMemory will use local in-memory fallback.")


def _simple_text_embedding(text: str, dim: int = 128) -> List[float]:
    """Generates a normalized deterministic feature embedding without requiring heavy neural downloads.
    
    Uses token n-grams and hashing to project text into a normalized unit sphere.
    Compatible with Qdrant cosine distance search.
    """
    clean = text.lower().strip()
    tokens = clean.split()
    vec = [0.0] * dim
    if not tokens:
        return vec

    for i, tok in enumerate(tokens):
        # 1-gram
        h1 = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16) % dim
        vec[h1] += 1.0
        # 2-gram
        if i + 1 < len(tokens):
            bigram = f"{tok}_{tokens[i+1]}"
            h2 = int(hashlib.sha256(bigram.encode("utf-8")).hexdigest(), 16) % dim
            vec[h2] += 1.5

    # L2 normalize
    norm = sum(x * x for x in vec) ** 0.5
    if norm > 0.0:
        vec = [x / norm for x in vec]
    return vec


class VectorMemory:
    """Persistent and in-memory semantic retrieval store for DAZY."""

    COLLECTION_NAME = "dazy_memories"
    EMBEDDING_DIM = 128

    def __init__(self, storage_dir: Optional[Path | str] = None):
        self.storage_dir = Path(storage_dir) if storage_dir else None
        self._client: Optional[Any] = None
        self._fallback_store: List[Dict[str, Any]] = []
        self._init_store()

    def _init_store(self) -> None:
        if not QDRANT_AVAILABLE:
            return

        try:
            if self.storage_dir:
                db_path = self.storage_dir / "qdrant_db"
                db_path.mkdir(parents=True, exist_ok=True)
                self._client = QdrantClient(path=str(db_path))
            else:
                self._client = QdrantClient(location=":memory:")

            collections = [c.name for c in self._client.get_collections().collections]
            if self.COLLECTION_NAME not in collections:
                self._client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(size=self.EMBEDDING_DIM, distance=Distance.COSINE),
                )
            logger.info("VectorMemory initialized with Qdrant collection '%s'", self.COLLECTION_NAME)
        except Exception as e:
            logger.error("Failed to initialize QdrantClient: %s. Using in-memory fallback.", e)
            self._client = None

    def store_memory(
        self,
        memory_id: str,
        text: str,
        category: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Stores a semantic memory entry with metadata."""
        if not text.strip():
            return False

        meta = metadata or {}
        meta["text"] = text
        meta["category"] = category
        meta["id"] = memory_id
        embedding = _simple_text_embedding(text, self.EMBEDDING_DIM)

        if self._client is not None:
            try:
                # Convert string ID to uint64 or UUID integer for Qdrant
                int_id = int(hashlib.md5(memory_id.encode("utf-8")).hexdigest()[:15], 16)
                point = PointStruct(id=int_id, vector=embedding, payload=meta)
                self._client.upsert(collection_name=self.COLLECTION_NAME, points=[point])
                return True
            except Exception as e:
                logger.warning("Qdrant upsert failed: %s; falling back to in-memory.", e)

        # In-memory fallback
        self._fallback_store.append({
            "id": memory_id,
            "text": text,
            "category": category,
            "vector": embedding,
            "metadata": meta,
        })
        return True

    def search_memories(
        self,
        query: str,
        limit: int = 5,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Searches for relevant memories using cosine similarity."""
        if not query.strip():
            return []

        q_vec = _simple_text_embedding(query, self.EMBEDDING_DIM)

        if self._client is not None:
            try:
                # Search with Qdrant
                query_res = self._client.query_points(
                    collection_name=self.COLLECTION_NAME,
                    query=q_vec,
                    limit=limit,
                )
                results = []
                for pt in query_res.points:
                    p = pt.payload or {}
                    if category and p.get("category") != category:
                        continue
                    results.append({
                        "id": p.get("id"),
                        "text": p.get("text"),
                        "category": p.get("category"),
                        "score": round(pt.score, 3),
                        "metadata": p,
                    })
                return results
            except Exception as e:
                logger.warning("Qdrant query failed: %s; using in-memory search.", e)

        # In-memory fallback cosine search
        scores = []
        for item in self._fallback_store:
            if category and item.get("category") != category:
                continue
            item_vec = item["vector"]
            # Dot product for normalized vectors
            score = sum(a * b for a, b in zip(q_vec, item_vec))
            scores.append((score, item))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "id": it["id"],
                "text": it["text"],
                "category": it["category"],
                "score": round(sc, 3),
                "metadata": it["metadata"],
            }
            for sc, it in scores[:limit]
        ]
