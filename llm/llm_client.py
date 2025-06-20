import time

from litellm import completion

from data_types.context_data import ContextData
from llm.prompt_builder import PromptBuilder


class LLMClient:
    # 어떤 요청을 받을지 모름 - 주제요청, 방송 흐름정리, 채팅 추천 등 요구사항에 따라 시스템 프롬프트가 다름
    def __init__(self, config: dict, proxy_url: str):
        self.prompt_builder = PromptBuilder(config["prompt_builder"])
        self.proxy_url = proxy_url

    def request_completion_choices(
        self,
        user_api_key: str,
        *,
        request_type: str,
        metadata: dict[str, str],
        prev_summary: str,
        cur_context: list[ContextData],
        custom_request: str,
    ):
        # system_prompt, metadata, prev_summary, cur_context, custom_request, system_request_emphasis
        # messages = self.prompt_builder.build_prompt_for_choices(request_type, metadata, prev_summary, cur_context, custom_request)

        pass

    def request_completion_summary(
        self,
        user_api_key: str,
        *,
        metadata: dict[str, str],
        prev_summary: str,
        cur_context: str,
    ):
        messages = self.prompt_builder.build_prompt_for_summary(metadata, prev_summary, cur_context)

        max_retries = 30
        base_delay = 1  # 초기 대기 시간 (초)

        for attempt in range(max_retries):
            try:
                response = completion(
                    model="gemini/gemini-2.0-flash",
                    messages=messages,
                    # api_base=self.proxy_url,
                    # api_key=user_api_key,
                    temperature=0.3,
                    top_p=0.9,
                    max_tokens=500,
                )
                return response.choices[0].message.content
            except Exception:
                if attempt == max_retries - 1:  # 마지막 시도였다면
                    raise  # 에러를 그대로 전파

                # 지수 백오프: 각 시도마다 대기 시간이 2배씩 증가
                delay = base_delay * (2**attempt)
                time.sleep(delay)
                continue
