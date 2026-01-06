import { UserRole, PlatformCode } from "@/types";


export interface AuthUser {
    id: string;
    role: UserRole;    // 역할
    channelName: string; // 담당 채널명 (주인: 본인채널, 편집자: 담당채널)
    platform: PlatformCode; // 'chzzk' | 'youtube' ...
    platformChannelUrl: string; // 실제 채널 링크
}
