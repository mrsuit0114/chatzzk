import json
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# 페이지 설정
st.set_page_config(page_title="개인 방송 데이터 분석", layout="wide")

# 타입 코드 정의
TYPE_CODES = {100: "채팅", 1000: "후원", 10000: "ASR"}


def load_jsonl(file):
    """JSONL 파일 로드"""
    data = []
    for line in file.getvalue().decode("utf-8").strip().split("\n"):
        if line.strip():
            data.append(json.loads(line))
    return data


def format_duration(ms):
    """밀리초를 시:분:초 형식으로 변환"""
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def get_file_id(filename):
    """파일명에서 숫자 ID 추출"""
    try:
        return os.path.splitext(filename)[0]
    except Exception:
        return None


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


def create_timeline_chart(df):
    """시간별 채팅/도네이션 개수 그래프"""
    # 시간대별로 그룹화 (1분 단위)
    df["minute"] = (df["timestamp_ms"] / (1000 * 60)).astype(int)

    timeline_data = []
    for minute in range(df["minute"].max() + 1):
        minute_data = df[df["minute"] == minute]
        chat_count = len(minute_data[minute_data["type_code"] == 100])
        donation_count = len(minute_data[minute_data["type_code"] == 1000])

        timeline_data.append({"minute": minute, "chat_count": chat_count, "donation_count": donation_count})

    timeline_df = pd.DataFrame(timeline_data)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(x=timeline_df["minute"], y=timeline_df["chat_count"], name="채팅 개수", line={"color": "blue"}),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=timeline_df["minute"], y=timeline_df["donation_count"], name="후원 개수", line={"color": "red"}),
        secondary_y=True,
    )

    fig.update_xaxes(title_text="시간 (분)")
    fig.update_yaxes(title_text="채팅 개수", secondary_y=False)
    fig.update_yaxes(title_text="후원 개수", secondary_y=True)
    fig.update_layout(title="시간별 채팅 및 후원 개수")

    return fig


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


