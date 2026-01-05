import { VodAnalysisHeaderProps } from "../../types";
import { AnalysisMetrics } from "./AnalysisMetrics";
import { ViewSwitcher } from "./ViewSwitcher";
import { VodInfo } from "./VodInfo";

export function VodAnalysisHeader({
    data,
    currentView,
    onViewChange,
    isInsightLocked = false,
}: VodAnalysisHeaderProps) {
    return (
        <header className="sticky top-14 z-40 w-full border-b bg-background">
            <div className="container mx-auto h-16 flex items-center justify-between gap-4">

                {/* [Left] VOD Info */}
                <VodInfo data={data} />

                {/* [Right] Metrics & Switcher */}
                <div className="flex items-center gap-6 flex-shrink-0">
                    {/* 1. Metrics Component */}
                    <div className="hidden lg:block">
                        <AnalysisMetrics
                            sentiments={data.sentiments}
                            avgScore={data.avgScore}
                        />
                    </div>

                    {/* 2. View Switcher */}
                    <ViewSwitcher
                        currentView={currentView}
                        onChange={onViewChange}
                        isInsightLocked={isInsightLocked}
                    />
                </div>
            </div>
        </header>
    );
}
