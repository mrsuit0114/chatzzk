import { useState } from "react";
import { SegmentTrendSection } from "./trend/SegmentTrendSection";
import { StructureListSection } from "./structure/StructureListSection";
import { DetailSection } from "./detail/DetailSection";
import { AnalysisIntervals, InsightViewData } from "../../types";

interface InsightViewProps {
    viewData: InsightViewData;
    intervals: AnalysisIntervals;
}

export function InsightView({ viewData, intervals }: InsightViewProps) {
    const [focusedTimestamp, setFocusedTimestamp] = useState<number | null>(null);

    const handleTrendClick = (timestamp: number) => {
        setFocusedTimestamp(timestamp);
    };

    return (
        <div className="flex flex-col gap-2 p-2">

            {/* Top: Trend Section */}
            <SegmentTrendSection
                data={viewData.segments}
                chapters={viewData.chapters}
                intervals={intervals}
                focusedTimestamp={focusedTimestamp}
                onChartClick={handleTrendClick}
            />

            {/* Bottom Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-2 h-[60vh] max-h-[800px]">
                <div className="col-span-6 border h-full overflow-hidden rounded">
                    <StructureListSection
                        data={viewData.segments}
                        chapters={viewData.chapters}
                        focusedTimestamp={focusedTimestamp}
                        onSeek={handleTrendClick}
                    />
                </div>
                <div className="col-span-6 border h-full overflow-hidden rounded">
                    <DetailSection
                        intervals={intervals}
                        clips={viewData.clips}
                        focusedTimestamp={focusedTimestamp}
                        onSeek={handleTrendClick}
                    />
                </div>
            </div>
        </div>
    );
}
