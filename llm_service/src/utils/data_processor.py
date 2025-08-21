from common.schemas.context_data import ContextData
from common.utils import list_processor

from config import Config


class DataProcessor:
    """
    A class for processing lists of ContextData.
    All methods are stateless and receive the data to be processed as an argument.
    """

    def __init__(self, config: Config):
        self.type_code_to_prompt_cmd = {v: k.upper() for k, v in config.DataProcessor.PROMPT_CMD_TO_TYPE_CODE.items()}

    def _get_prompt_content(self, context_data: ContextData):
        cmd = self.type_code_to_prompt_cmd[context_data.type_code]
        prompt_content = f"[{cmd}] {context_data.prompt_str}"
        return prompt_content

    def get_prompt_strings(self, contexts: list[ContextData]) -> str:
        """
        Extracts the prompt_str from a list of ContextData objects.

        Args:
            contexts: A list of ContextData objects.

        Returns:
            A list of strings, where each string is the prompt_str.
        """
        return "\n".join(self._get_prompt_content(context) for context in contexts if context.prompt_str)

    def create_sliding_windows(self, contexts: list[ContextData], window_ms: int, shift_ms: int):
        return list_processor.create_sliding_windows(contexts, window_ms, shift_ms)
