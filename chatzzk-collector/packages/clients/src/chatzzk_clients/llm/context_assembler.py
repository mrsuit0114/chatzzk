from collections import deque
from collections.abc import AsyncGenerator, AsyncIterable
from typing import TypeVar

from loguru import logger
from pydantic import ValidationError

from chatzzk_core.schemas.config.clients.llm import ContextAssemblerConfig
from chatzzk_core.schemas.internal import ASREntry, BaseStreamEntry, SegmentSummaryEntry

T = TypeVar("T", bound=BaseStreamEntry)


class ContextAssembler:
    """
    [Stateless] 스트림 병합 및 윈도우잉 ETL 클래스.
    """

    def __init__(self, config: ContextAssemblerConfig):
        self._hallucination_keywords = config.hallucination_keywords

    async def get_windows(
        self,
        iterators: list[AsyncGenerator[T, None]],
        window_size_ms: int,
        step_size_ms: int = 0,
        padding_ms: int = 0,
        preprocess_chat: bool = True,
    ) -> AsyncGenerator[list[T], None]:
        # [State] 메서드 지역 변수로 버퍼 관리 (동시성 안전)
        window_buffer: deque[T] = deque()
        if step_size_ms == 0:
            step_size_ms = window_size_ms

        merged_stream = self._merge_streams(iterators)
        current_window_start = 0

        async for entry in merged_stream:
            # [Logic] 전처리 옵션 전달
            processed_entry = self._preprocess_entry(entry, preprocess_chat)
            if not processed_entry:
                continue

            window_end_limit = current_window_start + window_size_ms + padding_ms

            # 현재 데이터가 윈도우 범위를 넘어섰다면 윈도우 마감 반복
            while entry.timestamp >= window_end_limit:
                window_data = self._extract_window_data(window_buffer, current_window_start, window_size_ms, padding_ms)

                if window_data:
                    yield window_data

                current_window_start += step_size_ms
                window_end_limit = current_window_start + window_size_ms + padding_ms

                cleanup_threshold = current_window_start - padding_ms
                self._cleanup_buffer(window_buffer, cleanup_threshold)

            window_buffer.append(processed_entry)

        # 잔여 버퍼 처리
        while window_buffer:
            window_data = self._extract_window_data(window_buffer, current_window_start, window_size_ms, padding_ms)

            if window_data:
                yield window_data

            current_window_start += step_size_ms
            cleanup_threshold = current_window_start - padding_ms
            self._cleanup_buffer(window_buffer, cleanup_threshold)

            if not window_buffer:
                break

            # 버퍼의 첫 데이터가 현재 처리하려는 윈도우보다 훨씬 미래라면 종료
            if window_buffer[0].timestamp > current_window_start + window_size_ms + padding_ms:
                break

    def format_chapter_window_to_text(self, entries: list[SegmentSummaryEntry]) -> str:
        lines = []
        for entry in entries:
            try:
                lines.append(entry.to_context_string())
            except NotImplementedError:
                continue
        return "\n".join(lines)

    def format_segment_window_to_text(self, entries: list[T]) -> str:
        lines = []
        current_tag = None
        last_content = None
        current_minute = None

        for entry in entries:
            # --- timestamp 처리 ---
            ts_ms = entry.timestamp
            if ts_ms is not None:
                minute = ts_ms // 60000

                if minute != current_minute:
                    hh = minute // 60
                    mm = minute % 60
                    if lines:
                        lines.append(f"\n--- [{hh:02d}:{mm:02d}] ---\n")
                    else:
                        lines.append(f"--- [{hh:02d}:{mm:02d}] ---\n")
                    current_minute = minute

            try:
                raw = entry.to_context_string()
            except NotImplementedError:
                continue

            if not raw:
                continue

            end = raw.find("]")
            tag = raw[1:end]
            content = raw[end + 1 :].lstrip()

            # --- 블록 선언 로직 ---
            if tag != current_tag:
                if current_tag is not None:
                    lines.append("")
                lines.append(f"{tag}:")
                current_tag = tag
                last_content = None  # 태그 바뀌면 중복 검사 리셋

            # --- 동일 content 생략 ---
            if content == last_content:
                continue

            lines.append(content)
            last_content = content

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    def _preprocess_entry(self, entry: T, preprocess_chat: bool) -> T | None:
        """
        preprocess_chat=False 이면 ChatEntry의 sanitize를 호출하지 않고 원본을 반환.
        ASR 필터링은 항상 수행 (데이터 품질 최소 보장).
        """
        # 1. ASR 필터링 (항상 수행)
        if isinstance(entry, ASREntry):
            if entry.is_hallucination(self._hallucination_keywords):
                return None
            return entry.sanitize()

        # 2. Chat 및 기타 Entry
        if not preprocess_chat:
            return entry

        # 3. Chat 전처리 (LLM 용)
        sanitized_entry = entry.sanitize()
        if not sanitized_entry.content:
            return None

        return sanitized_entry

    def _extract_window_data(self, buffer: deque[T], start_ms: int, duration_ms: int, padding_ms: int) -> list[T]:
        real_start = start_ms - padding_ms
        real_end = start_ms + duration_ms + padding_ms

        # deque 순회 (시간순 정렬되어 있으므로 효율적)
        # Python 3.11에서도 리스트 컴프리헨션이 가장 Pythonic하고 빠름
        return [e for e in buffer if real_start <= e.timestamp < real_end]

    def _cleanup_buffer(self, buffer: deque[T], threshold_time_ms: int):
        # popleft는 O(1)이므로 효율적임
        while buffer and buffer[0].timestamp < threshold_time_ms:
            buffer.popleft()

    async def _merge_streams(self, iterators: list[AsyncGenerator[T, None]]) -> AsyncGenerator[T, None]:
        # 스트림 초기화
        streams = []
        for gen in iterators:
            try:
                first_val = await anext(gen)
                streams.append({"gen": gen, "next_val": first_val})
            except StopAsyncIteration:
                pass

        while streams:
            # Min 찾기 (선형 탐색, N이 작으므로 충분히 빠름)
            min_idx = 0
            for i in range(1, len(streams)):
                if streams[i]["next_val"] < streams[min_idx]["next_val"]:
                    min_idx = i

            target = streams[min_idx]
            yield target["next_val"]

            # 선택된 스트림 전진
            try:
                target["next_val"] = await anext(target["gen"])
            except StopAsyncIteration:
                streams.pop(min_idx)

    async def as_model_stream(
        self,
        stream: AsyncIterable[dict],
        model: type[T],
    ) -> AsyncIterable[T]:
        async for item in stream:
            try:
                yield model.model_validate(item)
            except ValidationError as e:
                logger.warning(f"⚠️ Skipping invalid model data: {e}")
                continue
