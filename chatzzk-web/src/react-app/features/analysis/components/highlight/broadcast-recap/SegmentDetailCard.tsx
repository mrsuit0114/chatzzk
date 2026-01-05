import { Clock, Star, Flame, Zap } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { cn, formatTime } from "@/lib/utils";
import { getAtmosphereColor, type SegmentSummaryData } from "../types";

interface SegmentDetailCardProps {
    data: SegmentSummaryData;
}

export function SegmentDetailCard({ data }: SegmentDetailCardProps) {

    return (
        <Card className="border-border shadow-sm hover:border-primary/50 transition-colors">
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
                        <span className="text-xs tabular-nums">{data.score.toFixed(1)}</span>
                    </div>
                    <Badge variant="outline" className={cn("px-2 py-1 text-xs font-bold", getAtmosphereColor(data.atmosphere))}>
                        {data.atmosphere}
                    </Badge>
                </div>
            </CardHeader>

            <CardContent className="p-4 pt-2 space-y-4">
                {/* Summary & Keywords */}
                <div className="space-y-2">
                    <p className="text-sm leading-relaxed text-foreground/90">
                        {data.summary}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                        {data.keywords.map((keyword) => (
                            <Badge key={keyword} variant="secondary" className="px-1.5 py-0.5 text-[10px] text-muted-foreground font-normal">
                                #{keyword}
                            </Badge>
                        ))}
                    </div>
                </div>

                <Separator />

                {/* ✅ Detailed Metrics: Vol Peak & Mmt Peak (Full Data) */}
                <div className="grid grid-cols-2 gap-3">

                    {/* 1. Volume Peak Box */}
                    <div className="bg-secondary/10 p-3 rounded-md border flex flex-col gap-2">
                        {/* Header: Title & Timestamp */}
                        <div className="flex items-center justify-between border-b pb-1.5 border-border/50">
                            <div className="flex items-center gap-1.5 text-muted-foreground">
                                <Flame className="h-3.5 w-3.5 text-red-500 fill-red-500" />
                                <span className="text-xs font-bold text-foreground">Vol. Peak</span>
                            </div>
                            <span className="text-[12px] font-mono text-muted-foreground">{formatTime(data.volPeak.timestamp)}</span>
                        </div>

                        {/* Body: Volume (Main) & Momentum (Sub) */}
                        <div className="grid grid-cols-2 gap-2">
                            {/* Main Metric: Volume */}
                            <div className="flex flex-col">
                                <span className="text-[10px] text-muted-foreground font-semibold">Volume</span>
                                <span className="text-lg font-bold tabular-nums text-red-600 leading-tight">
                                    {data.volPeak.volume.toLocaleString()}
                                </span>
                            </div>
                            {/* Sub Metric: Momentum (참고용) */}
                            <div className="flex flex-col border-l pl-2 border-border/50">
                                <span className="text-[10px] text-muted-foreground">Momentum</span>
                                <span className="text-sm font-medium tabular-nums text-foreground/70 leading-tight mt-1">
                                    {data.volPeak.momentum.toFixed(2)}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* 2. Momentum Peak Box */}
                    <div className="bg-secondary/10 p-3 rounded-md border flex flex-col gap-2">
                        {/* Header: Title & Timestamp */}
                        <div className="flex items-center justify-between border-b pb-1.5 border-border/50">
                            <div className="flex items-center gap-1.5 text-muted-foreground">
                                <Zap className="h-3.5 w-3.5 text-blue-500 fill-blue-500" />
                                <span className="text-xs font-bold text-foreground">Mmt. Peak</span>
                            </div>
                            <span className="text-[12px] font-mono text-muted-foreground">{formatTime(data.mmtPeak.timestamp)}</span>
                        </div>

                        {/* Body: Momentum (Main) & Volume (Sub) */}
                        <div className="grid grid-cols-2 gap-2">
                            {/* Sub Metric: Volume (참고용) */}
                            <div className="flex flex-col border-r pr-2 border-border/50 text-right">
                                <span className="text-[10px] text-muted-foreground">Volume</span>
                                <span className="text-sm font-medium tabular-nums text-foreground/70 leading-tight mt-1">
                                    {data.mmtPeak.volume.toLocaleString()}
                                </span>
                            </div>
                            {/* Main Metric: Momentum */}
                            <div className="flex flex-col items-end">
                                <span className="text-[10px] text-muted-foreground font-semibold">Momentum</span>
                                <span className="text-lg font-bold tabular-nums text-blue-600 leading-tight">
                                    {data.mmtPeak.momentum.toFixed(2)}
                                </span>
                            </div>
                        </div>
                    </div>

                </div>
            </CardContent>
        </Card>
    );
}
