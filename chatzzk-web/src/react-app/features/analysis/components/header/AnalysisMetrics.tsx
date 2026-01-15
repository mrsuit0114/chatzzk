// src/features/vod/components/header/AnalysisMetrics.tsx

import { Star } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { Atmosphere, ATMOSPHERE_LABELS, KOREAN_TO_ATMOSPHERE } from "@/constants";

interface AnalysisMetricsProps {
    atmosphereRatio: Record<Atmosphere, number>;
    avgScore: number;
}

export function AnalysisMetrics({ atmosphereRatio, avgScore }: AnalysisMetricsProps) {
    // 점수 높은 순 정렬 후 Top 3 추출
    const sortedAtmospheres = Object.entries(atmosphereRatio)
        .map(([type, score]) => {
            const atmosphere = KOREAN_TO_ATMOSPHERE[type] as Atmosphere;

            return {
                type: atmosphere,
                score,
                label: ATMOSPHERE_LABELS[atmosphere],
            };
        })
        .sort((a, b) => b.score - a.score);
    const top3 = sortedAtmospheres.slice(0, 3);

    return (
        <div className="flex items-center gap-3 bg-secondary/10 px-3 py-1 rounded-lg border border-border/50 h-15">
            {/* 1. 분위기 비율 (Tooltip) */}
            <TooltipProvider delayDuration={100}>
                <Tooltip>
                    <TooltipTrigger asChild>
                        {/* asChild 사용 시, 내부에 단 하나의 자식 요소만 있어야 하며 ref 전달이 가능해야 함 */}
                        <div className="flex flex-col justify-center gap-[1px] cursor-help">
                            {top3.map((item) => (
                                // ✅ 수정 1: key를 item.label -> item.type으로 변경 (유니크 보장)
                                <div key={item.type} className="flex items-center justify-between w-[4.5rem]">
                                    <div className="flex items-center gap-1.5 overflow-hidden">
                                        <span className="text-[10px] text-muted-foreground truncate">{item.label}</span>
                                    </div>
                                    <span className="text-[10px] font-medium tabular-nums text-foreground">
                                        {item.score.toFixed(1)}%
                                    </span>
                                </div>
                            ))}
                        </div>
                    </TooltipTrigger>

                    <TooltipContent side="bottom" className="p-3 z-50">
                        <div className="space-y-2">
                            <p className="font-semibold text-xs mb-2 text-muted-foreground">전체 분위기 분석</p>
                            {sortedAtmospheres.map((item) => (
                                <div key={item.type} className="flex items-center justify-between gap-8 text-sm">
                                    <div className="flex items-center gap-2">
                                        <span>{item.label}</span>
                                    </div>
                                    <span className="font-bold tabular-nums">{item.score.toFixed(2)}%</span>
                                </div>
                            ))}
                        </div>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>

            <Separator orientation="vertical" className="h-6" />

            {/* 2. Avg Score */}
            <div className="flex flex-col items-end justify-center leading-none min-w-[3rem]">
                <span className="text-[9px] text-muted-foreground font-medium uppercase tracking-wider mb-0.5">Avg Score</span>
                <div className="flex items-center gap-1 text-lg font-bold text-foreground">
                    <Star className="h-3.5 w-3.5 text-yellow-500 fill-yellow-500" />
                    <span className="tabular-nums">{avgScore.toFixed(1)}</span>
                </div>
            </div>
        </div>
    );
}
