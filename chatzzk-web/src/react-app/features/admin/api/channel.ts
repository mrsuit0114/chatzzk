import { api } from "@/lib/api";
import { PlatformCode } from "@shared/constants/service_codes";
import { ChannelMetadata } from "@shared/types/channel";

export type AddChannelRequest = {
    platform: PlatformCode;
    channelId: string;
    channelName: string;
    shouldLinkUser: boolean;
    targetUserName?: string;
    metadata: ChannelMetadata; // 순수 CamelCase 객체 (폼 값 그대로)
};

export const addChannel = async (params: AddChannelRequest) => {
    // POST /api/admin/channels
    const { data } = await api.post('/admin/channels', params);
    return data;
};

export type AdminChannelDetail = {
    id: number;
    platform_code: PlatformCode;
    platform_channel_id: string;
    channel_name: string;
    is_collection_enabled: boolean;
    vod_exposure_delay_hours: number;
    vod_detail_exposure_delay_hours: number;
    owner: { user_name: string } | null; // 소유자가 없을 수 있음
    channel_metadata: {
        attributes: ChannelMetadata; // JSONB가 파싱된 상태
    } | null;
};

// 2. 조회 API
export const getChannelDetail = async (params: { platform: string; channelId: string }) => {
    // GET /api/admin/channels/detail?platform=CHZZK&channelId=...
    const { data } = await api.get<{ data: AdminChannelDetail }>('/admin/channels/detail', { params });
    return data.data;
};

// 3. 일반 정보 수정 요청 타입
export type UpdateChannelGeneralRequest = {
    channelName: string;
    isCollectionEnabled: boolean;
    vodExposureDelayHours: number;
    vodDetailExposureDelayHours: number;
    metadata: ChannelMetadata; // CamelCase
};

export const updateChannelGeneral = async (id: number, body: UpdateChannelGeneralRequest) => {
    const { data } = await api.put(`/admin/channels/${id}/general`, body);
    return data;
};

// 4. 소유권 이전 API
export const transferOwnership = async (id: number, targetUserName: string) => {
    const { data } = await api.post(`/admin/channels/${id}/transfer-ownership`, { targetUserName });
    return data;
};
