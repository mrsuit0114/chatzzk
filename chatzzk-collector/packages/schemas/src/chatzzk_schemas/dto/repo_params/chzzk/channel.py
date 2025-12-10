# [entity][동사(CRUD)]Params
from pydantic import BaseModel


class ChzzkChannelCreateParams(BaseModel):
    platform_id: int
    platform_channel_id: str
    channel_name: str
    verified_mark: bool


class ChzzkChannelFindParams(BaseModel):
    platform_channel_id: str | None = None
    channel_name: str | None = None
    verified_mark: bool | None = None
