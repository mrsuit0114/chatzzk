import { Atmosphere, KOREAN_TO_ATMOSPHERE, PlatformCode } from "@/constants";
import { AnalysisIntervals, ChapterSummaryData, ClipData, SegmentSummaryData, StreamLogData, VodMetadata } from "../types";
import type { RawDashboardResponse, StreamLogResponse } from "../types/external";

function mapKoreanAtmosphereRatio(
    raw: Record<string, number>
): Partial<Record<Atmosphere, number>> {
    const result: Partial<Record<Atmosphere, number>> = {};

    for (const [korean, value] of Object.entries(raw)) {
        const atmosphere = KOREAN_TO_ATMOSPHERE[korean];
        if (!atmosphere) continue; // ❗ 알 수 없는 키는 무시

        // 값 검증
        if (typeof value !== "number" || Number.isNaN(value)) continue;

        result[atmosphere] = value;
    }

    return result;
}

function mapRawDashboardMetaInfo(
    raw: RawDashboardResponse
): VodMetadata {
    return {
        platform: raw.metaInfo.platform as PlatformCode,
        title: raw.metaInfo.title,
        channelId: raw.metaInfo.channelId,
        channelName: raw.metaInfo.channelName,
        videoNo: raw.metaInfo.videoNo,
        publishDate: raw.metaInfo.publishDate.slice(0, 10),
        duration: raw.metaInfo.duration,
        intervals: raw.metaInfo.intervals,
        atmosphereRatio: mapKoreanAtmosphereRatio(raw.stats.atmosphereRatio) as Record<Atmosphere, number>,
        avgScore: raw.stats.avgScore,
    };
}

function mapRawChapters(
    raw: RawDashboardResponse,
    intervals: AnalysisIntervals
): ChapterSummaryData[] {
    return raw.chapters.map((ch, idx) => {
        const startTime = idx * intervals.chapterStep;
        return {
            id: `ch-${idx}`,
            title: ch.title,
            summary: ch.txt,
            startTime: startTime,
            endTime: startTime + intervals.chapterStep,
        };
    });
}

function mapRawSegments(
    raw: RawDashboardResponse,
    intervals: AnalysisIntervals
): SegmentSummaryData[] {
    return raw.segments.map((seg, idx) => {
        const startTime = idx * intervals.segmentStep;
        const endTime = startTime + intervals.segmentStep;

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
}

function mapRawClips(
    raw: RawDashboardResponse,
    intervals: AnalysisIntervals
): ClipData[] {
    return raw.stats.clip.volume.map((vol, idx) => ({
        startTime: idx * intervals.clipStep,
        endTime: (idx + 1) * intervals.clipStep,
        volume: vol,
        momentum: raw.stats.clip.momentum[idx] || 0
    }));
}

export function mapRawDataToViewData(raw: RawDashboardResponse) {
    const metaInfo = mapRawDashboardMetaInfo(raw);

    const intervals: AnalysisIntervals = raw.metaInfo.intervals;

    // 1. Chapter Mapping
    const chapters: ChapterSummaryData[] = mapRawChapters(raw, intervals);

    // 2. Segment Mapping
    const segments: SegmentSummaryData[] = mapRawSegments(raw, intervals);

    const clips: ClipData[] = mapRawClips(raw, intervals);

    return { chapters, segments, clips, metaInfo };
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
