import { Clock, Star, Flame, Zap } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { getBadgeClasses } from "@/features/analysis/utils";
import { SegmentSummaryData } from "../../types";
import { cn } from "@/lib/utils";
import { ATMOSPHERE_LABELS } from "@/constants";
import { formatTime } from "@/utils/time-formatter";
import { MetricCard } from "./MetricCard";

interface SegmentDetailCardProps {
    data: SegmentSummaryData;
}

export function SegmentDetailCard({ data }: SegmentDetailCardProps) {

    return (
        <Card className="border-border shadow-sm">
            {/* Header */}
            <CardHeader className="p-4 pb-2 flex flex-row items-center justify-between space-y-0">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Clock className="h-4 w-4" />
                    <span className="font-mono font-medium">
                        {formatTime(data.startTime)} ~ {formatTime(data.endTime)}
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1 text-yellow-600 font-bold bg-yellow-50 px-2 py-1 rounded-full border border-yellow-100">
                        <Star className="h-3 w-3 fill-yellow-500 text-yellow-500" />
                        <span className="text-xs tabular-nums">{data.score?.toFixed(1)}</span>
                    </div>
                    <Badge variant="outline" className={cn("px-2 py-1 text-xs font-bold", getBadgeClasses(data.atmosphere))}>
                        {ATMOSPHERE_LABELS[data.atmosphere]}
                    </Badge>
                </div>
            </CardHeader>

            <CardContent className="p-2 pt-2 space-y-2">
                {/* Summary & Keywords */}
                <div className="space-y-2 p-2">
                    <p className="text-sm leading-relaxed text-foreground/90">
                        {data.summary}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                        {data.keywords.map((keyword) => (
                            <Badge key={keyword} variant="secondary" className="px-1.5 py-0.5 text-[11px] text-muted-foreground font-normal">
                                #{keyword}
                            </Badge>
                        ))}
                    </div>
                </div>

                <Separator />

                {/* ✅ Detailed Metrics: Vol Peak & Mmt Peak (Full Data) */}
                <div className="grid grid-cols-2 gap-4">

                    <MetricCard
                        title="화력 Peak"
                        icon={<Flame className="h-4 w-4 text-red-500 fill-red-500" />}
                        timestamp={data.volPeak.timestamp}
                        volume={data.volPeak.volume}
                        momentum={data.volPeak.momentum}
                        isMainMetric="volume"
                    />

                    {/* 2. Momentum Peak Box */}
                    <MetricCard
                        title="급상승 Peak"
                        icon={<Zap className="h-4 w-4 text-blue-500 fill-blue-500" />}
                        timestamp={data.mmtPeak.timestamp}
                        volume={data.mmtPeak.volume}
                        momentum={data.mmtPeak.momentum}
                        isMainMetric="momentum"
                    />

                </div>
            </CardContent>
        </Card>
    );
}
