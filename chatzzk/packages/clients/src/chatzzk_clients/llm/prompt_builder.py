from typing import Any

from langfuse import Langfuse
from loguru import logger
from pydantic import BaseModel

from chatzzk_schemas.config.clients.llm import LangfuseConfig
from chatzzk_schemas.api_models.llm import StreamSegmentAnalysisParams, StreamSegmentAnalysisInput
from chatzzk_constants.service_codes import LLMTask
from chatzzk_schemas.storage.models import StreamEntry
from chatzzk_schemas.api_models.llm import PlatformMetadata, ChannelMetadata


class PromptBuilder:
    """
    # task에 맞는 params를 받고 적절한 Input으로 매핑하여 컴파일된 messages를 반환하는 것이 prompt_builder의 역할
    Langfuse를 사용하여 프롬프트 템플릿을 관리하고 컴파일하는 빌더 클래스.
    """

    def __init__(self, config: LangfuseConfig):
        self.langfuse = Langfuse(
            public_key=config.public_key,
            secret_key=config.secret_key,
            base_url=config.base_url,
        )
        self.prompts: dict[str, Any] = {}
        self._init_prompt_templates(config.prompt_paths)

    def _init_prompt_templates(self, prompt_paths: dict[str, str]) -> None:
        for k, p in prompt_paths.items():
            try:
                self.prompts[k] = self.langfuse.get_prompt(p, type="chat")
            except Exception as e:
                logger.warning(f"Failed to get prompt template '{p}': {e}")

    def _get_compiled_messages(self, task: LLMTask, params: BaseModel) -> list[dict[str, str]]:
        """
        Langfuse에서 가져온 템플릿에 파라미터를 주입하고 chat 포맷(list[dict])으로 반환
        """
        try:
            prompt_template = self.prompts.get(task.value)
            if not prompt_template:
                raise ValueError(f"Prompt template '{task.value}' not found")
            compiled_prompt = prompt_template.compile(**params.model_dump())

            return compiled_prompt

        except Exception as e:
            logger.error(f"Failed to get/compile prompt template '{task.value}': {e}")
            raise e

    def get_summary_prompt(
        self,
        *,
        platform_metadata: PlatformMetadata,
        channel_metadata: ChannelMetadata,
        previous_summary: str | None = None,
        broadcast_logs: list[StreamEntry],
    ):
        params = StreamSegmentAnalysisParams(
            platform_metadata=platform_metadata,
            channel_metadata=channel_metadata,
            broadcast_logs=broadcast_logs,
            previous_summary=previous_summary,
        )
        inputs = StreamSegmentAnalysisInput.from_analysis_params(params)
        return self._get_compiled_messages(LLMTask.SUMMARIZE, inputs)

    # def get_meta_summary_prompt(self, params: dict[str, Any]):
    #     params = StreamSegmentAnalysisParams.build(**params)
    #     inputs = StreamSegmentAnalysisInput.from_analysis_params(params)
    #     return self._get_compiled_messages(LLMTask.META_SUMMARIZE, inputs)
