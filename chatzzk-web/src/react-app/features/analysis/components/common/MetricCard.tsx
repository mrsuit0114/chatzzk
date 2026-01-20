import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { formatTime } from "@/utils/time-formatter";


export function MetricCard({ title, icon, timestamp, volume, momentum, isMainMetric }: any) {
    return (
        <div className="p-4 rounded-lg border bg-card/50 shadow-sm space-y-3">
            <div className="flex items-center justify-between border-b pb-2">
                <div className="flex items-center gap-2 font-semibold text-sm">
                    {icon}
                    <span>{title}</span>
                </div>
                <Badge variant="outline" className="font-mono text-[12px] text-muted-foreground">
                    {formatTime(timestamp)}
                </Badge>
            </div>
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <span className="text-[12px] uppercase text-muted-foreground font-bold block mb-0.5">화력</span>
                    <span className={cn("text-lg font-mono tracking-tight", isMainMetric === "volume" ? "font-bold text-red-600" : "text-foreground")}>
                        {volume.toLocaleString()}
                    </span>
                </div>
                <div>
                    <span className="text-[12px] uppercase text-muted-foreground font-bold block mb-0.5">변동 수치</span>
                    <span className={cn("text-lg font-mono tracking-tight", isMainMetric === "momentum" ? "font-bold text-blue-600" : "text-foreground")}>
                        {momentum.toFixed(2)}
                    </span>
                </div>
            </div>
        </div>
    );
}
