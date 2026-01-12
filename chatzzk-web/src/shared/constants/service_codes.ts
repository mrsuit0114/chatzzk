import { z } from "zod";

export const PLATFORM_CODE = {
    CHZZK: "CHZZK",
    YOUTUBE: "YOUTUBE",
    SOOP: "SOOP",
} as const;

export const PlatformCodeSchema = z.enum([
    PLATFORM_CODE.CHZZK,
    PLATFORM_CODE.YOUTUBE,
    PLATFORM_CODE.SOOP,
]);

export type PlatformCode = z.infer<typeof PlatformCodeSchema>;

export const USER_ROLE = {
    ADMIN: "ADMIN",
    OWNER: "OWNER",
    EDITOR: "EDITOR",
    USER: "USER",
} as const;

export const UserRoleSchema = z.enum([
    USER_ROLE.ADMIN,
    USER_ROLE.OWNER,
    USER_ROLE.EDITOR,
    USER_ROLE.USER,
]);

export type UserRole = z.infer<typeof UserRoleSchema>;

export const AUTH_DOMAIN = '@chatzzk.auth';
export const ID_REGEX = /^[a-z0-9]{4,20}$/;
export const PASSWORD_MIN_LENGTH = 8;
