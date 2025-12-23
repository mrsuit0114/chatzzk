from langfuse import Langfuse
from pydantic import BaseModel

from chatzzk_core.constants import LLMTask
from chatzzk_core.schemas.config.clients import LangfuseConfig


class PromptManager:
    def __init__(self, langfuse_client: Langfuse, config: LangfuseConfig):
        self.langfuse = langfuse_client
        self.prompt_paths = config.prompt_paths
        self.cache_ttl_seconds = config.cache_ttl_seconds

    def build_prompt(self, task: LLMTask, variables: BaseModel) -> list[dict[str, str]]:
        """
        내부적으로 Langfuse와 통신하고 변수를 주입하는 공통 로직
        """
        prompt_path = self.prompt_paths.get(task)
        if not prompt_path:
            raise ValueError(f"No prompt ID mapping found for task: {task}")

        prompt = self.langfuse.get_prompt(name=prompt_path, type="chat", cache_ttl_seconds=self.cache_ttl_seconds)

        compiled = prompt.compile(**variables.model_dump())

        return compiled
