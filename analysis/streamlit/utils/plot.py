import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_timeline_chart(df):
    """시간별 채팅/도네이션 개수 그래프"""
    # 시간대별로 그룹화 (1분 단위)
    df["minute"] = (df["timestamp_ms"] / (1000 * 60)).astype(int)

    timeline_data = []
    # Ensure minute range is not empty
    max_minute = 0
    if not df.empty:
        max_minute = df["minute"].max()

    for minute in range(max_minute + 1):
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
