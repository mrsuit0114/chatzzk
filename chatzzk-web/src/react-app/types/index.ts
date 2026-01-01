export const PLATFORM_CODE = {
    CHZZK: "chzzk",
    YOUTUBE: "youtube",
    SOOPLIVE: "sooplive",
} as const;

// 2. 타입 정의 ("chzzk" | "youtube" | "sooplive")
export type PlatformCode = typeof PLATFORM_CODE[keyof typeof PLATFORM_CODE];

// 3. UI 표시용 라벨 매핑 (전역 사용)
// 'all'은 DB에 저장되는 플랫폼은 아니지만 UI 필터용으로 자주 쓰이므로 포함하거나 별도로 관리
export const PLATFORM_LABELS: Record<string, string> = {
    all: "전체",
    [PLATFORM_CODE.CHZZK]: "치지직",
    [PLATFORM_CODE.YOUTUBE]: "유튜브",
    [PLATFORM_CODE.SOOPLIVE]: "숲",
};


export const PLATFORM_COLORS: Record<string, string> = {
    [PLATFORM_CODE.CHZZK]: "bg-green-600 hover:bg-green-700",
    [PLATFORM_CODE.YOUTUBE]: "bg-red-600 hover:bg-red-700",
};
