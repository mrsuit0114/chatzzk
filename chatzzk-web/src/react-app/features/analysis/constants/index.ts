// 상수에서 파생된 type은 함께 관리할 것
export const VIEW_TYPE = {
    HIGHLIGHT: "highlight",
    INSIGHT: "insight",
} as const;

export type ViewType = typeof VIEW_TYPE[keyof typeof VIEW_TYPE];

export const SORT_OPTIONS = {
    VOLUME: "volume",
    MOMENTUM: "momentum",
    SCORE: "score",
} as const;

export type SortOption = typeof SORT_OPTIONS[keyof typeof SORT_OPTIONS];

export const METRIC_TYPES = {
    SUMMARY: "summary",
    VOL_PEAK: "volPeak",
    MMT_PEAK: "mmtPeak",
} as const;

export type MetricType = typeof METRIC_TYPES[keyof typeof METRIC_TYPES];

export const METRIC_LABELS = {
    summary: "Summary",
    volPeak: "Volume Peak",
    mmtPeak: "Momentum Peak",
} as const;

export const CHART_KEYS = {
    VOLUME: "volume",
    MOMENTUM: "momentum",
} as const;

export type ChartKey = typeof CHART_KEYS[keyof typeof CHART_KEYS];


// ui constants
export const TREND_CHART_X_AXIS_HEIGHT = 20;
export const TREND_CHART_MARGIN = { top: 10, right: 0, left: 0, bottom: 10 } as const;
export const DETAIL_CHART_HEIGHT = 150;
