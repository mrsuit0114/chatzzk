import { LineChart, Lock, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { VIEW_TYPE, ViewType } from "../../constants";


interface ViewSwitcherProps {
    currentView: ViewType;
    onChange: (view: ViewType) => void;
    isInsightLocked?: boolean;
}

export function ViewSwitcher({ currentView, onChange, isInsightLocked }: ViewSwitcherProps) {

    const handleSwitch = () => {
        if (isInsightLocked) return;
        if (currentView === VIEW_TYPE.INSIGHT) {
            onChange(VIEW_TYPE.HIGHLIGHT); // 부모로 전달 (부모에서 잠금 체크 및 Toast 처리)
        } else {
            onChange(VIEW_TYPE.INSIGHT);
        }
    };

    return (
        <div className="flex p-1 bg-muted rounded-lg border h-9 select-none relative mr-2">
            {/* 1. Highlight Tab */}
            <button
                type="button"
                onClick={handleSwitch}
                className={cn(
                    "relative z-10 flex items-center justify-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold transition-all duration-200 min-w-[90px]",
                    currentView === VIEW_TYPE.HIGHLIGHT
                        ? "bg-background text-foreground shadow-sm ring-1 ring-border/50"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted-foreground/10"
                )}
            >
                <Sparkles className="h-3.5 w-3.5" />
                {VIEW_TYPE.HIGHLIGHT.label}
            </button>

            {/* 2. Insight Tab */}
            <button
                type="button"
                onClick={handleSwitch}
                className={cn(
                    "relative z-10 flex items-center justify-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold transition-all duration-200 min-w-[90px]",
                    currentView === VIEW_TYPE.INSIGHT
                        ? "bg-background text-primary shadow-sm ring-1 ring-border/50"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted-foreground/10",
                    isInsightLocked && "opacity-80"
                )}
            >
                {isInsightLocked ? <Lock className="h-3.5 w-3.5" /> : <LineChart className="h-3.5 w-3.5" />}
                {VIEW_TYPE.INSIGHT.label}
            </button>
        </div>
    );
}
