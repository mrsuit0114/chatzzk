from pydantic import BaseModel, Field

from chatzzk_core.constants import LLMPromptPaths


class LiteLLMProxyConfig(BaseModel):
    proxy_url: str
    api_key: str


class LangfuseConfig(BaseModel):
    public_key: str
    secret_key: str
    base_url: str
    prompt_paths: dict[str, str] = Field(default_factory=lambda: LLMPromptPaths.BY_TASK)
