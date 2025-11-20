from pydantic import BaseModel

from chatzzk_constants.service_codes import PlatformCode


# `[엔티티][동사][역할]DTO`
class PlatformAddRequestDTO(BaseModel):
    platform_code: PlatformCode
    platform_name: str
    donation_unit: str


class PlatformAddResponseDTO(BaseModel):
    platform_id: int
