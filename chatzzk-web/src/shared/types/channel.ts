// db와 백엔드와의 경계 - 일반적으로는 db의 경우 snake_case, 백엔드는 camelCase를 맞추기 위해 사용
// 혹은 컬럼의 이름을 웹 서비스에서 직접 사용하는 것보다 직관적인 이름을 적용할 때: ex) user -> userProfile


import { z } from 'zod';
import { PlatformCodeSchema } from '@shared/constants/service_codes';

// 1. 기본 정보 (카드용 - List View)
// 검색, 목록 조회 등 가볍게 사용할 때
export const ChannelDataSchema = z.object({
    platform_code: PlatformCodeSchema,
    platform_channel_id: z.string(), // 플랫폼별 ID (URL용)
    channel_name: z.string(),
}).transform((data) => ({
    platform: data.platform_code,
    channelId: data.platform_channel_id, // 표시용 ID
    channelName: data.channel_name,
}));

export type ChannelData = z.infer<typeof ChannelDataSchema>;

export const ChannelDetailSchema = z.object({
    // DB Output (Snake Case)
    channel_id: z.number(),
    platform_code: PlatformCodeSchema,
    platform_channel_id: z.string(),
    channel_name: z.string(),
    last_vod_crawled_at: z.string().nullable(),
    vod_exposure_delay_hours: z.number(),
    vod_detail_exposure_delay_hours: z.number(),
    is_collection_enabled: z.boolean(),
}).transform((data) => ({
    // Frontend Output (Camel Case)
    id: data.channel_id,
    platform: data.platform_code,
    channelId: data.platform_channel_id,
    channelName: data.channel_name,
    lastVodCrawledAt: data.last_vod_crawled_at,
    vodExposureDelayHours: data.vod_exposure_delay_hours,
    vodDetailExposureDelayHours: data.vod_detail_exposure_delay_hours,
    isCollectionEnabled: data.is_collection_enabled,
}));

export type ChannelDetailData = z.infer<typeof ChannelDetailSchema>;
