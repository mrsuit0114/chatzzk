from pydantic import BaseModel, Field

from chatzzk_constants.service_codes import LLMTask, LLMPromptPath


class LiteLLMProxyConfig(BaseModel):
    proxy_url: str
    api_key: str


class LangfuseConfig(BaseModel):
    public_key: str
    secret_key: str
    base_url: str
    prompt_paths: dict[str, str] = Field(
        default_factory=lambda: {
            LLMTask.SUMMARIZE.value: LLMPromptPath.SUMMARIZE,
            LLMTask.META_SUMMARIZE.value: LLMPromptPath.META_SUMMARIZE,
        }
    )
