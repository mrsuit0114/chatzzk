import { PlatformCode } from "@/types";

export interface ChannelCardUI {
    id: string;  // 채널 페이지를 접근할 수 있도록
    name: string;
    profileUrl?: string; // 프로필 이미지
    description?: string;

    platform: PlatformCode;
}
