from pydantic import BaseModel


class ShortTermSummaryData(BaseModel):
    request: str


class ContextData(BaseModel):
    """Data structure for context information."""

    timestamp_ms: int
    content: str
    type_code: int
    prompt_str: str
    pay_amount: int = 0
