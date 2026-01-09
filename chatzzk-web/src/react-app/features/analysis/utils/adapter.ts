// internal -> interanl?

import { PLATFORM_CODE, PlatformCode } from "@/constants";
import { VodHeaderData, VodMetadata } from "../types";

export function VodMetadataToVodHeaderData(metaInfo: VodMetadata): VodHeaderData {
    return ({
        title: metaInfo.title,
        videoNo: metaInfo.videoNo,
        vodUrl: formatVodUrl(metaInfo.platform, metaInfo.videoNo), // VOD URL은 별도 필드에서 매핑 필요
        platform: metaInfo.platform,
        platformChannelUrl: formatPlatformChannelUrl(metaInfo.platform, metaInfo.channelId), // 플랫폼 채널 URL도 별도 매핑 필요
        channelName: metaInfo.channelName,
        channelId: metaInfo.channelId,
        publishDate: metaInfo.publishDate,
        duration: metaInfo.duration,
        avgScore: metaInfo.avgScore,
        atmosphereRatio: metaInfo.atmosphereRatio,
    });
}

function formatVodUrl(platform: PlatformCode, videoNo: string): string {
    switch (platform) {
        case PLATFORM_CODE.CHZZK:
            return `https://chzzk.naver.com/video/${videoNo}`
        default:
            return "";
    }
}

function formatPlatformChannelUrl(platform: PlatformCode, channelId: string): string {
    switch (platform) {
        case PLATFORM_CODE.CHZZK:
            return `https://chzzk.naver.com/${channelId}`;
        default:
            return "";
    }
}
