# 1회의 LLM 요청을 담당
# ChatRecommendationProcessor, SummaryProcessor ...
# task는 팩토리패턴이고 호출하는 쪽에서 커맨드 패턴?


from clients import LLMClient
from llm_client_factory import LLMClientFactory
from prompt_builder_factory import PromptBuilderFactory
from prompt_builders import PromptBuilder


class LLMTask:
    def __init__(self, prompt_builder_type: str, llm_client_type: str):
        self.prompt_builder: PromptBuilder = PromptBuilderFactory.create_prompt_builder(prompt_builder_type)
        self.client: LLMClient = LLMClientFactory.create_llm_client(llm_client_type)

    def short_term_summary(self, datas: dict):
        task_type = "gemini"
        messages = self.prompt_builder.get_prompt(task_type, datas)

        response = self.client.send_completion(task_type, messages)

        return response
