// 구분하기에는 적기 때문에 현재는 index.ts 파일에 모두 작성합니다.
export const PLATFORM_CODE = {
    CHZZK: "chzzk",
    YOUTUBE: "youtube",
    SOOPLIVE: "sooplive",
} as const;

export const USER_ROLE = {
    OWNER: "owner",
    EDITOR: "editor",
} as const;

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
