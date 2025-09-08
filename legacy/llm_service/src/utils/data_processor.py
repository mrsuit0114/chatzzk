from common.schemas.context_data import ContextData
from common.schemas.service_codes import ContextType
from common.utils import list_processor


class DataProcessor:
    """
    A class for processing lists of ContextData.
    All methods are stateless and receive the data to be processed as an argument.
    """

    def _get_prompt_content(self, context_data: ContextData):
        cmd = ContextType(context_data.type_code).name
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
