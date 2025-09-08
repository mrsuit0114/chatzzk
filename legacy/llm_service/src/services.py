from llm_tasks import LLMTask
from utils.data_processor import DataProcessor

from common.schemas.summary import SummarySegment
from common.utils.data_loader import DataLoader


class LLMService:
    """Provides high-level services for LLM-related tasks."""

    def __init__(
        self,
        llm_task: LLMTask,
        data_loader: DataLoader,
        data_processor: DataProcessor,
    ):
        self.llm_task = llm_task
        self.data_loader = data_loader
        self.data_processor = data_processor

    def generate_full_summary(
        self,
        video_no: int,
        task_data: dict,
        window_ms: int,
        shift_ms: int,
    ) -> list[SummarySegment]:
        """
        Generates a full summary for a given video_no by processing the content in sliding windows.

        Args:
            video_no: The ID of the video to summarize.
            task_data: A dictionary containing metadata for the task (e.g., broadcast, platform info).
            window_ms: The size of each processing window in milliseconds.
            shift_ms: The step size for the sliding window in milliseconds.

        Returns:
            A list of SummarySegment objects, each representing a part of the summary.
        """
        raw_data = self.data_loader.get_contexts_from_jsonl(video_no)
        if not raw_data:
            return []

        windows = self.data_processor.create_sliding_windows(raw_data, window_ms, shift_ms)

        summaries: list[SummarySegment] = []
        prev_summary_content = None

        for i, window in enumerate(windows):
            if not window:
                continue

            start_ms = i * shift_ms
            end_ms = start_ms + window_ms
            context_prompt = self.data_processor.get_prompt_strings(window)

            current_task_data = task_data.copy()
            current_task_data["cur_context"] = context_prompt

            # "이전 요약 (없을 경우 비워둠)" is the alias for prev_summary
            if prev_summary_content:
                current_task_data["prev_summary"] = prev_summary_content

            summary_content = self.llm_task.short_term_summary(current_task_data)

            summary_segment = SummarySegment(
                start_ms=start_ms,
                end_ms=end_ms,
                content=summary_content,
            )
            summaries.append(summary_segment)

            prev_summary_content = summary_content

        return summaries
