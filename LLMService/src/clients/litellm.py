from litellm import completion

from clients.base import LLMClient


class LiteLLMClient(LLMClient):
    def _messages_to_chat_format(self, messages: list[tuple]):
        return [{"role": role, "content": content} for role, content in messages]

    def send_completion(self, task_type: str, messages: list[tuple]) -> str:
        formatted_messages = self._messages_to_chat_format(messages=messages)
        response = completion(
            model=f"litellm_proxy/{task_type}", messages=formatted_messages
        )  # ChatPromptTemplate, 즉 litellm의 completion에서 langchain이 제공하는 형식을 사용할 수 있어야함
        response = response.choices[0].message.content

        return response
