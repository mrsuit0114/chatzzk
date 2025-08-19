from pydantic import BaseModel


class ContextData(BaseModel):
    """Data structure for context information.

    Attributes:
        timestamp_ms: Timestamp of the context in milliseconds
        content: Content of the context
        type: Type of the context. ex. "ASR", "CHAT", "DONATION"
        prompt_str: Formatted string for prompt usage
    """

    timestamp_ms: int
    content: str
    type_code: int
    prompt_str: str
    pay_amount: int = 0
