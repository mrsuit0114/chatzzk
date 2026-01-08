import { KOREAN_TO_ATMOSPHERE } from "@/constants";
import { AnalysisIntervals, ChapterSummaryData, ClipData, SegmentSummaryData, StreamLogData } from "../types";
import type { RawDashboardResponse, StreamLogResponse } from "../types/external";

export function mapRawDataToViewData(raw: RawDashboardResponse) {
    const intervals: AnalysisIntervals = raw.metaInfo.intervals;

    // 1. Chapter Mapping
    const chapters: ChapterSummaryData[] = raw.chapters.map((ch, idx) => {
        const startTime = idx * intervals.chapterStep;
        return {
            id: `ch-${idx}`,
            title: ch.title,
            summary: ch.txt,
            startTime: startTime,
            endTime: startTime + intervals.chapterStep,
        };
    });

    // 2. Segment Mapping
    // stats.segment 리스트와 segments 리스트를 병합(Zip)해야 함
    const segments: SegmentSummaryData[] = raw.segments.map((seg, idx) => {
        const startTime = idx * intervals.segmentStep;
        const endTime = startTime + intervals.segmentStep;

        // 현재 세그먼트가 속한 챕터 ID 찾기
        // (단순 계산: startTime이 어떤 챕터 범위에 속하는지)
        const chapterIndex = Math.floor(startTime / intervals.chapterStep);
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
            atmosphere: KOREAN_TO_ATMOSPHERE[seg.atmo],

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

    const clips: ClipData[] = raw.stats.clip.volume.map((vol, idx) => ({
        startTime: idx * intervals.clipStep,
        endTime: (idx + 1) * intervals.clipStep,
        volume: vol,
        momentum: raw.stats.clip.momentum[idx] || 0
    }));

    return { chapters, segments, clips, intervals };
}

export function mapRawStreamLogs(rawLogs: StreamLogResponse): StreamLogData[] {
    const streamLogs = rawLogs.streamLogs.map(log => ({
        timestamp: log.ts,
        type: log.ty,
        user: log.u ?? undefined,
        content: log.c
    }));

    return streamLogs;
}
