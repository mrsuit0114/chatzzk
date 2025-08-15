from loguru import logger

from clients import LiteLLMClient, LLMClient
from enums import LLMClientType


class LLMClientFactory:
    @staticmethod
    def create_llm_client(llm_client_type: str) -> LLMClient:
        if llm_client_type == LLMClientType.LITELLM.value:
            return LiteLLMClient()
        else:
            logger.error("Not defined llm client type")
            raise ValueError
