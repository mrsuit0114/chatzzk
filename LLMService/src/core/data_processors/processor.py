import bisect
import copy
from typing import Any

from config import Config
from core.schemas import ContextData

# 요약, 채팅 추천만 고려해보자
# 요약의 경우 window sliding, shift를 고려해서 context용 prompt_str의 list로 반환
# 채팅 추천의 경우 start_ms와 window_duration를 고려해서 리스트로 반환 prompt_str로 반환
# prompt_str로 반환하기 위해 TYPE_CODE_TO_PROMPT_CMD의 매핑정보가 필요함


class DataContextProcessor:
    """
    Provides methods to compose and format context data for LLM prompts.
    """

    def __init__(self, config: Config):
        self.type_code_to_prompt_cmd = {v: k.upper() for k, v in config.DataProcessor.PROMPT_CMD_TO_TYPE_CODE.items()}

    def set_data(self, context_data: list[dict[str, Any]]):
        """
        Sets or replaces the base data for the processor.
        Data is assumed to be sorted by timestamp_ms.
        """
        self.data: list[ContextData] = [ContextData.model_validate(d) for d in context_data]
        self.timestamps: list[int] = [d.timestamp_ms for d in self.data]
        self.composed_data: list[list[ContextData]] = [[]]

    def reset_data(self):
        self.composed_data = [copy.deepcopy(self.data)]

    def _get_prompt_content(self, item: ContextData):
        return f"[{self.type_code_to_prompt_cmd[item.type_code]}] {item.prompt_str}"

    def create_time_windows(
        self, start_ms: int, end_ms: int, window_duration_ms: int, shift_duration_ms: int
    ) -> list[list[ContextData]]:
        """
        Composes the data into time-based sliding windows.
        Uses the currently filtered base data to create windows.
        """
        base_data = self.data
        if not base_data:
            self.composed_data = [[]]
            return self.composed_data

        new_windows = []
        start_idx = bisect.bisect_left(self.timestamps, start_ms)

        while start_idx < len(base_data):
            current_time = base_data[start_idx].timestamp_ms
            if current_time > end_ms:
                break

            end_time = current_time + window_duration_ms

            # Find the end index for the current window
            # bisect_right will find the insertion point, which is perfect for a slice endpoint
            end_idx = bisect.bisect_right(self.timestamps, end_time, lo=start_idx)

            window = base_data[start_idx:end_idx]
            if window:
                new_windows.append(window)

            # Find the start index for the next window using the time shift
            next_start_time = current_time + shift_duration_ms
            next_start_idx = bisect.bisect_left(self.timestamps, next_start_time, lo=start_idx)

            # If bisect_left returns the same index, it means we are stuck.
            # To prevent an infinite loop, we must advance by at least one element.
            if next_start_idx == start_idx:
                next_start_idx += 1

            start_idx = next_start_idx

        self.composed_data = new_windows
        return self.composed_data

    def get_windowed_prompt(self, window: list[ContextData], separator: str = "\n") -> str:
        """
        Formats the composed data windows into a list of prompt strings.
        """

        return separator.join(self._get_prompt_content(item) for item in window if item.prompt_str)
