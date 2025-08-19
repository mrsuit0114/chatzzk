from config import Config
from core.data_loaders.loader import DataLoader
from core.data_processors.processor import DataContextProcessor


class DataManager:
    def __init__(self, config: Config):
        self.data_loader = DataLoader()
        self.data_context_processor = DataContextProcessor(config)
