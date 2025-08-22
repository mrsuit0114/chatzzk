import pandas as pd
import plotly.express as px
import streamlit as st

from utils.analysis import (
    analyze_context_data,
    analyze_sliding_window,
    find_highlights,
    format_context_display,
    get_context_for_summary,
)
from utils.data import load_jsonl
from utils.helpers import format_duration, get_file_id
from utils.plot import create_timeline_chart

st.set_page_config(page_title="개인 방송 데이터 분석", layout="wide")


def render_overall_analysis_tab(analysis, summary_data):
    """Render the overall analysis tab."""
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

    st.subheader("📝 전체 요약 목록")

    window_minutes = st.number_input("윈도우 크기 (분)", min_value=5, max_value=300, value=5, step=5)

    if summary_data:
        window_ms = window_minutes * 60 * 1000
        max_timestamp = analysis["total_duration_ms"]

        start_time = 0
        while start_time <= max_timestamp:
            end_time = start_time + window_ms

            # Find summary objects that overlap with the window
            window_summaries = [s for s in summary_data if s["start_ms"] < end_time and s["end_ms"] > start_time]

            if window_summaries:
                # Get the min/max time from the actual summaries in the window
                min_summary_time = min(s["start_ms"] for s in window_summaries)
                max_summary_time = max(s["end_ms"] for s in window_summaries)

                start_formatted = format_duration(min_summary_time)
                end_formatted = format_duration(max_summary_time)

                st.markdown("---")
                st.markdown(f"### 🕐 {start_formatted} - {end_formatted}")
                st.write("**요약 내용:**")

                summary_contents = [s["content"] for s in window_summaries]
                full_summary = "<br><br>".join(summary_contents)
                st.markdown(full_summary, unsafe_allow_html=True)

            start_time += window_ms
    else:
        st.info("업로드된 요약 데이터가 없습니다.")


def render_summary_analysis_tab(analysis, summary_data):
    """Render the summary analysis tab."""
    st.header("📝 요약 기준 분석")

    summary_df = pd.DataFrame(summary_data)
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
    sort_option = st.selectbox("정렬 기준", ["시간순", "채팅 개수", "후원 개수", "전체 활동"])

    if sort_option == "채팅 개수":
        summary_analysis_df = summary_analysis_df.sort_values("chat_count", ascending=False)
    elif sort_option == "후원 개수":
        summary_analysis_df = summary_analysis_df.sort_values("donation_count", ascending=False)
    elif sort_option == "전체 활동":
        summary_analysis_df = summary_analysis_df.sort_values("total_activity", ascending=False)

    st.subheader("요약 목록")
    for _, row in summary_analysis_df.iterrows():
        with st.expander(
            f"🕐 {row['start_formatted']} - {row['end_formatted']} (채팅: {row['chat_count']}, 후원: {row['donation_count']})"
        ):
            st.write("**요약 내용:**")
            original_summary = summary_data[row["index"]]
            st.write(original_summary["content"])
            context_subset = get_context_for_summary(
                analysis["df"], original_summary["start_ms"], original_summary["end_ms"]
            )
            if not context_subset.empty:
                st.write("**구간 내 활동:**")
                formatted_context = format_context_display(context_subset)
                st.dataframe(formatted_context, use_container_width=True)


