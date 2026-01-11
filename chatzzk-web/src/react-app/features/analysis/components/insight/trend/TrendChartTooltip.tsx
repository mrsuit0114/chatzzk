import { ATMOSPHERE_LABELS } from "@/constants";
import { formatVideoTime, getBarColor } from "@/features/analysis/utils";


export const TrendChartTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
        // payload[0].payload에 우리가 주입한 chartData 객체 전체가 들어있습니다.
        const data = payload[0].payload;

        return (
            <div className="bg-white/85 border border-slate-200 p-3 rounded-lg shadow-lg text-xs min-w-[180px] max-w-[300px] z-50">
                {/* 1. 시간 정보 (원본 시간 사용) */}
                <div className="mb-2">
                    <p className="font-bold text-slate-800">
                        {formatVideoTime(data.startTime)} ~ {formatVideoTime(data.endTime)}
                    </p>

                    {/* ✅ [추가] Peak Timestamp가 있을 경우에만 표시 */}
                    {data.peakTimestamp !== null && (
                        <p className="text-[11px] text-orange-600 font-medium mt-0.5">
                            • Peak at: {formatVideoTime(data.peakTimestamp)}
                        </p>
                    )}
                </div>

                {/* 2. 지표 Grid */}
                <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-slate-600 mb-3">
                    <span className="font-medium">분위기</span>
                    <span
                        className="font-bold"
                        style={{ color: getBarColor(data.atmosphere) }}
                    >
                        {ATMOSPHERE_LABELS[data.atmosphere as keyof typeof ATMOSPHERE_LABELS] || ATMOSPHERE_LABELS["neutral"]}
                    </span>

                    <span>Volume</span>
                    <span className="font-mono text-slate-800">
                        {data.activeVolume.toFixed(2)}
                    </span>

                    <span>Momentum</span>
                    <span className="font-mono text-slate-800">
                        {data.activeMomentum.toFixed(2)}
                        <span className="ml-1 text-[11px] text-slate-400 font-normal">
                            ({data.originalMomentum.toFixed(2)})
                        </span>
                    </span>

                    <span>Score</span>
                    <span className="font-mono text-slate-800">
                        {data.score?.toFixed(1) || "-"}
                    </span>
                </div>

                {/* 3. Keywords */}
                {data.keywords && data.keywords.length > 0 && (
                    <div className="pt-2 border-t border-slate-100">
                        <p className="text-[12px] text-muted-foreground mb-1.5 font-medium">Keywords</p>
                        <div className="flex flex-wrap gap-1  max-w-full">
                            {data.keywords.slice(0, 5).map((k: string, i: number) => (
                                <span
                                    key={i}
                                    className="bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded text-[12px]"
                                >
                                    #{k}
                                </span>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        );
    }
    return null;
};
