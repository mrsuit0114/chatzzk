import pandas as pd

from .helpers import TYPE_CODES, format_duration


def analyze_context_data(context_data):
    """Context 데이터 분석"""
    if not context_data:
        return None

    df = pd.DataFrame(context_data)

    # 전체 방송 시간
    total_duration_ms = df["timestamp_ms"].max()
    total_duration_minutes = total_duration_ms / (1000 * 60)

    # 타입별 개수 계산
    chat_count = len(df[df["type_code"] == 100])
    donation_count = len(df[df["type_code"] == 1000])
    audio_count = len(df[df["type_code"] == 10000])

    # 후원 총액
    total_donation = df[df["type_code"] == 1000]["pay_amount"].sum()

    # 속도 계산 (개수/분)
    chat_rate = chat_count / total_duration_minutes if total_duration_minutes > 0 else 0
    donation_rate = donation_count / total_duration_minutes if total_duration_minutes > 0 else 0

    return {
        "total_duration_ms": total_duration_ms,
        "total_duration_minutes": total_duration_minutes,
        "chat_count": chat_count,
        "donation_count": donation_count,
        "audio_count": audio_count,
        "total_donation": total_donation,
        "chat_rate": chat_rate,
        "donation_rate": donation_rate,
        "df": df,
    }


def get_context_for_summary(context_df, start_ms, end_ms):
    """요약 구간에 해당하는 컨텍스트 데이터 추출"""
    mask = (context_df["timestamp_ms"] >= start_ms) & (context_df["timestamp_ms"] <= end_ms)
    return context_df[mask].copy()


def format_context_display(context_data):
    """컨텍스트 데이터를 표시용으로 포맷팅"""
    if context_data.empty:
        return pd.DataFrame()

    display_data = context_data.copy()
    display_data["type_name"] = display_data["type_code"].map(TYPE_CODES)
    display_data["timestamp_formatted"] = display_data["timestamp_ms"].apply(format_duration)

    return display_data[["timestamp_formatted", "type_name", "content", "pay_amount"]]


def analyze_sliding_window(context_df, window_seconds, include_chat=True, include_donation=False):
    """슬라이딩 윈도우 방식으로 분석"""
    if context_df.empty:
        return pd.DataFrame()

    window_ms = window_seconds * 1000
    max_timestamp = context_df["timestamp_ms"].max()

    results = []
    start_time = 0

    while start_time <= max_timestamp:
        end_time = start_time + window_ms

        window_data = context_df[(context_df["timestamp_ms"] >= start_time) & (context_df["timestamp_ms"] < end_time)]

        chat_count = len(window_data[window_data["type_code"] == 100]) if include_chat else 0
        donation_count = len(window_data[window_data["type_code"] == 1000]) if include_donation else 0
        total_count = chat_count + donation_count

        # 해당 구간이 포함된 요약 찾기
        summary_info = "해당 없음"

        results.append(
            {
                "start_time": start_time,
                "end_time": min(end_time, max_timestamp),
                "start_formatted": format_duration(start_time),
                "end_formatted": format_duration(min(end_time, max_timestamp)),
                "chat_count": chat_count,
                "donation_count": donation_count,
                "total_count": total_count,
                "rate_per_minute": total_count * 60 / window_seconds,
                "summary_info": summary_info,
            }
        )

        start_time += window_ms

    return pd.DataFrame(results)


def find_highlights(context_df, min_window, max_window, threshold, overall_rate):
    """하이라이트 구간 찾기"""
    if context_df.empty:
        return pd.DataFrame()

    min_window_ms = min_window * 1000
    max_window_ms = max_window * 1000
    threshold_rate = overall_rate * threshold

    # 최소 윈도우로 슬라이딩 윈도우 실행
    candidates = []
    max_timestamp = context_df["timestamp_ms"].max()

    start_time = 0
    while start_time <= max_timestamp:
        end_time = start_time + min_window_ms

        window_data = context_df[(context_df["timestamp_ms"] >= start_time) & (context_df["timestamp_ms"] < end_time)]

        chat_count = len(window_data[window_data["type_code"] == 100])
        rate = chat_count * 60 / min_window  # 분당 채팅 수

        if rate >= threshold_rate:
            candidates.append({"start_time": start_time, "end_time": end_time, "rate": rate})

        start_time += min_window_ms

    # 인접한 구간 병합
    highlights = []
    if candidates:
        current_highlight = candidates[0].copy()

        for i in range(1, len(candidates)):
            candidate = candidates[i]

            # 현재 하이라이트와 인접하고 최대 윈도우를 초과하지 않는 경우
            if (
                candidate["start_time"] <= current_highlight["end_time"]
                and candidate["end_time"] - current_highlight["start_time"] <= max_window_ms
            ):
                current_highlight["end_time"] = candidate["end_time"]
                current_highlight["rate"] = max(current_highlight["rate"], candidate["rate"])
            else:
                highlights.append(current_highlight)
                current_highlight = candidate.copy()

        highlights.append(current_highlight)

    # DataFrame으로 변환
    highlight_data = []
    for highlight in highlights:
        duration_seconds = (highlight["end_time"] - highlight["start_time"]) / 1000

        highlight_data.append(
            {
                "start_time": highlight["start_time"],
                "end_time": highlight["end_time"],
                "start_formatted": format_duration(highlight["start_time"]),
                "end_formatted": format_duration(highlight["end_time"]),
                "duration_seconds": duration_seconds,
                "chat_rate": highlight["rate"],
            }
        )

    return pd.DataFrame(highlight_data)
