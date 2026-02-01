// json을 사용하는 곳이 이 페이지 뿐이므로 여기서 관리하는게 맞겠고

// 1. 공통/기본 타입
export interface RawAnalysisIntervals {
    chapterStep: number; // ms
    segmentStep: number; // ms
    clipStep: number;    // ms
}

export interface RawDashboardMetaInfo {
    platform: string;
    title: string;
    channelId: string;
    channelName: string;
    videoNo: string;
    publishDate: string;
    duration: number; // seconds
    intervals: RawAnalysisIntervals;
}

// 2. 통계 데이터 (Columnar Structure)
export interface RawStatSeries {
    volume: number[];
    momentum: number[];
}

export interface RawDashboardStats {
    clip: RawStatSeries;
    segment: RawStatSeries; // segments 배열과 1:1 매핑됨 (인덱스 기준)
    atmosphereRatio: Record<string, number>;
    avgScore: number;
}

// 3. 세그먼트/챕터 상세
export interface RawSegmentPeak {
    peakTs: number;
    peakVl: number;
    peakMmt: number;
}

export interface RawSegmentItem {
    txt: string;
    kwd: string[];
    sc: number;
    atmo: string;
    volPeak: RawSegmentPeak;
    mmtPeak: RawSegmentPeak;
}

export interface RawChapterItem {
    title: string;
    keyTopics: string[];
}

export interface RawStreamLogItem {
    ts: number;
    ty: number;
    c: string;
    u?: string;
}

// 4. 최종 응답 구조
export interface RawDashboardResponse {
    version: "1.0";
    metaInfo: RawDashboardMetaInfo;
    stats: RawDashboardStats;
    segments: RawSegmentItem[];
    chapters: RawChapterItem[];
}

export interface StreamLogResponse {
    version: "1.0";
    streamLogs: RawStreamLogItem[];
}
