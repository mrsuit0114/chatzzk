# langfuse에서 시스템 프롬프트를 그대로 사용? - 우선은 작게 시작하고 평가를 구축하고 이를 기준으로 확장해나가자
# 예시 - 시스템: 너는 객관적으로 요약을 하는 전문가 입니다. / 유저: {{context}} {{request}}부터 시작

from abc import ABC, abstractmethod

from langfuse import get_client


class PromptBuilder(ABC):
    @abstractmethod
    def get_prompt(self, task_type: str, datas: dict):
        pass


class LangfusePromptBuilder(PromptBuilder):
    def __init__(self):
        self.langfuse = get_client()

    def _get_prompt_template(self, task_type: str, cache_ttl_seconds: int = 300):
        langfuse_prompt_template = self.langfuse.get_prompt(
            task_type, type="chat", cache_ttl_seconds=cache_ttl_seconds
        )

        return langfuse_prompt_template

    def get_prompt(self, task_type: str, datas: dict) -> list[tuple]:
        langfuse_prompt_template = self._get_prompt_template(task_type)

        langfuse_prompt = langfuse_prompt_template.get_langchain_prompt(**datas)

        return langfuse_prompt
