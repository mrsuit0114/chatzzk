from abc import ABC, abstractmethod

from litellm import completion
from loguru import logger

from llm.prompt_builder import PromptBuilderFactory


class LLMClient(ABC):
    def __init__(self, config: dict, task_type: str, proxy_url: str):
        self.prompt_builder = PromptBuilderFactory.create_prompt_builder(
            config[task_type]["prompt_builder"], task_type
        )
        self.proxy_url = proxy_url
        self.task_type = task_type

    @abstractmethod
    def complete(self, api_key: str, **kwargs):
        pass

    def _build_messages(self, **kwargs) -> list[dict]:
        return self.prompt_builder.build_messages(**kwargs)


class LLMClientFactory:
    @staticmethod
    def create_llm_client(config: dict, task_type: str, proxy_url: str) -> LLMClient:
        if task_type == "short_term_summary":
            return ShortTermSummaryLLMClient(config, proxy_url)
        else:
            raise ValueError(f"Invalid task type: {task_type}")


class ShortTermSummaryLLMClient(LLMClient):
    def __init__(self, config: dict, proxy_url: str):
        super().__init__(config, "short_term_summary", proxy_url)

    def complete(self, api_key: str, **kwargs) -> str:
        messages = self._build_messages(**kwargs)

        try:
            response = completion(
                model=self.task_type,
                messages=messages,
                api_key=api_key,
                base_url=self.proxy_url,
                custom_llm_provider="openai",
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in request_completion: {e}")
            raise e
