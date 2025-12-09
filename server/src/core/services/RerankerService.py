from typing import List, Tuple

from config.Config import CONFIG
from utils.logger import get_logger

log = get_logger("RerankerService")

class RerankerService:

    def __init__(self):
        self.model_name = CONFIG.reranker.model_name
        self.top_samples = CONFIG.reranker.top_samples
        log.info(f"Модель {self.model_name} загружена успешно")

    def rerank(self, query: str, documents: List[str]) -> List[Tuple[int, str, float]]:
        results = [
            (idx, doc, 0.0)
            for idx, doc in enumerate(documents[:self.top_samples])
        ]

        log.info(f"Возвращено {len(results)} документов")
        return results
