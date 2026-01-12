// 구분하기에는 적기 때문에 현재는 index.ts 파일에 모두 작성합니다.
// 상수에서 파생된 type은 함께 관리할 것
import { PLATFORM_CODE, PlatformCode, USER_ROLE, UserRole } from '@shared/constants/service_codes';
export { PLATFORM_CODE, USER_ROLE, type PlatformCode, type UserRole };

export const PLATFORM_LABELS: Record<string | "all", string> = {
    all: "전체",
    [PLATFORM_CODE.CHZZK]: "치지직",
    [PLATFORM_CODE.YOUTUBE]: "유튜브",
    [PLATFORM_CODE.SOOP]: "숲",
} as const;

export const PLATFORM_COLORS: Record<string, string> = {
    [PLATFORM_CODE.CHZZK]: "bg-green-600 hover:bg-green-700",
    [PLATFORM_CODE.YOUTUBE]: "bg-red-600 hover:bg-red-700",
    [PLATFORM_CODE.SOOP]: "bg-blue-600 hover:bg-blue-700",
} as const;

export const ATMOSPHERE = {
    NEUTRAL: "neutral",
    HILARIOUS: "hilarious",
    SADNESS: "sadness",
    ANGER: "anger",
    BOOING: "booing",
    ADMIRATION: "admiration",
    ANTICIPATION: "anticipation",
    ENCOURAGEMENT: "encouragement",
} as const;

export type Atmosphere = typeof ATMOSPHERE[keyof typeof ATMOSPHERE];

export const KOREAN_TO_ATMOSPHERE: Record<string, Atmosphere> = {
    "중립": ATMOSPHERE.NEUTRAL,
    "폭소": ATMOSPHERE.HILARIOUS,
    "슬픔": ATMOSPHERE.SADNESS,
    "분노": ATMOSPHERE.ANGER,
    "야유": ATMOSPHERE.BOOING,
    "감탄": ATMOSPHERE.ADMIRATION,
    "기대": ATMOSPHERE.ANTICIPATION,
    "격려": ATMOSPHERE.ENCOURAGEMENT,
} as const;

export const ATMOSPHERE_LABELS: Record<Atmosphere, string> = {
    [ATMOSPHERE.NEUTRAL]: "중립",
    [ATMOSPHERE.HILARIOUS]: "폭소",
    [ATMOSPHERE.SADNESS]: "슬픔",
    [ATMOSPHERE.ANGER]: "분노",
    [ATMOSPHERE.BOOING]: "야유",
    [ATMOSPHERE.ADMIRATION]: "감탄",
    [ATMOSPHERE.ANTICIPATION]: "기대",
    [ATMOSPHERE.ENCOURAGEMENT]: "격려",
} as const;
