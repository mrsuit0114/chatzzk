import { useMemo } from "react";
import { DetailChart } from "./DetailChart";
import { AnalysisIntervals, ClipData } from "@/features/analysis/types";
import { DETAIL_CHART_HEIGHT } from "@/features/analysis/constants";
import { StreamLogViewer } from "./StreamLogViewer";

interface DetailSectionProps {
    intervals: AnalysisIntervals;
    clips: ClipData[];
    focusedTimestamp: number | null;
    onSeek: (timestamp: number) => void;
}

export function DetailSection({
    clips,
    intervals,
    focusedTimestamp,
    onSeek
}: DetailSectionProps) {

    // 0. 현재 기준 시간 (null이면 0초로 간주)
    const currentTimestamp = focusedTimestamp ?? 0;

    // 1. [계산] 현재 Chapter 범위 계산 (수학적 계산 O(1))
    const currentChapterRange = useMemo(() => {
        const start = Math.floor(currentTimestamp / intervals.chapterStep) * intervals.chapterStep;
        const end = start + intervals.chapterStep;
        const chapterIndex = start / intervals.chapterStep;
        return { start, end, chapterIndex };
    }, [currentTimestamp, intervals.chapterStep]);

    // 2. [필터링] 현재 Chapter 범위에 속하는 Clip만 추출
    const currentClips = useMemo(() => {
        if (focusedTimestamp === null) return [];

        return clips.filter(clip =>
            clip.startTime >= currentChapterRange.start &&
            clip.startTime < currentChapterRange.end
        );
    }, [currentChapterRange, focusedTimestamp, clips]);

    // 3. [계산] 현재 Segment 범위 계산 (ReferenceArea용)
    const currentSegmentRange = useMemo(() => {
        // focusedTimestamp가 null일 때는 표시하지 않음 (선택사항)
        if (focusedTimestamp === null) return null;

        const start = Math.floor(currentTimestamp / intervals.segmentStep) * intervals.segmentStep;
        const end = start + intervals.segmentStep;
        return { start, end };
    }, [currentTimestamp, intervals.segmentStep, focusedTimestamp]);


    return (
        <section className="flex flex-col h-full border bg-card shadow-sm overflow-hidden">
            <div className="border-b bg-white/50 w-full p-2" style={{ height: DETAIL_CHART_HEIGHT + 10 }}>
                {focusedTimestamp !== null ? (
                    <DetailChart
                        data={currentClips}
                        segmentRange={currentSegmentRange}
                        focusedTimestamp={focusedTimestamp}
                        onSeek={onSeek}
                        xDomain={[currentChapterRange.start, currentChapterRange.end]}
                    />
                ) : (
                    // ✅ [초기 상태 처리] focusedTimestamp가 null일 때 안내 문구 표시
                    <div className="flex flex-col items-center justify-center h-full text-muted-foreground gap-1 select-none">
                        <span className="text-sm font-medium">선택된 챕터에 해당하는 차트가 여기에 표시됩니다.</span>
                    </div>
                )}
            </div>

            {/* Stream Logs Area (Placeholder) */}
            <div className="flex-1 bg-slate-50 min-h-0 overflow-hidden p-2">
                {focusedTimestamp !== null ? (
                    <StreamLogViewer
                        focusedTimestamp={focusedTimestamp}
                        chapterIndex={currentChapterRange.chapterIndex}
                    />
                ) : (
                    // ✅ [초기 상태] 데이터 로드 전 안내 문구
                    <div className="flex h-full items-center justify-center text-muted-foreground text-sm select-none opacity-50">
                        챕터에 해당하는 방송 로그가 여기에 표시됩니다.
                    </div>
                )}
            </div>
        </section>
    );
}
