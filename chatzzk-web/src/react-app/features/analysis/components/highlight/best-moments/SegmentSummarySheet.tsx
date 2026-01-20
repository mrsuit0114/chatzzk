import {
    Clock,
    Star,
    Flame,
    Zap,
} from "lucide-react";

import {
    Sheet,
    SheetContent,
    SheetDescription,
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
import { ATMOSPHERE_LABELS } from "@/constants";
import { MetricCard } from "../../common/MetricCard";


interface SegmentSummarySheetProps {
    data: SegmentSummaryData | null;
    isOpen: boolean;
    onClose: () => void;
}

export function SegmentSummarySheet({ data, isOpen, onClose }: SegmentSummarySheetProps) {
    if (!data) return null;

    return (
        <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <SheetContent className="w-full sm:max-w-md flex flex-col p-0 gap-0 border-l shadow-2xl">

                {/* 1. Header Area */}
                <SheetHeader className="p-6 pb-4 border-b bg-muted/10 space-y-1">
                    <SheetTitle className="text-lg font-bold leading-tight flex items-center gap-2">
                        <span className="w-1 h-5 bg-primary rounded-full" />
                        하이라이트 상세 정보
                    </SheetTitle>
                    {/* 접근성 준수용 Description (화면엔 안보임) */}
                    <SheetDescription className="sr-only">
                        선택한 하이라이트 구간의 상세 요약, 키워드, 지표 정보를 보여줍니다.
                    </SheetDescription>

                    <div className="flex items-center justify-between pt-2">
                        <div className="flex items-center gap-2">
                            <Badge variant="secondary" className="font-mono font-medium px-2 py-0.5 text-xs">
                                <Clock className="h-3 w-3 mr-1" />
                                {formatTime(data.startTime)} ~ {formatTime(data.endTime)}
                            </Badge>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="flex items-center gap-1 text-yellow-600 font-bold bg-yellow-50 px-2 py-0.5 rounded-md border border-yellow-100 text-xs shadow-sm">
                                <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />
                                {data.score.toFixed(1)}
                            </div>
                            <Badge variant="outline" className={cn("px-2 py-0.5 text-xs font-bold border-transparent", getBadgeClasses(data.atmosphere))}>
                                {ATMOSPHERE_LABELS[data.atmosphere]}
                            </Badge>
                        </div>
                    </div>
                </SheetHeader>

                {/* 2. Scrollable Body Area */}
                <ScrollArea className="flex-1">
                    <div className="p-6 space-y-6">

                        {/* Summary */}
                        <div className="space-y-3">
                            <h4 className="text-sm font-semibold text-foreground/90">상세 요약</h4>
                            <p className="text-sm leading-relaxed text-foreground/80 p-4 rounded-lg bg-muted/30 border">
                                {data.summary}
                            </p>
                        </div>

                        {/* Keywords */}
                        <div className="space-y-3">
                            <h4 className="text-sm font-semibold text-foreground/80">키워드</h4>
                            <div className="flex flex-wrap gap-2">
                                {data.keywords.map((keyword) => (
                                    <Badge key={keyword} variant="secondary" className="px-2.5 py-1 text-xs font-medium text-muted-foreground">
                                        #{keyword}
                                    </Badge>
                                ))}
                            </div>
                        </div>

                        <Separator />

                        {/* 3. Detailed Metrics Grid */}
                        <div className="grid gap-4">
                            {/* Vol Peak */}
                            <MetricCard
                                title="화력 Peak 시점"
                                icon={<Flame className="h-4 w-4 text-red-500 fill-red-500" />}
                                timestamp={data.volPeak.timestamp}
                                volume={data.volPeak.volume}
                                momentum={data.volPeak.momentum}
                                isMainMetric="volume"
                            />
                            {/* Mmt Peak */}
                            <MetricCard
                                title="급상승 Peak 시점"
                                icon={<Zap className="h-4 w-4 text-blue-500 fill-blue-500" />}
                                timestamp={data.mmtPeak.timestamp}
                                volume={data.mmtPeak.volume}
                                momentum={data.mmtPeak.momentum}
                                isMainMetric="momentum"
                            />
                        </div>
                    </div>
                </ScrollArea>
            </SheetContent>
        </Sheet>
    );
}
