// 피크 지점의 상세 데이터 (시간, 모멘텀, 볼륨)
export interface PeakData {
    timestamp: number; // ms 단위 (영상 내 절대 시간)
    volume: number;    // float
    momentum: number;  // float
}

export interface SegmentSummaryData {  // 데이터에서 id는 동일해도되나 렌더링 시 prefix로 구분필요
    id: string;             // 컴포넌트 + 역할, 페이지 단위 prefix, 케밥 표기법을 사용해서 page에서 로드할 때 적용해야겠네
    chapterId: string;      // chapter - 1, 2, ...
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


export interface ChapterSummaryData {
    id: string;             // Chapter ID
    title: string;          // 챕터 제목 (예: "1부: 삼국지 개요")
    summary: string;        // 챕터 전체 요약문
    startTime: number;      // ms
    endTime: number;        // ms
}

export const getAtmosphereColor = (attr: string) => {
    switch (attr.toLowerCase()) {
        case "funny": return "bg-orange-100 text-orange-700 border-orange-200";
        case "tension": return "bg-purple-100 text-purple-700 border-purple-200";
        case "touching": return "bg-pink-100 text-pink-700 border-pink-200";
        default: return "bg-secondary text-secondary-foreground border-transparent";
    }
};
