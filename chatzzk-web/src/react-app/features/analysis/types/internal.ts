import { Atmosphere } from "@/constants";
import { PlatformCode } from "@shared/constants/service_codes";
import { ViewType } from "../constants";

// ----------------------------------------------------------------------
// Header & Meta Types
// ----------------------------------------------------------------------
export interface VodHeaderData {
    title: string;
    videoNo: string;
    vodUrl: string;
    platform: PlatformCode;
    platformChannelUrl: string;
    channelName: string;
    channelId: string;
    publishDate: string;
    duration: number;
    avgScore: number;
    atmosphereRatio: Record<Atmosphere, number>;
}

export interface VodAnalysisHeaderProps {
    data: VodHeaderData;
    currentView: ViewType;
    onViewChange: (view: ViewType) => void;
    isInsightLocked?: boolean;
    insightUnlockTime?: Date; // 락 해제 시간 표시용
}

// ----------------------------------------------------------------------
// Analysis Data Types (Component Props)
// ----------------------------------------------------------------------

export interface PeakData {
    timestamp: number;
    volume: number;
    momentum: number;
}

export interface SegmentSummaryData {
    id: string;             // UI용 고유 ID (예: seg-0, seg-1)
    chapterId: string;      // 소속 챕터 ID

    startTime: number;
    endTime: number;

    momentum: number;
    volume: number;

    summary: string;
    keywords: string[];
    atmosphere: Atmosphere;

    score: number;
    volPeak: PeakData;
    mmtPeak: PeakData;
}

export interface ChapterSummaryData {
    id: string;             // UI용 고유 ID (예: ch-0)
    title: string;
    keyTopics: string[];
    startTime: number;
    endTime: number;
}

export interface ClipData {
    startTime: number;      // ms
    endTime: number;        // ms
    volume: number;
    momentum: number;
}

// 차트 시각화용 데이터 (RawStatSeries 변환)
export interface ChartSeriesData {
    timestamp: number;
    volume: number;
    momentum: number;
}

// ----------------------------------------------------------------------
// Stream Log Types
// ----------------------------------------------------------------------
export enum StreamLogType {
    CHAT = 1,
    DONATION = 2,
    ASR = 3,
}

export interface StreamLogData {
    timestamp: number;
    type: StreamLogType;
    content: string;
    user?: string;
}

export interface AnalysisIntervals {
    segmentStep: number; // ms
    chapterStep: number; // ms
    clipStep: number;    // ms
}

// ----------------------------------------------------------------------
// Page State Interface
// ----------------------------------------------------------------------
export interface VodAnalysisPageData {
    meta: VodHeaderData;
    chapters: ChapterSummaryData[];
    segments: SegmentSummaryData[];
    // clips: ClipData[]; // 필요 시 추가
    chartData: ChartSeriesData[]; // InsightView용
}

export interface InsightViewData {
    chapters: ChapterSummaryData[];
    segments: SegmentSummaryData[];
    clips: ClipData[];
}
