from loguru import logger

from core.enums import PromptBuilderType
from prompts.base import PromptBuilder
from prompts.langfuse import LangfusePromptBuilder


class PromptBuilderFactory:
    @staticmethod
    def create_prompt_builder(prompt_builder_type: str) -> PromptBuilder:
        if prompt_builder_type == PromptBuilderType.LANGFUSE.value:
            return LangfusePromptBuilder()
        else:
            logger.error("Not defined prompt builder type")
            raise ValueError
