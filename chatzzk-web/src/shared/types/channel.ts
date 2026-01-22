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


const BaseChannelDbFields = {
    channel_id: z.number(),
    platform_code: PlatformCodeSchema, // 기존에 정의된 Enum 스키마 사용 가정
    platform_channel_id: z.string(),
    channel_name: z.string(),
    last_vod_crawled_at: z.string().nullable(),
    vod_exposure_delay_hours: z.number(),
    vod_detail_exposure_delay_hours: z.number(),
    is_collection_enabled: z.boolean(),
};

// 2. 공통 변환 로직 (Snake -> Camel)
const transformBaseChannel = (data: any) => ({
    id: data.channel_id,
    platform: data.platform_code,
    channelId: data.platform_channel_id,
    channelName: data.channel_name,
    lastVodCrawledAt: data.last_vod_crawled_at,
    vodExposureDelayHours: data.vod_exposure_delay_hours,
    vodDetailExposureDelayHours: data.vod_detail_exposure_delay_hours,
    isCollectionEnabled: data.is_collection_enabled,
});

export const ChannelDetailSchema = z.object(BaseChannelDbFields)
    .transform(transformBaseChannel);

export type ChannelDetailData = z.infer<typeof ChannelDetailSchema>;

const metadataShape = {
    streamer_nicknames: z.array(z.string()).nullish().default([]),
    streamer_sex: z.enum(["남성", "여성"]).nullish().default("남성"),
    fan_nicknames: z.array(z.string()).nullish().default([]),
    additional_info: z.array(z.string()).nullish().default([]),
};

// 2. [조회용] DB(Snake) -> 앱(Camel) 변환 스키마
export const ChannelMetadataSchema = z.object(metadataShape).transform((data) => ({
    streamerNicknames: data.streamer_nicknames ?? [],
    streamerSex: data.streamer_sex ?? "남성",
    fanNicknames: data.fan_nicknames ?? [],
    additionalInfo: data.additional_info ?? [],
}));

export type ChannelMetadata = z.output<typeof ChannelMetadataSchema>;

// 3. [저장용] 앱(Camel) -> DB(Snake) 변환 스키마
// 프론트에서 보낸 데이터를 다시 DB 모양으로 되돌려줍니다.
export const ChannelMetadataUpdateSchema = z.object({
    streamerNicknames: z.array(z.string()).default([]),
    streamerSex: z.enum(["남성", "여성"]).default("남성"),
    fanNicknames: z.array(z.string()).default([]),
    additionalInfo: z.array(z.string()).default([]),
}).transform((data) => ({
    streamer_nicknames: data.streamerNicknames, // 다시 Snake로!
    streamer_sex: data.streamerSex,
    fan_nicknames: data.fanNicknames,
    additional_info: data.additionalInfo,
}));

export const MyChannelSchema = z.object({
    ...BaseChannelDbFields,
    metadata: z.object(metadataShape),
}).transform((data) => ({
    ...transformBaseChannel(data),
    channelMetadata: ChannelMetadataSchema.parse(data.metadata),
}));

export type MyChannelData = z.output<typeof MyChannelSchema>;
