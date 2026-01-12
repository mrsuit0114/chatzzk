export const PLATFORM_CODE = {
    CHZZK: "chzzk",
    YOUTUBE: "youtube",
    SOOP: "soop",
} as const;

export type PlatformCode = typeof PLATFORM_CODE[keyof typeof PLATFORM_CODE];

export const USER_ROLE = {
    ADMIN: "admin",
    OWNER: "owner",
    EDITOR: "editor",
} as const;

export type UserRole = typeof USER_ROLE[keyof typeof USER_ROLE];

export const AUTH_DOMAIN = '@chatzzk.auth';
export const ID_REGEX = /^[a-z0-9]+$/;
