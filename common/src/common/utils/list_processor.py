import bisect

from common.schemas.context_data import ContextData


def create_sliding_windows(contexts: list[ContextData], window_ms: int, shift_ms: int) -> list[list[ContextData]]:
    """
    Creates sliding windows of ContextData based on timestamps using bisect for performance.

    Args:
        contexts: A list of ContextData objects, assumed to be sorted by timestamp_ms.
        window_ms: The size of each window in milliseconds.
        shift_ms: The step size (stride) for the sliding window in milliseconds.

    Returns:
        A list of lists, where each inner list is a window of ContextData.
    """
    if not contexts:
        return []

    windows = []
    timestamps = [c.timestamp_ms for c in contexts]

    start_ts = 0
    max_ts = timestamps[-1]

    current_window_start_ts = start_ts
    search_start_idx = 0

    while current_window_start_ts <= max_ts:
        current_window_end_ts = current_window_start_ts + window_ms

        # Find window boundaries using binary search
        start_idx = bisect.bisect_left(timestamps, current_window_start_ts, lo=search_start_idx)
        end_idx = bisect.bisect_left(timestamps, current_window_end_ts, lo=start_idx)

        if start_idx < end_idx:
            windows.append(contexts[start_idx:end_idx])

        # Move to the next window
        current_window_start_ts += shift_ms
        search_start_idx = start_idx

    return windows


def slice_by_timestamp(contexts: list[ContextData], start_ms: int, length_ms: int) -> list[ContextData]:
    """
    Filters a list of ContextData to a specific time range.

    Args:
        contexts: A list of ContextData objects, assumed to be sorted by timestamp_ms.
        start_ms: The start of the time range in milliseconds (inclusive).
        end_ms: The end of the time range in milliseconds (exclusive).

    Returns:
        A new list of ContextData objects within the specified time range.
    """
    end_ms = start_ms + length_ms
    return [context for context in contexts if start_ms <= context.timestamp_ms < end_ms]
