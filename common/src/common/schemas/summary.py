from pydantic import BaseModel


class SummarySegment(BaseModel):
    start_ms: int
    end_ms: int
    content: str
