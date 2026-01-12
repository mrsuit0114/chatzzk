import { PlatformCode } from "@shared/constants/service_codes";

export interface VodData {
    videoNo: string;
    channelId: string;
    title: string;
    channelName: string;
    thumbnailUrl?: string;
    publishDate: string;      // [Formatted] "2024-01-01"
    duration: number;
    platform: PlatformCode
}
