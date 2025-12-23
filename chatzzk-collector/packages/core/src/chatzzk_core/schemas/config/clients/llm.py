from pydantic import BaseModel, Field

from chatzzk_core.constants import ASR_HALLUCINATION_KEYWORDS, LLM_PROMPT_PATHS, LLMTask


class ContextAssemblerConfig(BaseModel):
    hallucination_keywords: list[str] = Field(default=ASR_HALLUCINATION_KEYWORDS)


class LiteLLMConfig(BaseModel):
    base_url: str
    api_key: str
    max_retries: int


class LangfuseConfig(BaseModel):
    public_key: str
    secret_key: str
    base_url: str
    prompt_paths: dict[LLMTask, str] = Field(default=LLM_PROMPT_PATHS)
    cache_ttl_seconds: int = Field(default=300)
