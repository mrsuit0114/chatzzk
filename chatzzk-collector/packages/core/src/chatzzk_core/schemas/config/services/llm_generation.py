from pydantic import BaseModel, Field

from chatzzk_core.constants import LLM_PROMPT_PATHS, LLMTask, StreamWindowConfig


class LLMGenerationConfig(BaseModel):
    prompt_paths: dict[LLMTask, str] = Field(default=LLM_PROMPT_PATHS)
    stream_window_config: StreamWindowConfig = Field(default_factory=StreamWindowConfig)
