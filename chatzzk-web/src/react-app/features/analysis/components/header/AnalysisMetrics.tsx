import { Atmosphere, ATMOSPHERE_LABELS, KOREAN_TO_ATMOSPHERE } from "@/constants";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

interface AnalysisMetricsProps {
    atmosphereRatio: Record<Atmosphere, number>;
}

export function AnalysisMetrics({ atmosphereRatio }: AnalysisMetricsProps) {
    const sortedAtmospheres = Object.entries(atmosphereRatio)
        .map(([key, score]) => {
            const type = (KOREAN_TO_ATMOSPHERE[key] || key) as Atmosphere;
            const label = ATMOSPHERE_LABELS[type] || key;
            return { type, score, label };
        })
        .sort((a, b) => b.score - a.score);

    const top3 = sortedAtmospheres.slice(0, 3);

    return (
        <div className="flex items-center bg-secondary/20 px-3 py-1.5 rounded-lg border border-border/60 h-auto min-h-[3rem]">
            <Popover>
                <PopoverTrigger asChild>
                    <button
                        type="button"
                        className="flex flex-col justify-center gap-0.5 cursor-pointer select-none text-left rounded-sm hover:bg-muted/50 transition-colors py-0.5 px-1 -mx-1"
                    >
                        {top3.map((item) => (
                            <div key={item.type} className="flex items-center justify-between w-[5rem] text-[10px] leading-tight">
                                <span className="text-muted-foreground truncate max-w-[3rem]">{item.label}</span>
                                <span className="font-semibold tabular-nums text-foreground">
                                    {item.score?.toFixed(1)}%
                                </span>
                            </div>
                        ))}
                    </button>
                </PopoverTrigger>

                <PopoverContent
                    side="bottom"
                    align="start"
                    sideOffset={8}
                    className="p-3 z-50 w-auto min-w-[120px] bg-muted/90 text-foreground border border-border shadow-xl backdrop-blur-sm"
                >
                    <div className="space-y-2">
                        <p className="font-semibold text-xs mb-2 text-muted-foreground">전체 분위기 분석</p>
                        {sortedAtmospheres.map((item) => (
                            <div key={item.type} className="flex items-center justify-between gap-6 text-sm">
                                <span>{item.label}</span>
                                <span className="font-bold tabular-nums">{item.score?.toFixed(1)}%</span>
                            </div>
                        ))}
                    </div>
                </PopoverContent>
            </Popover>
        </div>
    );
}
