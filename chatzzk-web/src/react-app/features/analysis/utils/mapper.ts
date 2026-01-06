import { ChapterSummaryData, SegmentSummaryData } from "../types";
import type { RawDashboardResponse } from "../types/raw";

export function mapRawDataToViewData(raw: RawDashboardResponse) {
    const { segmentStep, chapterStep } = raw.metaInfo.intervals;

    const intervals = raw.metaInfo.intervals;

    // 1. Chapter Mapping
    const chapters: ChapterSummaryData[] = raw.chapters.map((ch, idx) => {
        const startTime = idx * chapterStep;
        return {
            id: `ch-${idx}`,
            title: ch.title,
            summary: ch.txt,
            startTime: startTime,
            endTime: startTime + chapterStep,
        };
    });

    // 2. Segment Mapping
    // stats.segment 리스트와 segments 리스트를 병합(Zip)해야 함
    const segments: SegmentSummaryData[] = raw.segments.map((seg, idx) => {
        const startTime = idx * segmentStep;
        const endTime = startTime + segmentStep;

        // 현재 세그먼트가 속한 챕터 ID 찾기
        // (단순 계산: startTime이 어떤 챕터 범위에 속하는지)
        const chapterIndex = Math.floor(startTime / chapterStep);
        const chapterId = `ch-${chapterIndex}`;

        return {
            id: `seg-${idx}`,
            chapterId: chapterId,

            // 시간 정보
            startTime: startTime,
            endTime: endTime,

            // 메타 정보
            summary: seg.txt,
            keywords: seg.kwd,
            score: seg.sc,
            atmosphere: seg.atmo,

            // 그래프 데이터 (stats 배열에서 인덱스로 조회)
            volume: raw.stats.segment.volume[idx] || 0,
            momentum: raw.stats.segment.momentum[idx] || 0,

            // Peak 정보 (필드명 매핑)
            volPeak: {
                timestamp: seg.volPeak.peakTs,
                volume: seg.volPeak.peakVl,
                momentum: seg.volPeak.peakMmt
            },
            mmtPeak: {
                timestamp: seg.mmtPeak.peakTs,
                volume: seg.mmtPeak.peakVl,
                momentum: seg.mmtPeak.peakMmt
            }
        };
    });


    return { chapters, segments, rawStats: raw.stats, intervals };
}
