import { z } from "zod";

export const CONTACT_EMAIL = "chatzzkcontact@gmail.com"

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

export const AUTH_DOMAIN = 'chatzzk.auth';
const ID_REGEX = /^[a-z0-9]{4,20}$/;
const PASSWORD_MIN_LENGTH = 8;


export const UserIdSchema = z.string().min(4).max(20).regex(ID_REGEX, "4~20자의 영문 소문자, 숫자만 사용 가능합니다.");
export type UserId = z.infer<typeof UserIdSchema>;

export const PasswordSchema = z.string().min(PASSWORD_MIN_LENGTH, `비밀번호는 최소 ${PASSWORD_MIN_LENGTH}자 이상이어야 합니다.`);
export type Password = z.infer<typeof PasswordSchema>;

export const DELAY_OPTIONS = [
    { value: "0", label: "즉시 공개" },
    { value: "12", label: "12시간 후" },
    { value: "24", label: "1일 후" },
    { value: "72", label: "3일 후" },
    { value: "168", label: "7일 후" },
    { value: "999999", label: "공개 안 함" },
]

export const BAN_DURATION = '876000h'

export const VOD_PIPELINE_STATUS = {
    PENDING: "PENDING",
    PROCESSING: "PROCESSING",
    COMPLETED: "COMPLETED",
    FAILED: "FAILED",
}

export const VodPipelineStatusSchema = z.enum([
    VOD_PIPELINE_STATUS.PENDING,
    VOD_PIPELINE_STATUS.PROCESSING,
    VOD_PIPELINE_STATUS.COMPLETED,
    VOD_PIPELINE_STATUS.FAILED,
]);

export type VodPipelineStatus = z.infer<typeof VodPipelineStatusSchema>;
