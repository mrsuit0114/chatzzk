// 구분하기에는 너무 적기 때문에 현재는 index.ts 파일에 모두 작성합니다.
import { PLATFORM_CODE, USER_ROLE } from "@/constants";


export type PlatformCode = typeof PLATFORM_CODE[keyof typeof PLATFORM_CODE];

export type UserRole = typeof USER_ROLE[keyof typeof USER_ROLE];
