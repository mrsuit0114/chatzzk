import { BestMomentsSection } from "./best-moments/BestMomentsSection";
import { BroadcastRecapSection } from "./broadcast-recap/BroadcastRecapSection";
import { SegmentSummaryData, ChapterSummaryData } from "../types";

interface HighlightViewProps {
    segments: SegmentSummaryData[];
    chapters: ChapterSummaryData[];
}

export function HighlightView({ segments, chapters }: HighlightViewProps) {
    return (
        <div className="flex flex-col">
            <BestMomentsSection data={segments} />
            <BroadcastRecapSection chapters={chapters} allSegments={segments} />
        </div>
    );
}
