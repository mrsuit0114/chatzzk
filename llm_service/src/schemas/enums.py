from enum import Enum


class LLMClientType(Enum):
    LITELLM = "litellm"


class PromptBuilderType(Enum):
    LANGFUSE = "langfuse"