def render_chat_analysis_tab(analysis):
    """Render the chat analysis tab."""
    st.header("💬 채팅 기준 분석")

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

            fig = px.bar(
                window_analysis,
                x="start_formatted",
                y="total_count",
                title="윈도우별 활동 개수",
                labels={"start_formatted": "시작 시간", "total_count": "활동 개수"},
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📊 구간별 상세 데이터")
            st.dataframe(
                window_analysis[["start_formatted", "end_formatted", "chat_count", "donation_count", "total_count"]],
                use_container_width=True,
            )

            st.subheader("🔍 특정 구간 컨텍스트 확인")
            window_options = [
                f"{idx}: {row['start_formatted']} - {row['end_formatted']}" for idx, row in window_analysis.iterrows()
            ]
            selected_option = st.selectbox("확인할 구간을 선택하세요.", options=window_options)
            if selected_option:
                selected_idx = int(selected_option.split(":")[0])
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


def render_highlight_analysis_tab(analysis, summary_data):
    """Render the highlight analysis tab."""
    st.header("⭐ 하이라이트 및 클립 추천")

    col1, col2, col3 = st.columns(3)
    with col1:
        min_window = st.number_input("최소 윈도우 (초)", min_value=10, max_value=120, value=30, key="min_window")
    with col2:
        max_window = st.number_input("최대 윈도우 (초)", min_value=60, max_value=600, value=60, key="max_window")
    with col3:
        threshold = st.number_input("임계값 배수", min_value=0.5, max_value=5.0, value=1.5, step=0.1, key="threshold")

    if st.button("🔍 하이라이트 분석 실행"):
        overall_chat_rate = analysis["chat_rate"]
        threshold_rate = overall_chat_rate * threshold
        highlights = find_highlights(analysis["df"], min_window, max_window, threshold, overall_chat_rate)
        st.info(
            f"방송 전체 분당 채팅 수: {overall_chat_rate:.1f}개/분, 하이라이트 조건: {threshold_rate:.1f}개/분 이상"
        )

        if not highlights.empty:
            st.success(f"✅ {len(highlights)}개의 하이라이트 구간을 발견했습니다!")
            highlights = highlights.sort_values("chat_rate", ascending=False)
            for idx, highlight in highlights.iterrows():
                with st.expander(
                    f"🎬 하이라이트 #{idx + 1} ({highlight['start_formatted']} - {highlight['end_formatted']}) - 채팅 속도: {highlight['chat_rate']:.1f}개/분"
                ):
                    st.write(f"**구간:** {highlight['start_formatted']} ~ {highlight['end_formatted']}")
                    st.write(f"**지속시간:** {highlight['duration_seconds']:.0f}초")
                    st.write(f"**채팅 속도:** {highlight['chat_rate']:.1f}개/분")

                    related_summaries = [
                        s
                        for s in summary_data
                        if s["start_ms"] <= highlight["end_time"] and s["end_ms"] >= highlight["start_time"]
                    ]
                    if related_summaries:
                        st.write("**관련 요약:**")
                        for summary in related_summaries:
                            st.write(
                                f"- *({format_duration(summary['start_ms'])} ~ {format_duration(summary['end_ms'])})*"
                            )
                            st.write(summary["content"])
                    else:
                        st.write("**관련 요약:** 없음")

                    context_subset = get_context_for_summary(
                        analysis["df"], highlight["start_time"], highlight["end_time"]
                    )
                    if not context_subset.empty:
                        st.write("**구간 내 활동:**")
                        formatted_context = format_context_display(context_subset)
                        st.dataframe(formatted_context, use_container_width=True)
        else:
            st.warning("⚠️ 설정한 조건에 맞는 하이라이트 구간을 찾을 수 없습니다. 임계값을 낮춰보세요.")


def main():
    """Main function to run the Streamlit app."""
    st.title("🎥 개인 방송 데이터 분석")

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

    context_id = get_file_id(context_file.name)
    summary_id = get_file_id(summary_file.name)

    if context_id != summary_id:
        st.error("⚠️ 두 파일의 이름이 다릅니다. 같은 방송의 데이터인지 확인해주세요.")
        st.info(f"Context 파일 ID: {context_id}")
        st.info(f"Summary 파일 ID: {summary_id}")
        return

    try:
        context_data = load_jsonl(context_file)
        summary_data = load_jsonl(summary_file)
        st.success(f"✅ 데이터 로드 완료 (방송 ID: {context_id})")
        st.info(f"Context 데이터: {len(context_data)}개, Summary 데이터: {len(summary_data)}개")
    except Exception as e:
        st.error(f"❌ 파일 로드 중 오류 발생: {e}")
        return

    analysis = analyze_context_data(context_data)
    if analysis is None:
        st.error("❌ 데이터 분석 실패")
        return

    tab1, tab2, tab3, tab4 = st.tabs(["📊 전체 분석", "📝 요약 기준 분석", "💬 채팅 기준 분석", "⭐ 하이라이트 추천"])

    with tab1:
        render_overall_analysis_tab(analysis, summary_data)
    with tab2:
        render_summary_analysis_tab(analysis, summary_data)
    with tab3:
        render_chat_analysis_tab(analysis)
    with tab4:
        render_highlight_analysis_tab(analysis, summary_data)


if __name__ == "__main__":
    main()
