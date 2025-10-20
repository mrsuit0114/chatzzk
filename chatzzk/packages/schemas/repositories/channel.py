from pydantic import BaseModel


class ChzzkChannelCreateDTO(BaseModel):
    platform_channel_id: str
    channel_name: str
    is_verified: bool = False
