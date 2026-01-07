import { TREND_CHART_MARGIN, TREND_CHART_X_AXIS_HEIGHT } from "@/features/analysis/constants";
import { Bar, ComposedChart, XAxis, YAxis } from "recharts";


interface TrendYAxisProps {
    height: number;
    yDomain: [number | 'auto', number | 'auto']; // 메인 차트와 동기화된 범위
}

export function TrendYAxis({ height, yDomain }: TrendYAxisProps) {
    // 렌더링 트리거용 더미 데이터
    const dummyData = [{ name: 'dummy', value: 0 }];
    const AXIS_WIDTH = 40;

    return (
        <div
            style={{ width: AXIS_WIDTH, height: height }}
            className="shrink-0 bg-background z-10 border-r"
        >
            <ComposedChart
                width={AXIS_WIDTH}
                height={height}
                data={dummyData} // ✅  데이터가 있어야 축이 그려짐
                margin={TREND_CHART_MARGIN}
            >
                {/* ✅ [핵심 2] 메인 차트와 레이아웃(높이) 싱크를 맞추기 위한 투명 X축 */}
                <XAxis
                    height={TREND_CHART_X_AXIS_HEIGHT}
                    tick={false}
                    axisLine={false}
                />

                <YAxis
                    yAxisId="left"
                    orientation="left"
                    domain={yDomain}
                    ticks={[0, 0.25, 0.5, 0.75, 1]}
                    tick={{ fontSize: 12, fill: "#666" }}
                    axisLine={false}
                    tickLine={true}
                    width={AXIS_WIDTH}
                    interval={0} // 모든 눈금 표시 강제
                />

                {/* ✅ [핵심 3] 차트 렌더링을 확실하게 트리거하기 위한 숨겨진 바 */}
                <Bar dataKey="value" yAxisId="left" style={{ display: 'none' }} />
            </ComposedChart>
        </div>
    );
}
