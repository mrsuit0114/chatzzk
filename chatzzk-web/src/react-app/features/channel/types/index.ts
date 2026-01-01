import { PlatformCode } from "@/types";

export interface ChannelCardUI {
    id: number;
    name: string;
    profileUrl?: string; // 프로필 이미지
    description?: string;

    platform: PlatformCode;
}
