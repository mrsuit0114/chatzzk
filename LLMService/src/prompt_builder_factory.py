from loguru import logger

from enums import PromptBuilderType
from prompt_builders import LangfusePromptBuilder, PromptBuilder


class PromptBuilderFactory:
    @staticmethod
    def create_prompt_builder(prompt_builder_type: str) -> PromptBuilder:
        if prompt_builder_type == PromptBuilderType.LANGFUSE.value:
            return LangfusePromptBuilder()
        else:
            logger.error("Not defined prompt builder type")
            raise ValueError
