from abc import ABC, abstractmethod


class PromptBuilder(ABC):
    @abstractmethod
    def get_prompt(self, task_type: str, datas: dict):
        pass
