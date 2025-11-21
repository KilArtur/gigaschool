import numpy as np

from sentence_transformers import CrossEncoder
from typing import List, Tuple

from config.Config import CONFIG
from utils.logger import get_logger

log = get_logger("RerankerService")

class RerankerService:

    def __init__(self):
        self.model_name = CONFIG.reranker.model_name
        self.top_samples = CONFIG.reranker.top_samples

        try:
            self.model = CrossEncoder(self.model_name)
            log.info(f"Модель {self.model_name} загружена успешно")
        except Exception as e:
            log.error(f"Ошибка загрузки модели {self.model_name}: {e}")
            raise

    def rerank(self, query: str, documents: List[str]) -> List[Tuple[int, str, float]]:

        pairs = [[query, doc] for doc in documents]

        scores = self.model.predict(pairs)

        ranked_indices = np.argsort(scores)[::-1]

        results = [
            (idx, documents[idx], scores[idx])
            for idx in ranked_indices[:self.top_samples]
        ]

        log.info("Результаты после реранкинга:")
        for i, (original_idx, doc_text, score) in enumerate(results[:5], 1):
            log.info(f"{i} чанк. [Score: {score:.4f}] (Исходный индекс: {original_idx})")

        return results
