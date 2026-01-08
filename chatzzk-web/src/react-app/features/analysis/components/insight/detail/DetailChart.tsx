import { useMemo } from "react";
import {
    ComposedChart,
    Bar,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    ReferenceArea,
    ResponsiveContainer,
    Cell,
    ReferenceLine
} from "recharts";
import { formatTime, scaleMomentum } from "@/features/analysis/utils";
import { ClipData } from "../../../types";
import { DetailChartTooltip } from "./DetailChartTooltip";
import { DETAIL_CHART_HEIGHT } from "@/features/analysis/constants";

interface DetailChartProps {
    data: ClipData[];
    segmentRange: { start: number; end: number } | null;
    focusedTimestamp: number | null;
    onSeek: (timestamp: number) => void;
    xDomain: [number, number];
}


export function DetailChart({
    data,
    segmentRange,
    focusedTimestamp,
    onSeek,
    xDomain,
}: DetailChartProps) {

    // 1. 데이터 가공: Scaling 적용 (Momentum & Volume)
    const { chartData } = useMemo(() => {
        if (data.length === 0) return { chartData: [] };

        const processed = data.map(clip => ({
            ...clip,
            // X축 데이터
            startTime: clip.startTime,
            endTime: clip.endTime,

            Volume: clip.volume,
            scaledMomentum: scaleMomentum(clip.momentum),

            originalMomentum: clip.momentum,
        }));

        return { chartData: processed };
    }, [data]);

    const handleClick = (state: any) => {
        if (state && state.activeTooltipIndex !== undefined) {
            const item = chartData[state.activeTooltipIndex];
            if (item) onSeek(item.startTime);
        }
    };

    return (
        <div className="w-full select-none">
            <ResponsiveContainer width="100%" height={DETAIL_CHART_HEIGHT}>
                <ComposedChart
                    data={chartData}
                    margin={{ top: 0, right: 10, left: 0, bottom: 0 }}
                    onClick={handleClick}
                >

                    <XAxis
                        dataKey="startTime"
                        type="number"
                        domain={xDomain}
                        tickFormatter={(val) => formatTime(val)}
                        tick={{ fontSize: 10, fill: '#64748b' }}
                        interval="preserveStartEnd"
                        minTickGap={30}
                        height={20}
                        allowDataOverflow={true}
                    />

                    <YAxis
                        width={30}
                        domain={[0, 1.1]}
                        ticks={[0, 0.25, 0.5, 0.75, 1]}
                        tick={{ fontSize: 10, fill: '#64748b' }}
                    />

                    <ReferenceLine
                        y={1.1}
                        stroke="#e2e8f0"
                    />

                    <ReferenceLine
                        y={0.5}
                        stroke="#ee4ce6ff"
                        strokeDasharray="3 3"
                    />

                    <Tooltip
                        content={<DetailChartTooltip />}
                        cursor={{ fill: '#f1f5f9', opacity: 0.5 }}
                    />

                    {segmentRange && (
                        <ReferenceArea
                            yAxisId={0}
                            x1={segmentRange.start}
                            x2={segmentRange.end}
                            fill="#2564ebff"
                            fillOpacity={0.08}
                            ifOverflow="visible"
                        />
                    )}

                    <Bar
                        dataKey="volume"
                        barSize={4}
                        fill="#fb923c"
                        isAnimationActive={false}
                    >
                        {chartData.map((entry, index) => {
                            const isActive = focusedTimestamp !== null &&
                                focusedTimestamp >= entry.startTime &&
                                focusedTimestamp < entry.endTime;
                            return (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={isActive ? "#ea580c" : "#fdba74"}
                                    opacity={isActive ? 1 : 0.7}
                                />
                            );
                        })}
                    </Bar>

                    <Line
                        type="monotone"
                        dataKey="scaledMomentum"
                        stroke="#2564eb"
                        strokeWidth={1.5}
                        dot={false}
                        isAnimationActive={false}
                    />
                </ComposedChart>
            </ResponsiveContainer>
        </div>
    );
}
