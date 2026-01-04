import { PlatformCode } from "@/types";

export interface ChannelCardUI {
    name: string;
    platform: PlatformCode;
    channelId: string;

    profileUrl?: string; // 프로필 이미지
    description?: string;
}
