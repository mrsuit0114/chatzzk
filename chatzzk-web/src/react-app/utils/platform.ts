import { PlatformCode, PLATFORM_CODE } from "@shared/constants/service_codes";

export function formatVodUrl(platform: PlatformCode, videoNo: string): string {
    switch (platform) {
        case PLATFORM_CODE.CHZZK:
            return `https://chzzk.naver.com/video/${videoNo}`
        default:
            return "#";
    }
}

export function formatPlatformChannelUrl(platform: PlatformCode, channelId: string): string {
    switch (platform) {
        case PLATFORM_CODE.CHZZK:
            return `https://chzzk.naver.com/${channelId}`;
        default:
            return "#";
    }
}
