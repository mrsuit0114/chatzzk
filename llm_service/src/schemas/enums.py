from enum import Enum


class LLMClientType(Enum):
    LITELLM = "litellm"


class PromptBuilderType(Enum):
    LANGFUSE = "langfuse"


class TaskType(Enum):
    SHORT_TERM_SUMMARY = "short_term_summary"
