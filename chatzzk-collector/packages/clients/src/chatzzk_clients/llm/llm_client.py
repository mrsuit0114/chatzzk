from typing import Any

import aiohttp
import litellm
from loguru import logger
from pydantic import BaseModel

from chatzzk_core.schemas.config import LiteLLMProxyConfig


class LLMPClient:
    """
    LLM Proxy Server에 요청을 보내는 클라이언트.
    litellm의 completion 기능을 활용하여 OpenAI 호환 API(Proxy)와 통신.
    """

    def __init__(self, config: LiteLLMProxyConfig, session: aiohttp.ClientSession):
        self.proxy_url = config.proxy_url
        self.api_key = config.api_key
        self.session = session
        litellm.use_litellm_proxy = True

    async def generate(self, messages: list[dict[str, Any]], model: str, schema_model: BaseModel, **kwargs) -> str:
        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                response_format=schema_model,
                base_url=self.proxy_url,
                api_key=self.api_key,
                shared_session=self.session,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Proxy LLM generation failed: {e}")
            raise e
