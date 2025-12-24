from langfuse import Langfuse
from loguru import logger
from pydantic import BaseModel

from chatzzk_core.schemas.config.clients import LangfuseConfig


class PromptManager:
    def __init__(self, langfuse_client: Langfuse, config: LangfuseConfig):
        self.langfuse = langfuse_client
        self.cache_ttl_seconds = config.cache_ttl_seconds

    def build_prompt(self, prompt_path: str, variables: BaseModel) -> list[dict[str, str]]:
        try:
            prompt = self.langfuse.get_prompt(name=prompt_path, type="chat", cache_ttl_seconds=self.cache_ttl_seconds)
            compiled = prompt.compile(**variables.model_dump())
            return compiled

        except Exception as e:
            logger.error(f"Failed to build prompt from {prompt_path}: {e}")
            raise
