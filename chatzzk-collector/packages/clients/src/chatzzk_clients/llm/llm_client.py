from typing import Any, TypeVar

import instructor
from pydantic import BaseModel

from chatzzk_core.schemas.config.clients import LiteLLMConfig

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self, client: instructor.AsyncInstructor, config: LiteLLMConfig):
        self.client = client
        self.max_retries = config.max_retries

    async def request_completion(
        self, messages: list[dict[str, str]], model: str, response_model: type[T], **kwargs: Any
    ) -> T:
        """
        LiteLLM Proxy로 요청을 보내고, 구조화된 데이터를 반환합니다.

        Args:
            messages: OpenAI 포맷의 메시지 리스트
            model: LiteLLM Proxy의 model_alias로 사용됨
            response_model: 반환받을 Pydantic 모델 클래스
            **kwargs: 추가 파라미터 (필요한 경우에만 사용)

        Returns:
            response_model의 인스턴스 (T)
        """
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                response_model=response_model,
                max_retries=self.max_retries,
                **kwargs,
            )
            return response

        except Exception as e:
            raise e
