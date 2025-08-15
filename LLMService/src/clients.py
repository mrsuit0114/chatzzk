# 받은 프롬프트로 llm을 호출(직접 호출하지 않아도됨, 프록시에 요청 등 가능)해서 받은 응답을 반환하는 클래스
# LiteLLMClient, OpenAIClient...
# 지금은 LiteLLM Proxy를 사용하는 LiteLLMClient만 있음
# LITELLM_PROXY_API_KEY, LITELLM_PROXY_API_BASE는 환경 변수로 설정하고 요청마다 따로 설정할 필요가 없기 때문에 따로 설정해줄게 없네

from abc import ABC, abstractmethod

from litellm import completion


class LLMClient(ABC):
    @abstractmethod
    def send_completion(self, task_type: str, messages):
        pass


class LiteLLMClient(LLMClient):
    def _messages_to_chat_format(self, messages: list[tuple]):
        return [{"role": role, "content": content} for role, content in messages]

    def send_completion(self, task_type: str, messages) -> str:
        formatted_messages = self._messages_to_chat_format(messages=messages)
        response = completion(
            model=f"litellm_proxy/{task_type}", messages=formatted_messages
        )  # ChatPromptTemplate, 즉 litellm의 completion에서 langchain이 제공하는 형식을 사용할 수 있어야함
        response = response.choices[0].message.content

        return response
