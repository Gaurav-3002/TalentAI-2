import os
import logging
from typing import List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Embeddings via Emergent Integrations using EMERGENT_LLM_KEY.
    Implements simple REST calls as per integration playbook.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-large"):
        self.api_key = api_key or os.environ.get("EMERGENT_LLM_KEY")
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY is required for embedding generation")
        self.model = model
        self.base_url = "https://api.emergent-integrations.com/v1"
        self.dimensions: Optional[int] = None
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/models", headers=self.headers, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _embeddings_call(self, texts: List[str], dimensions: Optional[int] = None) -> List[List[float]]:
        payload = {"model": self.model, "input": texts}
        if dimensions:
            payload["dimensions"] = dimensions
        resp = requests.post(
            f"{self.base_url}/embeddings",
            headers=self.headers,
            json=payload,
            timeout=45,
        )
        resp.raise_for_status()
        data = resp.json()
        vectors = [item["embedding"] for item in data.get("data", [])]
        if not self.dimensions and vectors:
            self.dimensions = len(vectors[0])
            logger.info(f"[EmbeddingService] Auto-detected embedding dims: {self.dimensions}")
        return vectors

    async def generate_embeddings(self, texts: List[str], dimensions: Optional[int] = None) -> List[List[float]]:
        if not texts:
            return []
        try:
            return self._embeddings_call(texts, dimensions)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    async def generate_single_embedding(self, text: str, dimensions: Optional[int] = None) -> List[float]:
        vectors = await self.generate_embeddings([text], dimensions)
        return vectors[0] if vectors else []

    def get_dimensions(self) -> Optional[int]:
        return self.dimensions