from pydantic import BaseModel, Field

from chatzzk_core.constants import LLM_PROMPT_PATHS, LLMTask, StreamWindowConstant


class StreamWindowConfig(BaseModel):
    clip_size: int = StreamWindowConstant.CLIP_SIZE
    segment_size: int = StreamWindowConstant.SEGMENT_SIZE
    chapter_size: int = StreamWindowConstant.CHAPTER_SIZE
    stream_log_padding_size: int = StreamWindowConstant.STREAM_LOG_PADDING_SIZE


class LLMGenerationConfig(BaseModel):
    prompt_paths: dict[LLMTask, str] = Field(default=LLM_PROMPT_PATHS)
    stream_window_config: StreamWindowConfig = Field(default_factory=StreamWindowConfig)
