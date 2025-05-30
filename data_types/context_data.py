from typing import NamedTuple


class ContextData(NamedTuple):
    """Data structure for context information.

    Attributes:
        timestamp_ms: Timestamp of the context in milliseconds
        content: Content of the context
        type: Type of the context. ex. "ASR", "CHAT", "DONATION"
    """

    timestamp_ms: int
    content: str
    type: str
