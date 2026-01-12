import { PlatformCode } from "@/constants";

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
