// db와 백엔드와의 경계 - 일반적으로는 db의 경우 snake_case, 백엔드는 camelCase를 맞추기 위해 사용
import { z } from 'zod';
import { PlatformCodeSchema } from '@shared/constants/service_codes';

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
