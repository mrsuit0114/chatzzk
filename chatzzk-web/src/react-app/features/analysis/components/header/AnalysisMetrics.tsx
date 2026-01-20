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
        .map(([key, score]) => {
            // 한글 키 -> 영문 Enum 변환 (매핑 없으면 그대로 사용하거나 fallback)
            const type = (KOREAN_TO_ATMOSPHERE[key] || key) as Atmosphere;
            const label = ATMOSPHERE_LABELS[type] || key;
            return { type, score, label };
        })
        .sort((a, b) => b.score - a.score);

    const top3 = sortedAtmospheres.slice(0, 3);

    return (
        <div className="flex items-center gap-3 bg-secondary/20 px-3 py-1.5 rounded-lg border border-border/60 h-auto min-h-[3rem]">
            {/* 1. 분위기 비율 (Tooltip) */}
            <TooltipProvider delayDuration={0}>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <div className="flex flex-col justify-center gap-0.5 cursor-help select-none">
                            {top3.map((item) => (
                                <div key={item.type} className="flex items-center justify-between w-[5rem] text-[10px] leading-tight">
                                    <span className="text-muted-foreground truncate max-w-[3rem]">{item.label}</span>
                                    <span className="font-semibold tabular-nums text-foreground">
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
                                    <span className="font-bold tabular-nums">{item.score.toFixed(1)}%</span>
                                </div>
                            ))}
                        </div>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>

            <Separator orientation="vertical" className="h-8 bg-border/60" />

            {/* 2. Avg Score */}
            <div className="flex flex-col items-end justify-center min-w-[3.5rem]">
                <span className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider mb-0.5">평점 평균</span>
                <div className="flex items-center gap-1.5 text-xl font-bold text-foreground leading-none">
                    <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                    <span className="tabular-nums tracking-tight">{avgScore.toFixed(1)}</span>
                </div>
            </div>
        </div>
    );
}
