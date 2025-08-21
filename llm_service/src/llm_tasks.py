from common.schemas.enums import TaskType

from llm_clients.base import LLMClient
from llm_clients.factory import LLMClientFactory
from prompts.base import PromptBuilder
from prompts.factory import PromptBuilderFactory
from schemas import task_models


class LLMTask:
    def __init__(self, prompt_builder_type: str, llm_client_type: str):
        self.prompt_builder: PromptBuilder = PromptBuilderFactory.create_prompt_builder(prompt_builder_type)
        self.client: LLMClient = LLMClientFactory.create_llm_client(llm_client_type)

    def short_term_summary(self, data: dict):
        task_type = TaskType.SHORT_TERM_SUMMARY.value

        summary_data = task_models.ShortTermSummaryData(**data)

        # 2. Pydantic 모델의 헬퍼 메서드를 호출하여 프롬프트 템플릿에 맞는 딕셔너리 생성
        prompt_variables = summary_data.to_prompt_dict()

        # 3. 프롬프트 빌더에 가공된 변수들을 전달
        # prompt_builder는 이제 간단한 key-value만 처리하면 됩니다.
        messages = self.prompt_builder.get_prompt(task_type, prompt_variables)

        response = self.client.send_completion(task_type, messages)

        return response
