from datetime import datetime

from pydantic import BaseModel


class ChzzkVODCreateParams(BaseModel):
    channel_id: int
    video_no: int
    video_title: str
    duration: int
    video_category_value: str
    publish_date: datetime
    live_open_date: datetime


class ChzzkVODFindParams(BaseModel):
    video_no: int | None = None
