from pydantic import BaseModel


# [entity][동사][역할]DTO
class ChzzkChannelAddRequestDTO(BaseModel):
    platform_channel_id: str


class ChzzkChannelAddResponseDTO(BaseModel):
    platform_channel_id: str
    channel_name: str
    verified_mark: bool
