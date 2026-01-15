import { z } from 'zod';

// ----------------------------------------------------------------------
// 1. 공통/기본 타입
// ----------------------------------------------------------------------
export const AnalysisIntervalsSchema = z.object({
    chapterStep: z.number(), // ms
    segmentStep: z.number(), // ms
    clipStep: z.number(),    // ms
});

export const DashboardMetaInfoSchema = z.object({
    platform: z.string(),
    title: z.string(),
    channelId: z.string(),
    channelName: z.string(),
    videoNo: z.string(),
    publishDate: z.string(),
    duration: z.number(), // seconds
    intervals: AnalysisIntervalsSchema,
});

// ----------------------------------------------------------------------
// 2. 통계 데이터 (Columnar Structure)
// ----------------------------------------------------------------------
export const StatSeriesSchema = z.object({
    volume: z.array(z.number()),
    momentum: z.array(z.number()),
});

export const DashboardStatsSchema = z.object({
    clip: StatSeriesSchema,
    segment: StatSeriesSchema, // segments 배열과 1:1 매핑됨
    atmosphereRatio: z.record(z.string(), z.number()), // Record<string, number>
    avgScore: z.number(),
});

// ----------------------------------------------------------------------
// 3. 세그먼트/챕터 상세
// ----------------------------------------------------------------------
export const SegmentPeakSchema = z.object({
    peakTs: z.number(),
    peakVl: z.number(),
    peakMmt: z.number(),
});

export const SegmentItemSchema = z.object({
    txt: z.string(),
    kwd: z.array(z.string()),
    sc: z.number(),
    atmo: z.string(),
    volPeak: SegmentPeakSchema,
    mmtPeak: SegmentPeakSchema,
});

export const ChapterItemSchema = z.object({
    title: z.string(),
    txt: z.string(),
});

export const StreamLogItemSchema = z.object({
    ts: z.number(),
    ty: z.number(),
    c: z.string(),
    u: z.string().optional(),
});

// ----------------------------------------------------------------------
// 4. 최종 응답 구조 (R2 JSON 파일 구조)
// ----------------------------------------------------------------------

// analytics.json
export const RawDashboardResponseSchema = z.object({
    version: z.literal("1.0"),
    metaInfo: DashboardMetaInfoSchema,
    stats: DashboardStatsSchema,
    segments: z.array(SegmentItemSchema),
    chapters: z.array(ChapterItemSchema),
});

// stream_logs_${index}.json
export const StreamLogResponseSchema = z.object({
    version: z.literal("1.0"),
    streamLogs: z.array(StreamLogItemSchema),
});

// ✅ 타입 추출 (프론트/백엔드에서 사용)
export type RawDashboardResponse = z.infer<typeof RawDashboardResponseSchema>;
export type StreamLogResponse = z.infer<typeof StreamLogResponseSchema>;
export type RawSegmentItem = z.infer<typeof SegmentItemSchema>;
// ... 필요에 따라 추가 export
