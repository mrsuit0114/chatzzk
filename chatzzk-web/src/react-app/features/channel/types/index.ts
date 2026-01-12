import { PlatformCode } from "@shared/constants/service_codes";

export interface ChannelData {
    channelName: string;
    platform: PlatformCode;
    channelId: string;
}
