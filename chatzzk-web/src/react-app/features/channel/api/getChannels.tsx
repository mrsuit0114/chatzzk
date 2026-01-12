import { api } from "@/lib/api";
import { ChannelData } from "@shared/types/channel";

type GetChannelsParams = {
    platform: string;
    page: number;
    query: string;
};

type ChannelResponse = {
    data: ChannelData[];
    meta: {
        total: number;
        page: number;
        pageSize: number;
        totalPages: number;
    };
};

export const getChannels = async (params: GetChannelsParams): Promise<ChannelResponse> => {
    const response = await api.get('/channels', {
        params: {
            platform: params.platform === 'all' ? 'ALL' : params.platform, // 'all' -> 'ALL' 변환
            page: params.page,
            query: params.query,
        },
    });
    return response.data;
};
