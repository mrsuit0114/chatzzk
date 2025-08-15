from enum import Enum


class LLMClientType(Enum):
    LITELLM = "litellm"


class PromptBuilderType(Enum):
    LANGFUSE = "langfuse"


class TaskType(Enum):
    SHORTTERMSUMMARY = "short_term_summary"
