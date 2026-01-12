import {
    Clock,
    Star,
    Flame,
    Zap,
} from "lucide-react";

import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getBadgeClasses } from "@/features/analysis/utils";
import { SegmentSummaryData } from "@/features/analysis/types";

import { cn } from "@/lib/utils";
import { formatTime } from "@/utils/time-formatter";


interface SegmentSummarySheetProps {
    data: SegmentSummaryData | null;
    isOpen: boolean;
    onClose: () => void;
}

export function SegmentSummarySheet({ data, isOpen, onClose }: SegmentSummarySheetProps) {
    if (!data) return null;

    return (
        <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <SheetContent className="w-full sm:max-w-md flex flex-col p-0 gap-0" aria-describedby={undefined}>

                {/* 1. Header Area */}
                <SheetHeader className="p-6 pb-4 border-b bg-muted/10">
                    <SheetTitle className="text-lg font-bold leading-tight mb-2">
                        Highlight Detail
                    </SheetTitle>

                    <div className="flex items-center justify-between">
                        {/* Left: Time Range */}
                        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                            <Clock className="h-4 w-4" />
                            <span className="font-mono font-medium">
                                {formatTime(data.startTime)} ~ {formatTime(data.endTime)}
                            </span>
                        </div>

                        {/* Right: Score & Atmosphere (UI 일관성: 우측 배치) */}
                        <div className="flex items-center gap-2">
                            {/* Score */}
                            <div className="flex items-center gap-1 text-yellow-600 font-bold bg-yellow-50 px-2 py-1 rounded-full border border-yellow-100">
                                <Star className="h-3.5 w-3.5 fill-yellow-500 text-yellow-500" />
                                <span className="text-xs tabular-nums">{data.score.toFixed(1)}</span>
                            </div>
                            {/* Atmosphere */}
                            <Badge variant="outline" className={cn("px-2.5 py-1 text-xs font-bold", getBadgeClasses(data.atmosphere))}>
                                {data.atmosphere}
                            </Badge>
                        </div>
                    </div>
                </SheetHeader>

                {/* 2. Scrollable Body Area */}
                <ScrollArea className="flex-1 p-6">
                    <div className="space-y-6">

                        {/* Summary */}
                        <div className="space-y-3">
                            <h4 className="text-sm font-semibold text-foreground/80 flex items-center gap-2">
                                <span className="w-1 h-4 bg-primary rounded-full" />
                                상세 요약
                            </h4>
                            <p className="text-sm leading-7 text-foreground/90 bg-muted/30 p-4 rounded-lg border">
                                {data.summary}
                            </p>
                        </div>

                        {/* Keywords */}
                        <div className="space-y-3">
                            <h4 className="text-sm font-semibold text-foreground/80">관련 키워드</h4>
                            <div className="flex flex-wrap gap-2">
                                {data.keywords.map((keyword) => (
                                    <Badge key={keyword} variant="secondary" className="px-2.5 py-1 text-xs font-medium text-muted-foreground">
                                        #{keyword}
                                    </Badge>
                                ))}
                            </div>
                        </div>

                        <Separator />

                        {/* 3. Detailed Metrics Grid (Timestamp, Vol, Mmt 전부 명시) */}
                        <div className="grid grid-cols-1 gap-4">

                            {/* A. Volume Peak Info */}
                            <div className="space-y-3 p-4 rounded-lg border bg-card shadow-sm">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2 text-foreground">
                                        <Flame className="h-4 w-4 text-red-500 fill-red-500" />
                                        <span className="text-sm font-bold">Volume Peak</span>
                                    </div>
                                    {/* Timestamp */}
                                    <span className="text-xs font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">
                                        @ {formatTime(data.volPeak.timestamp)}
                                    </span>
                                </div>
                                <div className="grid grid-cols-2 gap-4 pt-1">
                                    <div>
                                        <span className="text-[10px] uppercase text-muted-foreground font-bold">Volume</span>
                                        {/* 기준 지표 강조 */}
                                        <p className="text-xl font-bold tabular-nums text-red-600">
                                            {data.volPeak.volume.toLocaleString()}
                                        </p>
                                    </div>
                                    <div>
                                        <span className="text-[10px] uppercase text-muted-foreground font-bold">Momentum</span>
                                        <p className="text-xl font-medium tabular-nums text-foreground/80">
                                            {data.volPeak.momentum.toFixed(1)}
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* B. Momentum Peak Info */}
                            <div className="space-y-3 p-4 rounded-lg border bg-card shadow-sm">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2 text-foreground">
                                        <Zap className="h-4 w-4 text-blue-500 fill-blue-500" />
                                        <span className="text-sm font-bold">Momentum Peak</span>
                                    </div>
                                    {/* Timestamp */}
                                    <span className="text-xs font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">
                                        @ {formatTime(data.mmtPeak.timestamp)}
                                    </span>
                                </div>
                                <div className="grid grid-cols-2 gap-4 pt-1">
                                    <div>
                                        <span className="text-[10px] uppercase text-muted-foreground font-bold">Volume</span>
                                        <p className="text-xl font-medium tabular-nums text-foreground/80">
                                            {data.mmtPeak.volume.toLocaleString()}
                                        </p>
                                    </div>
                                    <div>
                                        <span className="text-[10px] uppercase text-muted-foreground font-bold">Momentum</span>
                                        {/* 기준 지표 강조 */}
                                        <p className="text-xl font-bold tabular-nums text-blue-600">
                                            {data.mmtPeak.momentum.toFixed(1)}
                                        </p>
                                    </div>
                                </div>
                            </div>

                        </div>
                    </div>
                </ScrollArea>

                {/* Footer Removed */}

            </SheetContent>
        </Sheet>
    );
}
