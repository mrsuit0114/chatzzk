// src/features/vod/components/header/AnalysisMetrics.tsx

import { Star } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { Sentiment } from "../../types";

interface AnalysisMetricsProps {
    sentiments: Sentiment[];
    avgScore: number;
}

export function AnalysisMetrics({ sentiments, avgScore }: AnalysisMetricsProps) {
    // 점수 높은 순 정렬 후 Top 3 추출
    const sortedSentiments = [...sentiments].sort((a, b) => b.score - a.score);
    const top3 = sortedSentiments.slice(0, 3);

    return (
        <div className="flex items-center gap-3 bg-secondary/10 px-3 py-1 rounded-lg border border-border/50 h-15">
            {/* 1. 분위기 비율 (수직 배치) */}
            <TooltipProvider delayDuration={100}>
                <Tooltip>
                    <TooltipTrigger asChild>
                        <div className="flex flex-col justify-center gap-[1px] cursor-help">
                            {top3.map((item) => (
                                <div key={item.label} className="flex items-center justify-between w-[4.5rem]">
                                    <div className="flex items-center gap-1.5 overflow-hidden">
                                        <span className={cn("flex-shrink-0 h-1.5 rounded-full", item.color.replace("text-", "bg-"))} />
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
                            {sortedSentiments.map((item) => (
                                <div key={item.label} className="flex items-center justify-between gap-8 text-sm">
                                    <div className="flex items-center gap-2">
                                        <span className={cn("w-2 h-2 rounded-full", item.color.replace("text-", "bg-"))} />
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
