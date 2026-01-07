import { useState, useMemo } from "react";
import { ChapterList } from "./ChapterList";
import { SegmentList } from "./SegmentList";
import { ChapterSummaryData, SegmentSummaryData } from "@/features/analysis/types";

interface BroadcastRecapSectionProps {
    chapters: ChapterSummaryData[];
    allSegments: SegmentSummaryData[];
}

export function BroadcastRecapSection({ chapters, allSegments }: BroadcastRecapSectionProps) {
    const [selectedChapterId, setSelectedChapterId] = useState<string>("");

    // 선택된 챕터에 해당하는 세그먼트 필터링
    const currentSegments = useMemo(() => {
        if (!selectedChapterId) return [];
        return allSegments.filter((seg) => seg.chapterId === selectedChapterId);
    }, [selectedChapterId, allSegments]);

    return (
        <section className="space-y-4 pt-6 border-t">
            <div className="space-y-1 px-1">
                <h2 className="text-xl font-bold tracking-tight">Broadcast Recap</h2>
                <p className="text-sm text-muted-foreground">
                    방송의 전체 흐름(Chapter)과 상세 내용(Segment)을 시간 순서대로 확인하세요.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 h-[80vh] min-h-[600px]">

                {/* [Left] Chapter List Container */}
                <div className="md:col-span-6 lg:col-span-6 h-full border-r pr-4 overflow-hidden">
                    <ChapterList
                        chapters={chapters}
                        selectedChapterId={selectedChapterId}
                        onSelectChapter={setSelectedChapterId}
                    />
                </div>

                {/* [Right] Segment List Container */}
                <div className="md:col-span-6 lg:col-span-6 h-full overflow-hidden">
                    <SegmentList segments={currentSegments} />
                </div>

            </div>
        </section>
    );
}
