from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def send_completion(self, task_type: str, messages):
        pass
