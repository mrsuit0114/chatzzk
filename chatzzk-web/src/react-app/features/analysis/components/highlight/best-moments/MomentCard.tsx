import { Flame, Zap, Star, Clock, Timer } from "lucide-react";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { getBadgeClasses } from "@/features/analysis/utils";
import { SORT_OPTIONS, SortOption } from "@/features/analysis/constants";
import { SegmentSummaryData } from "@/features/analysis/types";
import { ATMOSPHERE_LABELS } from "@/constants";
import { formatTime, formatInterval } from "@/utils/time-formatter";



interface MomentCardProps {
    data: SegmentSummaryData;
    interval: number;
    sortBy: SortOption;
    onClick: () => void;
}

export function MomentCard({ data, interval, sortBy, onClick }: MomentCardProps) {

    // 2. Footer에 보여줄 Peak 데이터 결정
    // - Momentum 정렬일 때만 mmtPeak(급상승 기준)를 보여주고,
    // - Volume이나 Score 정렬일 때는 가장 일반적인 volPeak(화력 기준)를 보여줍니다.
    const activePeak = sortBy === SORT_OPTIONS.MOMENTUM ? data.mmtPeak : data.volPeak;

    return (
        <Card
            onClick={onClick}
            className={cn(
                "group relative cursor-pointer overflow-hidden transition-all flex flex-col border-border",
                "hover:shadow-md hover:border-primary/50",
                // ✅ [수정] 고정 사이즈 부여
                // shrink-0을 주어 Flex 컨테이너 안에서 찌그러지지 않게 합니다.
                "w-[320px] h-[270px] shrink-0"
            )}
        >
            {/* Header (높이 고정됨) */}
            <CardHeader className="p-3 pb-2 flex flex-row items-center justify-between space-y-0">
                <div className="flex items-center gap-1.5">
                    <div className="flex items-center gap-1 text-xs font-mono font-medium text-foreground bg-muted/80 px-1.5 py-0.5 rounded">
                        <Clock className="h-3 w-3" />
                        <span>{formatTime(data.startTime)}</span>
                    </div>
                    <div className="flex items-center text-[11px] text-foreground/70">
                        <Timer className="h-3 w-3 mr-0.5" />
                        <span>{formatInterval(interval)}</span>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <div className={cn(
                        "flex items-center gap-1 text-xs tabular-nums transition-colors",
                        sortBy === SORT_OPTIONS.SCORE ? "text-yellow-600 font-bold" : "text-muted-foreground"
                    )}>
                        <Star className={cn("h-3 w-3", sortBy === SORT_OPTIONS.SCORE ? "fill-yellow-500 text-yellow-500" : "")} />
                        {data.score.toFixed(1)}
                    </div>
                    <Badge variant="outline" className={cn("text-[10px] font-bold px-2 py-0.5", getBadgeClasses(data.atmosphere))}>
                        {ATMOSPHERE_LABELS[data.atmosphere]}
                    </Badge>
                </div>
            </CardHeader>

            {/* Content (Flex-1로 남는 공간 차지) */}
            <CardContent className="p-3 pt-1 flex flex-col h-full">

                {/* 1. Summary Area (Flex-1) */}
                {/* 요약문이 짧아도 이 영역은 늘어나있으므로, 키워드는 항상 바닥에 붙음 */}
                <div className="flex-1 min-h-0">
                    <p className="text-sm font-medium leading-relaxed line-clamp-6 text-foreground/90 group-hover:text-primary transition-colors">
                        {data.summary}
                    </p>
                </div>

                {/* 2. Keywords (Fixed Position relative to bottom content) */}
                {/* mt-2로 상단(Summary)과의 최소 간격 유지 */}
                <div className="flex flex-wrap gap-1.5 mt-2 mb-3 h-[18px] overflow-hidden">
                    {data.keywords.map((keyword) => (
                        <span key={keyword} className="text-[12px] px-1.5 py-0.5 bg-secondary/50 rounded text-muted-foreground whitespace-nowrap">
                            #{keyword}
                        </span>
                    ))}
                </div>

                {/* 3. Footer (Fixed Height) */}
                <div className="mt-auto">
                    <Separator className="mb-2" />
                    <div className="bg-secondary/10 -mx-1 px-2 py-1 rounded flex items-center justify-between">
                        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                            <span className="text-[10px] uppercase font-bold tracking-wider opacity-70">Peak</span>
                            <span className="font-mono font-medium text-foreground">
                                {formatTime(activePeak.timestamp)}
                            </span>
                        </div>
                        <div className="flex items-center gap-3">
                            <div className={cn("flex items-center gap-1 transition-opacity", sortBy === SORT_OPTIONS.VOLUME ? "opacity-100" : "opacity-60")}>
                                <Flame className={cn("h-3.5 w-3.5", sortBy === SORT_OPTIONS.VOLUME ? "text-red-500 fill-red-500" : "text-muted-foreground")} />
                                <span className={cn("text-xs tabular-nums", sortBy === SORT_OPTIONS.VOLUME && "font-bold text-red-600")}>
                                    {activePeak.volume.toFixed(2)}
                                </span>
                            </div>
                            <div className={cn("flex items-center gap-1 transition-opacity", sortBy === SORT_OPTIONS.MOMENTUM ? "opacity-100" : "opacity-60")}>
                                <Zap className={cn("h-3.5 w-3.5", sortBy === SORT_OPTIONS.MOMENTUM ? "text-blue-500 fill-blue-500" : "text-muted-foreground")} />
                                <span className={cn("text-xs tabular-nums", sortBy === SORT_OPTIONS.MOMENTUM && "font-bold text-blue-600")}>
                                    {activePeak.momentum.toFixed(2)}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

            </CardContent>
        </Card>
    );
}
