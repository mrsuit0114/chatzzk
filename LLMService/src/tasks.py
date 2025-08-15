from clients.base import LLMClient
from clients.factory import LLMClientFactory
from core import schemas
from prompts.base import PromptBuilder
from prompts.factory import PromptBuilderFactory


class LLMTask:
    def __init__(self, prompt_builder_type: str, llm_client_type: str):
        self.prompt_builder: PromptBuilder = PromptBuilderFactory.create_prompt_builder(prompt_builder_type)
        self.client: LLMClient = LLMClientFactory.create_llm_client(llm_client_type)

    def short_term_summary(self, data: schemas.ShortTermSummaryData):
        task_type = "gemini"
        messages = self.prompt_builder.get_prompt(task_type, data.model_dump())

        response = self.client.send_completion(task_type, messages)

        return response
