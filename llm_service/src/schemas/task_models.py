from pydantic import BaseModel


class ShortTermSummaryData(BaseModel):
    request: str
