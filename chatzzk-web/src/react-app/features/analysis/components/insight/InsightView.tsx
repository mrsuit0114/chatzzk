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
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 h-auto lg:h-[60vh] lg:min-h-[600px]">

                {/* Left: Structure List (Chapters) */}
                {/* ✅ 모바일: h-[450px] 고정, 데스크탑: h-full */}
                <div className="col-span-1 lg:col-span-6
                                h-[350px] lg:h-full
                                border rounded-lg overflow-hidden bg-card shadow-sm">
                    <StructureListSection
                        data={viewData.segments}
                        chapters={viewData.chapters}
                        focusedTimestamp={focusedTimestamp}
                        onSeek={handleTrendClick}
                    />
                </div>

                {/* Right: Detail Section (Clips/Logs) */}
                {/* ✅ 모바일: h-[500px] 고정, 데스크탑: h-full */}
                <div className="col-span-1 lg:col-span-6
                                h-[350px] lg:h-full
                                border rounded-lg overflow-hidden bg-card shadow-sm">
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
