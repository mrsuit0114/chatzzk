from langfuse import get_client, observe
from prompts.base import PromptBuilder


class LangfusePromptBuilder(PromptBuilder):
    def __init__(self, cache_ttl_seconds: int = 300):
        self.langfuse = get_client()
        self.cache_ttl_seconds = cache_ttl_seconds

    def _get_prompt_template(self, task_type: str):
        langfuse_prompt_template = self.langfuse.get_prompt(
            task_type, type="chat", cache_ttl_seconds=self.cache_ttl_seconds, label="latest"
        )

        return langfuse_prompt_template

    @observe(as_type="generation")
    def get_prompt(self, task_type: str, data: dict) -> list[tuple]:
        langfuse_prompt_template = self._get_prompt_template(task_type)
        self.langfuse.update_current_generation(prompt=langfuse_prompt_template)
        langfuse_prompt = langfuse_prompt_template.get_langchain_prompt(**data)

        return langfuse_prompt
