// 피크 지점의 상세 데이터 (시간, 모멘텀, 볼륨)
export interface PeakData {
    timestamp: number; // ms 단위 (영상 내 절대 시간)
    volume: number;    // float
    momentum: number;  // float
}

export interface SegmentSummaryData {
    id: string;             // segment - timestamp 고유 ID
    chapterId: string;      // chapter - timestamp 부모 챕터 ID (연결용)
    startTime: number;      // ms
    endTime: number;        // ms

    summary: string;        // 상세 요약 본문 (가변 길이)
    keywords: string[];     // ["유비", "조조", "개그", ...]
    atmosphere: string;     // 대표 분위기 (예: "Funny", "Tension") - 필터링용

    momentum: number;      // 급상승 지표 (모멘텀)
    volume: number;        // 화력 지표 (볼륨)
    // 정렬 및 평가 지표
    score: number;          // 서비스 평가 점수
    volPeak: PeakData;      // 화력(Volume) 기준 피크 정보
    mmtPeak: PeakData;      // 급상승(Momentum) 기준 피크 정보
}

export const SORT_OPTIONS = {
    VOLUME: "volume",
    MOMENTUM: "momentum",
    SCORE: "score",
} as const;

export type SortOption = typeof SORT_OPTIONS[keyof typeof SORT_OPTIONS];
