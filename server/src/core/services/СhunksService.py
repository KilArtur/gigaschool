import os
import json
import asyncio
from pathlib import Path
from sentence_transformers import SentenceTransformer

from utils.logger import get_logger
from config.Config import CONFIG

log = get_logger("ChunksService")


class ChunkProcessor:
    def __init__(self):
        self.chunk_size = CONFIG.chunks.chunk_size
        self.overlap = CONFIG.chunks.overlap
        self.model_name = CONFIG.chunks.model_name
        log.info(f"Загрузка модели {self.model_name}...")
        self.encoder = SentenceTransformer(self.model_name)
        self.encoder.max_seq_length = CONFIG.chunks.encoder_max_seq_length
        log.info(f"Модель загружена. Max sequence length: {self.encoder.get_max_seq_length()}")

    def count_tokens(self, text: str) -> int:
        tokens = self.encoder.tokenizer.encode(text)
        return len(tokens)

    def create_chunks_with_overlap(self, text: str) -> list[str]:
        words = text.split()
        chunks = []
        current_chunk = []
        current_tokens = 0

        for word in words:
            word_with_space = word + " "
            word_tokens = self.count_tokens(word_with_space)

            if current_tokens + word_tokens > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(chunk_text)

                overlap_words = []
                overlap_tokens = 0
                for w in reversed(current_chunk):
                    w_with_space = w + " "
                    w_tokens = self.count_tokens(w_with_space)
                    if overlap_tokens + w_tokens > self.overlap:
                        break
                    overlap_words.insert(0, w)
                    overlap_tokens += w_tokens

                current_chunk = overlap_words
                current_tokens = overlap_tokens

            current_chunk.append(word)
            current_tokens += word_tokens

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        log.info(f"Создано {len(chunks)} чанков")
        return chunks

    def process_kb_page(self, kb_page_path: str) -> list[dict]:
        try:
            with open(kb_page_path, 'r', encoding='utf-8') as f:
                page_data = json.load(f)

            url = page_data.get('url', '')
            title = page_data.get('title', '')
            content = page_data.get('text', page_data.get('content', ''))

            token_count = self.count_tokens(content)
            log.info(f"Обработка {Path(kb_page_path).name}: {token_count} токенов")

            if token_count < self.chunk_size:
                log.info(f"Текст меньше {self.chunk_size} токенов, создается один чанк")
                return [{
                    'url': url,
                    'title': title,
                    'content': content
                }]

            chunks = self.create_chunks_with_overlap(content)

            result = []
            for chunk_text in chunks:
                result.append({
                    'url': url,
                    'title': title,
                    'content': chunk_text,
                })

            return result

        except Exception as e:
            log.error(f"Ошибка при обработке {kb_page_path}: {e}")
            raise

    def save_chunks(self, chunks: list[dict], output_dir: str, base_name: str):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for i, chunk_data in enumerate(chunks, 1):
            chunk_filename = output_path / f"{base_name}_chunk_{i}.json"
            with open(chunk_filename, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, ensure_ascii=False, indent=2)

            token_count = self.count_tokens(chunk_data['content'])
            log.info(f"Сохранен {chunk_filename.name}: {token_count} токенов")

    async def process_kb_directory(self, kb_dir: str, output_dir: str):
        kb_path = Path(kb_dir)

        if not kb_path.exists():
            log.error(f"Директория {kb_dir} не существует")
            return

        kb_files = sorted(kb_path.glob("kb_page_*.json"))
        log.info(f"Найдено {len(kb_files)} файлов для обработки")

        for kb_file in kb_files:
            try:
                log.info(f"Обработка файла: {kb_file.name}")
                chunks = self.process_kb_page(str(kb_file))

                base_name = kb_file.stem

                self.save_chunks(chunks, output_dir, base_name)
                log.info(f"Файл {kb_file.name} обработан: создано {len(chunks)} чанк(ов)")

            except Exception as e:
                log.error(f"Ошибка при обработке {kb_file.name}: {e}")
                continue

        log.info("Обработка всех файлов завершена!")

    def process_document(self, document_data: dict) -> list[dict]:
        try:
            url = document_data.get('url', '')
            title = document_data.get('title', '')
            content = document_data.get('content', '')

            if not content:
                log.warning(f"Пустой контент для документа: {title}")
                return []

            token_count = self.count_tokens(content)
            log.info(f"Обработка документа '{title}': {token_count} токенов")

            if token_count < self.chunk_size:
                log.info(f"Текст меньше {self.chunk_size} токенов, создается один чанк")
                return [{
                    'url': url,
                    'title': title,
                    'content': content
                }]

            chunks = self.create_chunks_with_overlap(content)

            result = []
            for chunk_text in chunks:
                result.append({
                    'url': url,
                    'title': title,
                    'content': chunk_text,
                })

            log.info(f"Создано {len(result)} чанков для '{title}'")
            return result

        except Exception as e:
            log.error(f"Ошибка при обработке документа: {e}")
            return []

    async def process_parser_output(self, parser_data_dir: str, output_dir: str):
        parser_path = Path(parser_data_dir)

        if not parser_path.exists():
            log.error(f"Директория {parser_data_dir} не существует")
            return

        json_files = sorted(parser_path.glob("*.json"))
        log.info(f"Найдено {len(json_files)} JSON файлов для обработки")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        total_chunks = 0

        for json_file in json_files:
            try:
                log.info(f"Обработка файла: {json_file.name}")

                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if not isinstance(data, list):
                    log.warning(f"Файл {json_file.name} не содержит массив документов, пропускаем")
                    continue

                for i, document in enumerate(data, 1):
                    chunks = self.process_document(document)

                    if not chunks:
                        continue

                    base_name = f"{json_file.stem}_doc_{i}"
                    self.save_chunks(chunks, output_dir, base_name)
                    total_chunks += len(chunks)

                log.info(f"Файл {json_file.name} обработан: {len(data)} документов")

            except Exception as e:
                log.error(f"Ошибка при обработке {json_file.name}: {e}")
                continue

        log.info(f"Обработка завершена! Всего создано {total_chunks} чанков")


async def main():
    parser_data_dir = "./core/data"
    output_dir = "./core/data/chunks"

    processor = ChunkProcessor()
    await processor.process_parser_output(parser_data_dir, output_dir)


if __name__ == "__main__":
    asyncio.run(main())