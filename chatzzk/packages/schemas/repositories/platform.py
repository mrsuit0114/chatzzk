from pydantic import BaseModel

from chatzzk.packages.constants.service_codes import PlatformCode


class PlatformCreateDTO(BaseModel):
    platform_code: PlatformCode
    platform_name: str
    donation_unit: str
