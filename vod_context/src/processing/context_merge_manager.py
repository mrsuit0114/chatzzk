from heapq import merge

from common.schemas.context_data import ContextData


class ContextMergeManager:
    @staticmethod
    def merge_context(
        chat_context: list[ContextData], asr_context: list[ContextData], asr_offset_ms: int = 0
    ) -> list[ContextData]:
        if asr_offset_ms != 0:
            for ctx in asr_context:
                ctx.timestamp_ms += asr_offset_ms

        merged_data = list(merge(chat_context, asr_context, key=lambda x: x.timestamp_ms))
        return merged_data
