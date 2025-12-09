from utils.logger import get_logger
from config.Config import CONFIG

log = get_logger("ChunksService")


class ChunkProcessor:
    def __init__(self):
        self.chunk_size = CONFIG.chunks.chunk_size
        self.overlap = CONFIG.chunks.overlap
        self.model_name = CONFIG.chunks.model_name
        log.info(f"Загрузка модели {self.model_name}...")