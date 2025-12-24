from typing import Protocol


class ContextRenderable(Protocol):
    def to_context_string(self) -> str: ...
