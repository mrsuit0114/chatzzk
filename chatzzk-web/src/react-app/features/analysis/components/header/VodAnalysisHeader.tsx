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
        <header className="relative lg:sticky z-40 w-full border-b bg-background transition-all">
            <div className="container mx-auto">
                <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 py-4 lg:py-0 lg:h-16">
                    {/* [Left] VOD Info */}
                    <div className="w-full lg:w-auto lg:flex-1 min-w-0">
                        <VodInfo data={data} />
                    </div>

                    {/* [Right] Metrics & Switcher */}
                    <div className="flex items-center justify-between lg:justify-end gap-3 lg:gap-6 w-full lg:w-auto flex-shrink-0">

                        {/* [변경 3] Metrics: 모바일에서도 공간이 확보되었으므로 보여줍니다. (선택사항)
                            만약 모바일에서 숨기고 싶다면 기존처럼 hidden lg:block 유지 */}
                        <div className="block">
                            <AnalysisMetrics
                                atmosphereRatio={data.atmosphereRatio}
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
            </div>
        </header>
    );
}
