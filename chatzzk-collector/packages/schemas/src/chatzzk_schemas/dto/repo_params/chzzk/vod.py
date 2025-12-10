from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChzzkVODCreateParams(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True, extra="ignore")

    channel_id: int
    video_no: int
    video_title: str
    duration: int
    video_category_value: str
    publish_date: datetime
    live_open_date: datetime


class ChzzkVODFindParams(BaseModel):
    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True, extra="ignore")

    video_no: int | None = None
