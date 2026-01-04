import { PlatformCode } from "@/types";

export interface VodCardUI {
    videoNo: string;
    channelId: string;
    title: string;
    channelName: string;
    thumbnailUrl?: string;
    publishDate: string;      // [Formatted] "2024-01-01"
    duration: string;    // [Formatted] "01:30:00"
    platform: PlatformCode
}
