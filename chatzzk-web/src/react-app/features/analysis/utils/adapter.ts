// internal -> interanl?
import { formatVodUrl, formatPlatformChannelUrl } from "@/utils/platform";
import { PlatformCode } from "@shared/constants/service_codes";
import { KOREAN_TO_ATMOSPHERE } from "@/constants";
import { RawDashboardMetaInfo, RawDashboardStats, VodHeaderData, RawDashboardResponse, SegmentSummaryData, ChapterSummaryData, RawChapterItem, RawSegmentItem, ClipData, RawStreamLogItem, StreamLogData, StreamLogType } from "../types";

export function transformRawToHeaderData(
    meta: RawDashboardMetaInfo,
    stats: RawDashboardStats
): VodHeaderData {
    return ({
        title: meta.title,
        videoNo: meta.videoNo,
        platform: meta.platform as PlatformCode, // Zod string -> Enum casting
        channelName: meta.channelName,
        channelId: meta.channelId,
        publishDate: meta.publishDate,
        duration: meta.duration,

        // 2. Stats에서 가져오는 정보
        avgScore: stats.avgScore,
        atmosphereRatio: stats.atmosphereRatio, // Record<string, number>

        // 3. URL 유틸리티로 생성하는 정보
        vodUrl: formatVodUrl(meta.platform as PlatformCode, meta.videoNo),
        platformChannelUrl: formatPlatformChannelUrl(meta.platform as PlatformCode, meta.channelId),
    });
}

export function transformHighlightData(rawData: RawDashboardResponse): {
    segments: SegmentSummaryData[];
    chapters: ChapterSummaryData[];
} {
    const { metaInfo, segments: rawSegments, chapters: rawChapters, stats } = rawData;
    const { segmentStep, chapterStep } = metaInfo.intervals;

    // 1. 챕터 변환 (Chapters)
    const chapters: ChapterSummaryData[] = rawChapters.map((raw: RawChapterItem, index: number) => {
        const startTime = index * chapterStep;
        return {
            id: `ch-${index}`, // UI용 ID 생성
            title: raw.title,
            summary: raw.txt,
            startTime: startTime,
            endTime: startTime + chapterStep,
        };
    });

    // 2. 세그먼트 변환 (Segments)
    const segments: SegmentSummaryData[] = rawSegments.map((raw: RawSegmentItem, index: number) => {
        const startTime = index * segmentStep;
        const endTime = startTime + segmentStep;
        const chapterIndex = Math.floor(startTime / chapterStep);

        // 챕터 배열 범위를 벗어나지 않도록 방어 코드
        const safeChapterIndex = Math.min(chapterIndex, chapters.length - 1);
        const parentChapterId = chapters[safeChapterIndex]?.id || '';

        return {
            id: `seg-${index}`,
            chapterId: parentChapterId, // 챕터 연결
            startTime,
            endTime,

            summary: raw.txt,
            keywords: raw.kwd,
            atmosphere: KOREAN_TO_ATMOSPHERE[raw.atmo],
            momentum: stats.segment.momentum[index],
            volume: stats.segment.volume[index],

            score: raw.sc,
            volPeak: {
                timestamp: raw.volPeak.peakTs,
                volume: raw.volPeak.peakVl,
                momentum: raw.volPeak.peakMmt
            },
            mmtPeak: {
                timestamp: raw.mmtPeak.peakTs,
                volume: raw.mmtPeak.peakVl,
                momentum: raw.mmtPeak.peakMmt
            }
        };
    });

    return { chapters, segments };
}

export function transformClipsData(rawData: RawDashboardResponse): ClipData[] {
    const { stats, metaInfo } = rawData;
    const { clipStep } = metaInfo.intervals;
    const { volume, momentum } = stats.clip;

    // volume과 momentum 배열 길이가 같다고 가정
    return volume.map((vol, index) => {
        const startTime = index * clipStep;
        return {
            startTime,
            endTime: startTime + clipStep,
            volume: vol,
            momentum: momentum[index] || 0,
        };
    });
}

export function transformStreamLog(raw: RawStreamLogItem): StreamLogData {
    return {
        timestamp: raw.ts,
        type: raw.ty as StreamLogType,
        content: raw.c,
        user: raw.u,
    };
}
