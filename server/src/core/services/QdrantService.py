from typing import List, Dict, Any
from pathlib import Path
import uuid
import asyncio
import json

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

from utils.logger import get_logger
from config.Config import CONFIG

log = get_logger("QdrantService")

class QdrantService:
    def __init__(self):
        self.host = CONFIG.qdrant.host
        self.port = CONFIG.qdrant.port
        self.collection_name = CONFIG.qdrant.collection_name
        self.model_name = CONFIG.qdrant.model_name
        self.vector_size = CONFIG.qdrant.vector_size
        self.top_samples = CONFIG.qdrant.top_samples
        self.batch_size = CONFIG.qdrant.batch_size

        try:
            self.client = QdrantClient(host=self.host, port=self.port, timeout=60)
            log.info(f"Подключение к Qdrant установлено: {self.host}:{self.port}")
        except Exception as e:
            log.error(f"Ошибка подключения к Qdrant: {e}")
            raise

        try:
            self.model = SentenceTransformer(self.model_name)
            log.info(f"Модель {self.model_name} загружена успешно")
        except Exception as e:
            log.error(f"Ошибка загрузки модели {self.model_name}: {e}")
            raise

        self._ensure_collection_exists()

    def _ensure_collection_exists(self) -> None:
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                log.info(f"Коллекция '{self.collection_name}' создана")
            else:
                log.info(f"Коллекция '{self.collection_name}' уже существует")

        except Exception as e:
            log.error(f"Ошибка при создании коллекции: {e}")
            raise

    def clear_all_chunks(self):
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            log.info(f"Коллекция '{self.collection_name}' удалена")

            self._ensure_collection_exists()

            log.info("Все чанки успешно удалены из Qdrant")

        except Exception as e:
            log.error(f"Ошибка при очистке чанков: {e}")

    def add_vectorized_chunks(self, chunks_dir):
        try:
            chunks_path = Path(chunks_dir)
            if not chunks_path.exists():
                log.error(f"Директория {chunks_dir} не существует")

            chunk_files = list(chunks_path.glob("*.json"))

            if not chunk_files:
                log.warning(f"Не найдено файлов чанков в директории {chunks_dir}")

            log.info(f"Найдено {len(chunk_files)} файлов чанков")

            points = []

            for chunk_file in chunk_files:
                try:
                    with open(chunk_file, 'r', encoding='utf-8') as f:
                        chunk_data = json.load(f)

                    content = chunk_data.get("content", "")

                    if not content:
                        log.warning(f"Файл {chunk_file.name} имеет пустой content, пропускаем")
                        continue

                    embedding = self.model.encode(content).tolist()

                    point = PointStruct(
                        id=str(uuid.uuid4()),
                        vector=embedding,
                        payload={
                            "text": content,
                            "url": chunk_data.get("url", ""),
                            "title": chunk_data.get("title", ""),
                            "parsed_at": chunk_data.get("parsed_at", ""),
                            "filename": chunk_file.name,
                            "chunk_id": chunk_file.stem
                        }
                    )

                    points.append(point)

                except Exception as e:
                    log.error(f"Ошибка при обработке файла {chunk_file}: {e}")
                    continue

            if not points:
                log.error("Не удалось обработать ни одного файла чанков")
                return

            total_uploaded = 0

            for i in range(0, len(points), self.batch_size):
                batch = points[i:i + self.batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch,
                    wait=True
                )
                total_uploaded += len(batch)
                log.info(f"Загружено {total_uploaded}/{len(points)} чанков")

            log.info(f"Успешно добавлено {len(points)} чанков в Qdrant")

        except Exception as e:
            log.error(f"Ошибка при добавлении чанков: {e}")

    def add_chunks_directly(self, chunks: List[Dict[str, str]]) -> int:
        try:
            points = []

            for chunk_data in chunks:
                content = chunk_data.get("text", "")

                if not content:
                    log.warning("Пропущен чанк с пустым текстом")
                    continue

                embedding = self.model.encode(content).tolist()

                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "text": content,
                        "url": chunk_data.get("url", ""),
                        "title": chunk_data.get("title", ""),
                        "parsed_at": "",
                        "filename": "manual",
                        "chunk_id": str(uuid.uuid4())
                    }
                )

                points.append(point)

            if not points:
                log.error("Не удалось обработать ни одного чанка")
                return 0

            total_uploaded = 0

            for i in range(0, len(points), self.batch_size):
                batch = points[i:i + self.batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch,
                    wait=True
                )
                total_uploaded += len(batch)
                log.info(f"Загружено {total_uploaded}/{len(points)} чанков")

            log.info(f"Успешно добавлено {len(points)} чанков в Qdrant")
            return len(points)

        except Exception as e:
            log.error(f"Ошибка при добавлении чанков: {e}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        try:
            collection_info = self.client.get_collection(self.collection_name)

            log.debug(f"Collection info type: {type(collection_info)}")
            log.debug(f"Collection info attributes: {dir(collection_info)}")

            return {
                "name": self.collection_name,
                "vectors_count": collection_info.vectors_count,
                "points_count": collection_info.points_count,
                "status": collection_info.status
            }
        except Exception as e:
            log.error(f"Ошибка при получении информации о коллекции: {e}")
            return {}

    def search_similar(self, query: str) -> List[Dict[str, Any]]:
        try:
            query_embedding = self.model.encode(query).tolist()

            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=self.top_samples
            )

            results = []
            for result in search_results:
                results.append({
                    "id": result.id,
                    "score": result.score,
                    "text": result.payload.get("text", ""),
                    "link": result.payload.get("url", ""),
                    "title": result.payload.get("title", ""),
                    "parsed_at": result.payload.get("parsed_at", ""),
                    "filename": result.payload.get("filename", ""),
                    "chunk_id": result.payload.get("chunk_id", "")
                })

            return results

        except Exception as e:
            log.error(f"Ошибка при поиске: {e}")
            return []


async def main():
    qdrant_service = QdrantService()

    # chunks_dir = "../../data/chunks"
    # qdrant_service.clear_all_chunks()
    # qdrant_service.add_vectorized_chunks(chunks_dir)
    # print("Чанки успешно добавлены в векторную БД")
    #
    info = qdrant_service.get_collection_info()
    print(info)

    if info.get("points_count", 0) > 0:
        query = "Какие направления есть в компании?"

        results = qdrant_service.search_similar(query)
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result['score']:.3f}, File: {result['filename']}")
            print(f"Text: {result['text'][:100]}...")
            print(f"Link: {result['link']}")
            print(f"Title: {result['title']}")
    else:
        print("Коллекция пуста, иди чини БД")

if __name__ == "__main__":
    asyncio.run(main())