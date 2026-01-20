import { TREND_CHART_MARGIN, TREND_CHART_X_AXIS_HEIGHT } from "@/features/analysis/constants";
import { getBarColor } from "@/features/analysis/utils";
import {
    ComposedChart, Line, Bar, XAxis, YAxis, Tooltip,
    Cell, ReferenceArea,
    ReferenceLine
} from "recharts";
import { TrendChartTooltip } from "./TrendChartTooltip";
import { formatVideoTime } from "@/utils/time-formatter";

interface TrendChartProps {
    data: any[];
    activeIndex: number | null;
    showVolume: boolean;
    showMomentum: boolean;
    fillBar: boolean;
    onChartClick: (timestamp: number) => void;
    width: number;
    height: number;
    yDomain: [number, number];
    xTicks: number[];
    xDomain: [number, number];
    barSize: number;
}

export function TrendChart({
    data,
    activeIndex,
    showVolume,
    showMomentum,
    fillBar,
    onChartClick,
    width,
    height,
    xDomain,
    xTicks,
    yDomain,
    barSize
}: TrendChartProps) {

    const activeData = activeIndex !== null ? data[activeIndex] : null;

    return (
        <ComposedChart
            width={width}
            height={height}
            data={data}
            margin={TREND_CHART_MARGIN}
            onClick={(e) => {
                if (e && e.activeIndex !== undefined) {
                    const selectedItem = data[Number(e.activeIndex)]
                    onChartClick(selectedItem.originalTimestamp);
                }
            }}
        >

            {/* ✅ [수정] XAxis: 시간 포맷 및 간격 조정 */}
            <XAxis
                dataKey="activeTimestamp" // 1. 숫자인 Timestamp(ms) 사용
                type="number"            // 2. 숫자 축으로 명시
                domain={xDomain}         // 3. [0, TotalDuration] 적용
                ticks={xTicks}
                tickFormatter={formatVideoTime} // 4. 숫자를 시간 문자열로 변환 (0 -> 00:00)
                allowDataOverflow={true}
                interval="preserveStartEnd" // 공간 부족 시 자동으로 건너뜀
                minTickGap={30}             // 최소 30px 간격 유지
                tick={{ fontSize: 10 }}
                height={TREND_CHART_X_AXIS_HEIGHT}
            />

            {/* ✅ [수정] YAxis: 실제 렌더링은 TrendYAxis가 담당하므로 여기서는 숨김 처리하되 도메인은 맞춤 */}
            <YAxis
                yAxisId="common"
                hide
                domain={yDomain}
            />

            <Tooltip
                content={<TrendChartTooltip />}
                cursor={{ fill: "transparent" }} // 커서 배경 투명하게 (바 그래프 강조를 위해)
                offset={60}
            />

            <ReferenceLine
                y={0.5}
                yAxisId="common"
                stroke="#ee4ce6ff"
                strokeDasharray="3 3"
                opacity={0.8}
            />

            {/* ReferenceArea (Current Indicator) */}
            {activeData !== null && (
                <ReferenceArea
                    yAxisId="common"
                    x1={activeData.startTime}
                    x2={activeData.endTime}
                    fill="#2564eb33"
                    fillOpacity={0.8}
                    ifOverflow="visible"
                />
            )}

            {showVolume && (
                <Bar
                    dataKey="activeVolume"
                    yAxisId="common"
                    barSize={barSize}
                    opacity={0.8}
                >
                    {data.map((entry: any, index: number) => (
                        <Cell
                            key={`cell-${index}`}
                            fill={fillBar ? getBarColor(entry.atmosphere) : getBarColor("Default")}
                            opacity={activeIndex === index ? 1 : 0.6}
                        />
                    ))}
                </Bar>
            )}

            {showMomentum && (
                <Line
                    type="monotone"
                    dataKey="activeMomentum"
                    yAxisId="common"
                    stroke="#2564ebbe"
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                />
            )}
        </ComposedChart>
    );
}
