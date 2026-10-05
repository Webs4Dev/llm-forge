import numpy as np
from sentence_transformers import SentenceTransformer


class SemanticCache:
    def __init__(
        self,
        threshold: float = 0.90,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        self.threshold = threshold
        self.model = SentenceTransformer(model_name)

        self.entries = []

        self.hits = 0
        self.misses = 0

    def _embed(self, text: str) -> np.ndarray:
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
        )

        norm = np.linalg.norm(embedding)

        if norm == 0:
            return embedding

        return embedding / norm

    def _similarity(
        self,
        query_embedding: np.ndarray,
        stored_embedding: np.ndarray,
    ) -> float:
        return float(
            np.dot(
                query_embedding,
                stored_embedding,
            )
        )

    def get(
        self,
        text: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ):
        query_embedding = self._embed(text)

        best_similarity = -1.0
        best_response = None

        for entry in self.entries:
            if entry["model"] != model:
                continue

            if entry["temperature"] != temperature:
                continue

            if entry["max_tokens"] != max_tokens:
                continue

            similarity = self._similarity(
                query_embedding,
                entry["embedding"],
            )

            if similarity > best_similarity:
                best_similarity = similarity
                best_response = entry["response"]

        if best_similarity >= self.threshold:
            self.hits += 1

            return {
                "response": best_response,
                "similarity": best_similarity,
                "hit": True,
            }

        self.misses += 1

        return {
            "response": None,
            "similarity": best_similarity,
            "hit": False,
        }

    def set(
        self,
        text: str,
        response: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ):
        embedding = self._embed(text)

        self.entries.append(
            {
                "embedding": embedding,
                "response": response,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )

    def clear(self):
        self.entries.clear()
        self.hits = 0
        self.misses = 0

    def hit_rate(self):
        total = self.hits + self.misses

        if total == 0:
            return 0.0

        return self.hits / total