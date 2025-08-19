from loguru import logger

from config import Config
from core.data_loaders.loader import DataLoader
from core.data_processors.processor import DataContextProcessor
from core.enums import DataFormatType, DataSourceType

config = Config()
DATA_DIR = "./LLMService/data/full_contexts"

data_loader = DataLoader()
data_context_processor = DataContextProcessor(config)

res = data_loader.load(DataSourceType.LOCAL_FILE, DataFormatType.JSONL, f"{DATA_DIR}/8723456.jsonl")
data_context_processor.set_data(res)

windowed_context = data_context_processor.create_time_windows(0, 100000, 120000, 120000)
res_prompts = []
for window in windowed_context:
    prompts = data_context_processor.get_windowed_prompt(window)
    res_prompts.append(prompts)

if res_prompts:
    logger.info("data loaded!")
else:
    logger.warning("data load fail")
