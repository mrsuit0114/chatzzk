from enum import Enum


class LLMClientType(Enum):
    LITELLM = "litellm"


class PromptBuilderType(Enum):
    LANGFUSE = "langfuse"


class TaskType(Enum):
    SHORT_TERM_SUMMARY = "short_term_summary"


class DataSourceType(Enum):
    LOCAL_FILE = "local_file"
    DATABASE = "database"
    # API = "api" # for future extension


class DataFormatType(Enum):
    JSON = "json"
    JSONL = "jsonl"
    # CSV = "csv" # for future extension
