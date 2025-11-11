from pydantic import BaseModel

from chatzzk.packages.constants.client import MediaProcessorConstant


class MediaProcessorConfig(BaseModel):
    target_sample_rate: int = MediaProcessorConstant.TARGET_SAMPLE_RATE
    target_channels: int = MediaProcessorConstant.TARGET_CHANNELS
    acodec: str = MediaProcessorConstant.ACODEC
    worker_num: int = MediaProcessorConstant.WORKER_NUM
    chunk_size: int = MediaProcessorConstant.CHUNK_SIZE
