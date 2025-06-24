from abc import ABC, abstractmethod


def _expand_dict(data: dict) -> str:
    prompt = ""
    for key, value in data.items():
        if isinstance(value, str):
            prompt += value + "\n"
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    prompt += _expand_dict(item)
                else:
                    prompt += f"- {item}\n"
        elif isinstance(value, dict):
            prompt += _expand_dict(value)
    return prompt


def _build_prompt_format_from_json(data: dict) -> str:
    prompt = ""
    for key, value in data.items():
        if isinstance(value, str):
            prompt += value + "\n"
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    prompt += f"\n{_expand_dict(item)}"
                else:
                    prompt += f"- {item}\n"
        elif isinstance(value, dict):
            prompt += _expand_dict(value)
    return prompt


class PromptBuilder(ABC):
    def __init__(self, config: dict):
        self.system_prompt_format = _build_prompt_format_from_json(config["system_prompt_format"])
        self.user_prompt_format = _build_prompt_format_from_json(config["user_prompt_format"])

    @abstractmethod
    def _build_system_prompt(self) -> str:
        pass

    @abstractmethod
    def _build_user_prompt(self, **kwargs) -> str:
        pass

    def build_messages(self, **kwargs) -> list[dict]:
        return [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": self._build_user_prompt(**kwargs)},
        ]


class ShortTermSummaryPromptBuilder(PromptBuilder):
    def __init__(self, config: dict):
        super().__init__(config)

    def _build_system_prompt(self) -> str:
        return self.system_prompt_format

    def _build_user_prompt(self, metadata: dict, prev_summary: str, cur_context: str) -> str:
        return self.user_prompt_format.format(**metadata, prev_summary=prev_summary, cur_context=cur_context)


class PromptBuilderFactory(PromptBuilder):
    @staticmethod
    def create_prompt_builder(config: dict, task_type: str) -> PromptBuilder:
        if task_type == "short_term_summary":
            return ShortTermSummaryPromptBuilder(config)
        else:
            raise ValueError(f"Invalid prompt type: {task_type}")
