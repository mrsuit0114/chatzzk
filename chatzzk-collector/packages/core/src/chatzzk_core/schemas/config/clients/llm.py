from pydantic import BaseModel, Field

from chatzzk_core.constants import ASR_HALLUCINATION_KEYWORDS, LLMPromptPaths, LLMTask


class ContextAssemblerConfig(BaseModel):
    hallucination_keywords: list[str] = Field(default=ASR_HALLUCINATION_KEYWORDS)


class LiteLLMProxyConfig(BaseModel):
    proxy_url: str
    api_key: str


class LangfuseConfig(BaseModel):
    public_key: str
    secret_key: str
    base_url: str
    prompt_paths: dict[LLMTask, str] = Field(default=LLMPromptPaths.BY_TASK)
