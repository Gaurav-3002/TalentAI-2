import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import faiss
import numpy as np

logger = logging.getLogger(__name__)


class FAISSService:
    """Simple FAISS wrapper with persistence and metadata storage."""

    def __init__(self, index_path: str, metadata_path: str):
        self.index_path = Path(index_path)
        self.metadata_path = Path(metadata_path)
        self.index: Optional[faiss.Index] = None
        self.dimensions: Optional[int] = None
        self.metadata: Dict[str, Dict[str, Any]] = {}
        os.makedirs(self.index_path.parent, exist_ok=True)

    async def initialize(self):
        try:
            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                self.dimensions = self.index.d
                logger.info(f"[FAISS] Loaded index {self.index_path} (ntotal={self.index.ntotal}, d={self.dimensions})")
                if self.metadata_path.exists():
                    with open(self.metadata_path, "r") as f:
                        self.metadata = json.load(f)
            else:
                logger.info("[FAISS] No existing index found, will create on first add")
        except Exception as e:
            logger.error(f"[FAISS] Initialize failed: {e}")
            self.index = None

    def _ensure_index(self, d: int):
        if self.index is None:
            self.dimensions = d
            # Use inner product with normalized vectors to emulate cosine
            self.index = faiss.IndexFlatIP(d)
            logger.info(f"[FAISS] Created new IndexFlatIP with d={d}")

    def _normalize(self, X: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        return X / norms

    async def add_vectors(self, vectors: np.ndarray, metadata_list: List[Dict[str, Any]]) -> List[int]:
        if vectors is None or vectors.size == 0:
            return []
        if vectors.ndim != 2:
            raise ValueError("vectors must be 2D array [n, d]")
        self._ensure_index(vectors.shape[1])
        vecs = self._normalize(vectors.astype(np.float32))
        start_id = self.index.ntotal if self.index is not None else 0
        self.index.add(vecs)
        ids = list(range(start_id, start_id + vecs.shape[0]))
        for i, m in enumerate(metadata_list):
            self.metadata[str(ids[i])] = m
        return ids

    async def search(self, query: np.ndarray, k: int = 10, threshold: float = 0.0) -> List[Dict[str, Any]]:
        if self.index is None or self.index.ntotal == 0:
            return []
        if query.ndim == 1:
            query = query.reshape(1, -1)
        q = self._normalize(query.astype(np.float32))
        scores, indices = self.index.search(q, k)
        out: List[Dict[str, Any]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            if float(score) < float(threshold):
                continue
            meta = self.metadata.get(str(int(idx)), {})
            out.append({"id": int(idx), "score": float(score), "metadata": meta})
        return out

    async def save(self):
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_path))
            with open(self.metadata_path, "w") as f:
                json.dump(self.metadata, f)
            logger.info(f"[FAISS] Saved index to {self.index_path} and metadata to {self.metadata_path}")

    def stats(self) -> Dict[str, Any]:
        if self.index is None:
            return {"status": "not_initialized"}
        return {"status": "ready", "total_vectors": int(self.index.ntotal), "dimensions": int(self.index.d), "index_type": type(self.index).__name__}