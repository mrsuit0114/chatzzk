import time

from litellm import completion, exceptions
from llm_clients.base import LLMClient


class LiteLLMClient(LLMClient):
    def _messages_to_chat_format(self, messages: list[tuple]):
        return [{"role": role, "content": content} for role, content in messages]

    def send_completion(self, task_type: str, messages: list[tuple]) -> str:
        formatted_messages = self._messages_to_chat_format(messages=messages)

        max_retries = 10
        retry_delay_seconds = 1  # Initial delay

        for attempt in range(max_retries):
            try:
                response = completion(model=f"litellm_proxy/{task_type}", messages=formatted_messages)
                return response.choices[0].message.content
            except exceptions.RateLimitError:
                print(
                    f"Rate limit hit for {task_type}, retrying in {retry_delay_seconds}s... (Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(retry_delay_seconds)
                retry_delay_seconds *= 2  # Exponential backoff
            except exceptions.APIError as e:
                print(
                    f"API Error for {task_type}: {e}. Retrying in {retry_delay_seconds}s... (Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(retry_delay_seconds)
                retry_delay_seconds *= 2
            except Exception as e:  # Catch other unexpected errors
                print(f"An unexpected error occurred for {task_type}: {e}. (Attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:  # If last attempt, re-raise
                    raise
                time.sleep(retry_delay_seconds)
                retry_delay_seconds *= 2

        # If all retries fail, an exception will be re-raised by the last except block
        raise Exception(f"Failed to get completion for {task_type} after {max_retries} attempts.")
