# sleep_tracking_app/rag/vector_db.py
import os
import hashlib
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from ..contracts import ResearchHit, ResearchRetriever

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "sleep_research_articles")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-albert-small-v2")


class SleepVectorDB(ResearchRetriever):
    def __init__(self, host: str = QDRANT_HOST, port: int = QDRANT_PORT, collection: str = QDRANT_COLLECTION):
        self.host = host
        self.port = port
        self.client = None
        self.collection_name = collection
        self.embedding_model = None
        self._initialized = False

    def _ensure_initialized(self):
        """Defer network access and model loading until an operation needs them."""
        if self._initialized:
            return
        from sentence_transformers import SentenceTransformer

        if self.client is None:
            self.client = QdrantClient(host=self.host, port=self.port, timeout=30)
        if self.embedding_model is None:
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self._init_collection()
        self._initialized = True

    def _init_collection(self) -> None:
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if self.collection_name not in collections:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.embedding_model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
                )
        except Exception as e:
            raise RuntimeError(f"Qdrant init failed: {e}")

    def _make_id(self, text_id: str) -> int:
        return int(hashlib.md5(text_id.encode()).hexdigest()[:16], 16)

    def upsert_chunks(self, chunks: List[Dict[str, Any]], batch_size: int = 100):
        """
        chunks: list of {'id': '...', 'text': '...', 'meta': {...}}
        """
        self._ensure_initialized()
        points = []
        for ch in chunks:
            emb = self.embedding_model.encode(ch["text"]).tolist()
            pid = self._make_id(ch["id"])
            points.append(PointStruct(id=pid, vector=emb, payload={**ch.get("meta", {}), "text": ch["text"]}))

            if len(points) >= batch_size:
                self.client.upsert(collection_name=self.collection_name, wait=True, points=points)
                points = []
        if points:
            self.client.upsert(collection_name=self.collection_name, wait=True, points=points)

    def search(self, query: str, *, limit: int = 4) -> list[ResearchHit]:
        self._ensure_initialized()
        q_emb = self.embedding_model.encode(query).tolist()
        if hasattr(self.client, "query_points"):
            results = self.client.query_points(
                collection_name=self.collection_name, query=q_emb, limit=limit,
            ).points
        else:
            results = self.client.search(collection_name=self.collection_name, query_vector=q_emb, limit=limit)
        formatted = []
        for hit in results:
            payload = hit.payload or {}
            formatted.append(ResearchHit(
                text=payload.get("text", ""),
                source=payload.get("source", ""),
                score=float(hit.score),
                chunk_id=str(payload.get("chunk_id", hit.id)),
            ))
        return formatted

    def get_stats(self) -> Dict[str, Any]:
        self._ensure_initialized()
        info = self.client.get_collection(self.collection_name)
        return {"points_count": info.points_count, "collection_name": self.collection_name}
