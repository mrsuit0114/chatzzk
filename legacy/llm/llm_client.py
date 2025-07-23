import json
from abc import ABC, abstractmethod

from litellm import acompletion, completion
from llm.prompt_builder import PromptBuilderFactory
from loguru import logger
from pydantic import BaseModel

from data_types.task_param import GeneralChoiceParams, GeneralParams, ShortTermSummaryParams


class LLMClient(ABC):
    def __init__(self, config: dict, task_type: str, proxy_url: str):
        self.prompt_builder = PromptBuilderFactory.create_prompt_builder(config["prompt_builder"], task_type)
        self.proxy_url = proxy_url
        self.task_type = task_type

    @abstractmethod
    async def async_complete(self, api_key: str, params):
        pass

    @abstractmethod
    def complete(self, api_key: str, params) -> str | list[str]:
        pass

    def _build_messages(self, params) -> list[dict]:
        return self.prompt_builder.build_messages(params)

    def show_prompt(self, params):
        system_prompt = self.prompt_builder._build_system_prompt()
        user_prompt = self.prompt_builder._build_user_prompt(params)
        print(f"System Prompt:\n{system_prompt}\n\nUser Prompt:\n{user_prompt}")


class LLMClientFactory:
    @staticmethod
    def create_llm_client(config: dict, task_type: str, proxy_url: str) -> LLMClient:
        if task_type == "short_term_summary":
            return ShortTermSummaryLLMClient(config, proxy_url)
        elif task_type == "general":
            return GeneralLLMClient(config, proxy_url)
        elif task_type == "general_choice":
            return GeneralChoiceLLMClient(config, proxy_url)
        else:
            raise ValueError(f"Invalid task type: {task_type}")


# 요약을 위한 용도로 시스템에서만 사용되는 클라이언트
class ShortTermSummaryLLMClient(LLMClient):
    def __init__(self, config: dict, proxy_url: str):
        super().__init__(config, "short_term_summary", proxy_url)

    async def async_complete(self, api_key: str, params: ShortTermSummaryParams) -> str:
        messages = self._build_messages(params)

        try:
            response = await acompletion(
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

    def complete(self, api_key: str, params: ShortTermSummaryParams) -> str:
        messages = self._build_messages(params)

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


class GeneralChoiceResponse(BaseModel):
    choices: list[str]


# 방송 주제 추천, 채팅 추천, 도네이션 추천 등의 용도로 사용되는 클라이언트
class GeneralChoiceLLMClient(LLMClient):
    def __init__(self, config: dict, proxy_url: str):
        super().__init__(config, "general_choice", proxy_url)
        self.choice_num = config["choice_num"]

    async def async_complete(self, api_key: str, params: GeneralChoiceParams) -> list[str]:
        messages = self._build_messages(params)
        try:
            response = await acompletion(
                model=self.task_type,
                messages=messages,
                api_key=api_key,
                base_url=self.proxy_url,
                custom_llm_provider="openai",
                response_format=GeneralChoiceResponse,
            )
            return json.loads(response.choices[0].message.content)["choices"][: self.choice_num]
        except Exception as e:
            logger.error(f"Error in request_completion: {e}")
            raise e

    def complete(self, api_key: str, params: GeneralChoiceParams) -> list[str]:
        messages = self._build_messages(params)

        try:
            response = completion(
                model=self.task_type,
                messages=messages,
                api_key=api_key,
                base_url=self.proxy_url,
                custom_llm_provider="openai",
                response_format=GeneralChoiceResponse,
            )
            return json.loads(response.choices[0].message.content)["choices"][: self.choice_num]
        except Exception as e:
            logger.error(f"Error in request_completion: {e}")
            raise e


# 방송 분위기, 전반적인 여론 등 현재 방송 상황에 대해 범용적인 물음에 대한 답변을 위한 클라이언트
class GeneralLLMClient(LLMClient):
    def __init__(self, config: dict, proxy_url: str):
        super().__init__(config, "general", proxy_url)

    async def async_complete(self, api_key: str, params: GeneralParams) -> str:
        messages = self._build_messages(params)
        try:
            response = await acompletion(
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

    def complete(self, api_key: str, params: GeneralParams) -> str:
        messages = self._build_messages(params)

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
