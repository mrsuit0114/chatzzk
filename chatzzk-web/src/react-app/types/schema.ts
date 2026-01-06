// import { z } from "zod";

// // ==========================================
// // 1. Enums & Constants
// // ==========================================

// // Python: chatzzk_core.constants.PlatformCode
// // 실제 값 확인 필요 (예시: CHZZK, YOUTUBE 등)
// export const PlatformCodeSchema = z.enum(["chzzk", "youtube", "sooplive"]).describe("플랫폼 코드");

// // Python: chatzzk_core.constants.EntryTypeCode
// // 1: 채팅, 2: 후원, 3: ASR 등 (실제 정의된 상수 값에 맞춤)
// export const EntryTypeCodeSchema = z.union([
//     z.literal(1),
//     z.literal(2),
//     z.literal(3),
// ]).describe("로그 타입 (1: 일반, 2: 후원, 3: ASR)");

// // ==========================================
// // 2. Component Schemas (하위 객체)
// // ==========================================

// // Python: AnalysisIntervals
// export const AnalysisIntervalsSchema = z.object({
//     chapterStep: z.int().describe("챕터 단위 시간 (ms)"),
//     segmentStep: z.int().describe("세그먼트 단위 시간 (ms)"),
//     clipStep: z.int().describe("클립(그래프) 단위 시간 (ms)"),
// });

// // Python: DashboardMetaInfo (alias_generator로 인해 snake_case -> camelCase 변환됨)
// export const DashboardMetaInfoSchema = z.object({
//     vod_id: z.int(),
//     platform: PlatformCodeSchema,
//     platform_url: z.url(),
//     title: z.string(),
//     channelId: z.string().describe("platform_channel_id"),
//     channelName: z.string(),
//     videoNo: z.string(),
//     publishDate: z.iso.datetime().or(z.string()).describe("ISO 8601 string"),
//     duration: z.int().describe("영상 전체 길이 (s)"),
//     intervals: AnalysisIntervalsSchema,
// });

// // Python: StatSeries
// export const StatSeriesSchema = z.object({
//     volume: z.array(z.number()).describe("Volume 값 배열"),
//     momentum: z.array(z.number()).describe("Momentum 값 배열"),
// });

// // Python: SegmentPeak
// export const SegmentPeakSchema = z.object({
//     peakTs: z.int().describe("Peak 타임스탬프 (ms)"),
//     peakVl: z.number().describe("Peak Volume 값"),
//     peakMmt: z.number().describe("Peak Momentum 값"),
// });

// // Python: SegmentItem
// export const SegmentItemSchema = z.object({
//     txt: z.string().describe("세그먼트 요약 텍스트"),
//     kwd: z.array(z.string()).describe("주요 키워드 리스트"),
//     sc: z.number().describe("중요도/흥미도 점수 (Score)"),
//     atmo: z.string().describe("분위기"),
//     avgScore: z.number().describe("세그먼트 평균 점수"), // avg_score -> avgScore

//     volPeak: SegmentPeakSchema, // vol_peak -> volPeak
//     mmtPeak: SegmentPeakSchema, // mmt_peak -> mmtPeak
// });

// // Python: ChapterItem
// export const ChapterItemSchema = z.object({
//     title: z.string(),
//     txt: z.string().describe("챕터 요약"),
// });

// // Python: DashboardStats
// export const DashboardStatsSchema = z.object({
//     clip: StatSeriesSchema.describe("상세 그래프 데이터"),
//     segment: StatSeriesSchema.describe("요약 그래프 데이터"),
//     atmosphere: z.record(z.string(), z.number()).describe("분위기 통계 (dict[str, float])"),
// });

// // Python: StreamLogItem
// export const StreamLogItemSchema = z.object({
//     ts: z.int().describe("타임스탬프 (ms)"),
//     ty: EntryTypeCodeSchema,
//     u: z.string().nullable().optional().describe("사용자명 (None 가능)"),
//     c: z.string().describe("내용 (Content)"),
// });

// // ==========================================
// // 3. API Response Schemas (최상위 응답)
// // ==========================================

// // Python: DashboardResponse
// export const DashboardResponseSchema = z.object({
//     version: z.literal("1.0"),
//     metaInfo: DashboardMetaInfoSchema, // meta_info -> metaInfo
//     stats: DashboardStatsSchema,
//     segments: z.array(SegmentItemSchema),
//     chapters: z.array(ChapterItemSchema),
// });

// // Python: StreamLogResponse
// export const StreamLogResponseSchema = z.object({
//     version: z.literal("1.0"),
//     streamLogs: z.array(StreamLogItemSchema), // stream_logs -> streamLogs
// });

// // ==========================================
// // 4. Type Exports
// // ==========================================

// export type DashboardResponse = z.infer<typeof DashboardResponseSchema>;
// export type StreamLogResponse = z.infer<typeof StreamLogResponseSchema>;

// // 하위 타입들도 필요 시 export
// export type DashboardMetaInfo = z.infer<typeof DashboardMetaInfoSchema>;
// export type SegmentItem = z.infer<typeof SegmentItemSchema>;
// export type ChapterItem = z.infer<typeof ChapterItemSchema>;
// export type StreamLogItem = z.infer<typeof StreamLogItemSchema>;
// export type DashboardStats = z.infer<typeof DashboardStatsSchema>;
// export type AnalysisIntervals = z.infer<typeof AnalysisIntervalsSchema>;


// 받는 파일의 스키마만 정의하고 mapper가 types.py에 정의된 구조로 반환하는 역할을 담당