def main():
    st.title("🎥 개인 방송 데이터 분석")

    # 사이드바 - 파일 업로드
    st.sidebar.header("📁 파일 업로드")

    context_file = st.sidebar.file_uploader(
        "Context 파일 (JSONL)", type=["jsonl"], help="채팅, 오디오, 후원 데이터가 포함된 JSONL 파일"
    )

    summary_file = st.sidebar.file_uploader(
        "Short Term Summary 파일 (JSONL)", type=["jsonl"], help="요약 데이터가 포함된 JSONL 파일"
    )

    if context_file is None or summary_file is None:
        st.info("📤 Context와 Short Term Summary 파일을 모두 업로드해주세요.")
        return

    # 파일명 검증
    context_id = get_file_id(context_file.name)
    summary_id = get_file_id(summary_file.name)

    if context_id != summary_id:
        st.error("⚠️ 두 파일의 이름이 다릅니다. 같은 방송의 데이터인지 확인해주세요.")
        st.info(f"Context 파일 ID: {context_id}")
        st.info(f"Summary 파일 ID: {summary_id}")
        return

    # 데이터 로드
    try:
        context_data = load_jsonl(context_file)
        summary_data = load_jsonl(summary_file)

        st.success(f"✅ 데이터 로드 완료 (방송 ID: {context_id})")
        st.info(f"Context 데이터: {len(context_data)}개, Summary 데이터: {len(summary_data)}개")

    except Exception as e:
        st.error(f"❌ 파일 로드 중 오류 발생: {e}")
        return

    # 분석 실행
    analysis = analyze_context_data(context_data)

    if analysis is None:
        st.error("❌ 데이터 분석 실패")
        return

    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs(["📊 전체 분석", "📝 요약 기준 분석", "💬 채팅 기준 분석", "⭐ 하이라이트 추천"])

    # 전체 분석 탭
    with tab1:
        st.header("📊 전체 분석")

        # 기본 정보
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("방송 시간", format_duration(analysis["total_duration_ms"]))

        with col2:
            st.metric("채팅 개수", f"{analysis['chat_count']:,}개")

        with col3:
            st.metric("후원 개수", f"{analysis['donation_count']}개")

        with col4:
            st.metric("후원 총액", f"{analysis['total_donation']:,}원")

        # 속도 정보
        col5, col6 = st.columns(2)

        with col5:
            st.metric("채팅 속도", f"{analysis['chat_rate']:.1f}개/분")

        with col6:
            st.metric("후원 속도", f"{analysis['donation_rate']:.1f}개/분")

        # 시간별 그래프
        st.subheader("시간별 채팅 및 후원 추이")
        timeline_chart = create_timeline_chart(analysis["df"])
        st.plotly_chart(timeline_chart, use_container_width=True)

    # 요약 기준 분석 탭
    with tab2:
        st.header("📝 요약 기준 분석")

        summary_df = pd.DataFrame(summary_data)

        # 각 요약에 대한 정보 계산
        summary_analysis = []

        for idx, row in summary_df.iterrows():
            context_subset = get_context_for_summary(analysis["df"], row["start_ms"], row["end_ms"])

            chat_count = len(context_subset[context_subset["type_code"] == 100])
            donation_count = len(context_subset[context_subset["type_code"] == 1000])

            summary_analysis.append(
                {
                    "index": idx,
                    "start_formatted": format_duration(row["start_ms"]),
                    "end_formatted": format_duration(row["end_ms"]),
                    "content": row["content"][:100] + "..." if len(row["content"]) > 100 else row["content"],
                    "chat_count": chat_count,
                    "donation_count": donation_count,
                    "total_activity": chat_count + donation_count,
                }
            )

        summary_analysis_df = pd.DataFrame(summary_analysis)

        # 정렬 옵션
        sort_option = st.selectbox("정렬 기준", ["시간순", "채팅 개수", "후원 개수", "전체 활동"])

        if sort_option == "채팅 개수":
            summary_analysis_df = summary_analysis_df.sort_values("chat_count", ascending=False)
        elif sort_option == "후원 개수":
            summary_analysis_df = summary_analysis_df.sort_values("donation_count", ascending=False)
        elif sort_option == "전체 활동":
            summary_analysis_df = summary_analysis_df.sort_values("total_activity", ascending=False)

        # 요약 선택
        st.subheader("요약 목록")

        for idx, row in summary_analysis_df.iterrows():
            with st.expander(
                f"🕐 {row['start_formatted']} - {row['end_formatted']} (채팅: {row['chat_count']}, 후원: {row['donation_count']})"
            ):
                st.write("**요약 내용:**")
                st.write(summary_data[row["index"]]["content"])

                # 해당 구간의 컨텍스트 표시
                context_subset = get_context_for_summary(
                    analysis["df"], summary_data[row["index"]]["start_ms"], summary_data[row["index"]]["end_ms"]
                )

                if not context_subset.empty:
                    st.write("**구간 내 활동:**")
                    formatted_context = format_context_display(context_subset)
                    st.dataframe(formatted_context, use_container_width=True)

    # 채팅 기준 분석 탭
    with tab3:
        st.header("💬 채팅 기준 분석")

        # 설정
        col1, col2, col3 = st.columns(3)

        with col1:
            window_seconds = st.number_input("윈도우 크기 (초)", min_value=10, max_value=300, value=30)

        with col2:
            include_chat = st.checkbox("채팅 포함", value=True)

        with col3:
            include_donation = st.checkbox("후원 포함", value=False)

        if include_chat or include_donation:
            window_analysis = analyze_sliding_window(analysis["df"], window_seconds, include_chat, include_donation)

            if not window_analysis.empty:
                # 통계 정보
                st.subheader("📈 구간별 통계")

                most_active = window_analysis.loc[window_analysis["total_count"].idxmax()]
                least_active = window_analysis.loc[window_analysis["total_count"].idxmin()]

                col1, col2 = st.columns(2)

                with col1:
                    st.metric(
                        "가장 활발한 시점",
                        f"{most_active['start_formatted']} - {most_active['end_formatted']}",
                        f"{most_active['total_count']}개 ({most_active['rate_per_minute']:.1f}개/분)",
                    )

                with col2:
                    st.metric(
                        "가장 저조한 시점",
                        f"{least_active['start_formatted']} - {least_active['end_formatted']}",
                        f"{least_active['total_count']}개 ({least_active['rate_per_minute']:.1f}개/분)",
                    )

                # 그래프
                fig = px.bar(
                    window_analysis,
                    x="start_formatted",
                    y="total_count",
                    title="윈도우별 활동 개수",
                    labels={"start_formatted": "시작 시간", "total_count": "활동 개수"},
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

                # 상세 데이터
                st.subheader("📊 구간별 상세 데이터")
                st.dataframe(
                    window_analysis[
                        [
                            "start_formatted",
                            "end_formatted",
                            "chat_count",
                            "donation_count",
                            "total_count",
                        ]
                    ],
                    use_container_width=True,
                )

                # 컨텍스트 확인
                st.subheader("🔍 특정 구간 컨텍스트 확인")
                window_options = [
                    f"{idx}: {row['start_formatted']} - {row['end_formatted']}"
                    for idx, row in window_analysis.iterrows()
                ]
                selected_window_option = st.selectbox("확인할 구간을 선택하세요.", options=window_options)

                if selected_window_option:
                    selected_idx = int(selected_window_option.split(":")[0])
                    selected_window = window_analysis.loc[selected_idx]

                    context_subset = get_context_for_summary(
                        analysis["df"], selected_window["start_time"], selected_window["end_time"]
                    )

                    if not context_subset.empty:
                        st.write(
                            f"**{selected_window['start_formatted']} - {selected_window['end_formatted']} 구간 내 활동:**"
                        )
                        formatted_context = format_context_display(context_subset)
                        st.dataframe(formatted_context, use_container_width=True)
                    else:
                        st.write("해당 구간에 활동이 없습니다.")

    # 하이라이트 추천 탭
    with tab4:
        st.header("⭐ 하이라이트 및 클립 추천")

        # 설정
        col1, col2, col3 = st.columns(3)

        with col1:
            min_window = st.number_input("최소 윈도우 (초)", min_value=10, max_value=120, value=30)

        with col2:
            max_window = st.number_input("최대 윈도우 (초)", min_value=60, max_value=600, value=60)

        with col3:
            threshold = st.number_input("임계값 배수", min_value=0.5, max_value=5.0, value=1.5, step=0.1)

        if st.button("🔍 하이라이트 분석 실행"):
            overall_chat_rate = analysis["chat_rate"]
            threshold_rate = overall_chat_rate * threshold

            st.info(f"방송 전체 분당 채팅 수: {overall_chat_rate:.1f}개/분")

            highlights = find_highlights(analysis["df"], min_window, max_window, threshold, overall_chat_rate)

            if not highlights.empty:
                st.success(
                    f"✅ {len(highlights)}개의 하이라이트 구간을 발견했습니다! (임계값: {threshold_rate:.1f}개/분)"
                )

                # 정렬
                highlights = highlights.sort_values("chat_rate", ascending=False)

                # 하이라이트 목록
                for idx, highlight in highlights.iterrows():
                    with st.expander(
                        f"🎬 하이라이트 #{idx + 1} ({highlight['start_formatted']} - {highlight['end_formatted']}) - 채팅 속도: {highlight['chat_rate']:.1f}개/분"
                    ):
                        st.write(f"**구간:** {highlight['start_formatted']} ~ {highlight['end_formatted']}")
                        st.write(f"**지속시간:** {highlight['duration_seconds']:.0f}초")
                        st.write(f"**채팅 속도:** {highlight['chat_rate']:.1f}개/분")

                        # Find and display related summaries
                        related_summaries = []
                        for summary in summary_data:
                            if (summary["start_ms"] <= highlight["end_time"]) and (
                                summary["end_ms"] >= highlight["start_time"]
                            ):
                                related_summaries.append(summary)

                        if related_summaries:
                            st.write("**관련 요약:**")
                            for summary in related_summaries:
                                st.write(
                                    f"- *({format_duration(summary['start_ms'])} ~ {format_duration(summary['end_ms'])})*"
                                )
                                st.write(summary["content"])
                        else:
                            st.write("**관련 요약:** 없음")

                        # 해당 구간의 컨텍스트 표시
                        context_subset = get_context_for_summary(
                            analysis["df"], highlight["start_time"], highlight["end_time"]
                        )

                        if not context_subset.empty:
                            st.write("**구간 내 활동:**")
                            formatted_context = format_context_display(context_subset)
                            st.dataframe(formatted_context, use_container_width=True)
            else:
                st.warning("⚠️ 설정한 조건에 맞는 하이라이트 구간을 찾을 수 없습니다. 임계값을 낮춰보세요.")


if __name__ == "__main__":
    main()
