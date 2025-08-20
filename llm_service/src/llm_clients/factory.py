from loguru import logger

from llm_clients.base import LLMClient
from llm_clients.litellm import LiteLLMClient
from schemas.enums import LLMClientType


class LLMClientFactory:
    @staticmethod
    def create_llm_client(llm_client_type: str) -> LLMClient:
        if llm_client_type == LLMClientType.LITELLM.value:
            return LiteLLMClient()
        else:
            logger.error("Not defined llm client type")
            raise ValueError
