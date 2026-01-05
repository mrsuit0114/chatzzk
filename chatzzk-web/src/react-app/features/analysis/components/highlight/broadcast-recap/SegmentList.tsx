import { SegmentDetailCard } from "./SegmentDetailCard";
import type { SegmentSummaryData } from "../types";

interface SegmentListProps {
    segments: SegmentSummaryData[];
}

export function SegmentList({ segments }: SegmentListProps) {
    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b shrink-0 bg-background z-10">
                <h3 className="text-lg font-bold">Segment Detail</h3>
                <span className="text-xs text-muted-foreground font-medium">
                    Total {segments.length} items
                </span>
            </div>

            {/* Scrollable Content Area */}
            <div className="flex-1 overflow-y-auto py-4 pr-2 space-y-4 min-h-0 custom-scrollbar pb-20">
                {segments.length > 0 ? (
                    segments.map((segment) => (
                        <SegmentDetailCard key={segment.id} data={segment} />
                    ))
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-muted-foreground text-sm border-2 border-dashed rounded-lg">
                        <p>해당 챕터에 포함된 세그먼트가 없습니다.</p>
                    </div>
                )}
            </div>
        </div>
    );
}
