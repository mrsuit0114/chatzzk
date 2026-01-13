// db와 백엔드와의 경계 - 일반적으로는 db의 경우 snake_case, 백엔드는 camelCase를 맞추기 위해 사용
// type은 프론트엔드에서 사용됨
import { z } from 'zod';
import { PlatformCodeSchema, VodPipelineStatusSchema } from '@shared/constants/service_codes';

export const VodDataSchema = z.object({
    video_no: z.string(),
    channel_id: z.string(),
    video_title: z.string(),
    channel_name: z.string(),
    publish_date: z.string(),
    duration: z.number(),
    platform: PlatformCodeSchema
}).transform((data) => ({
    videoNo: data.video_no,
    channelId: data.channel_id,
    title: data.video_title,
    channelName: data.channel_name,
    publishDate: data.publish_date,
    duration: data.duration,
    platform: data.platform
}));

export type VodData = z.infer<typeof VodDataSchema>;

export const MyVodDataSchema = z.object({
    video_no: z.string(),
    channel_id: z.string(),
    video_title: z.string(),
    channel_name: z.string(),
    publish_date: z.string(),
    duration: z.number(),
    platform_code: PlatformCodeSchema,
    pipeline_status: VodPipelineStatusSchema,
    is_exposed: z.boolean(),
}).transform((data) => ({
    videoNo: data.video_no,
    channelId: data.channel_id,
    title: data.video_title,
    channelName: data.channel_name,
    publishDate: data.publish_date,
    duration: data.duration,
    platform: data.platform_code,
    status: data.pipeline_status, // 상태 (Badge 표시용)
    isExposed: data.is_exposed,   // 스위치 제어용
}));

export type MyVodData = z.infer<typeof MyVodDataSchema>;
