import { api } from "@/lib/api";
import { MyVodData } from "@shared/types/vod";

type GetMyVodsParams = {
    page: number;
    query?: string;
    visibility?: 'ALL' | 'PUBLIC' | 'PRIVATE';
};

type GetMyVodsResponse = {
    data: MyVodData[];
    meta: {
        total: number;
        page: number;
        pageSize: number;
        totalPages: number;
    };
};

// 1. 조회 API
export const getMyVods = async (params: GetMyVodsParams): Promise<GetMyVodsResponse> => {
    const { data } = await api.get<GetMyVodsResponse>('/my/vods', {
        params: {
            ...params,
            visibility: params.visibility || 'ALL'
        }
    });
    return data;
};

type UpdateVodExposureParams = {
    videoNo: string;
    isExposed: boolean;
    platform: string;
    channelId: string;
};

// 2. 노출 상태 변경 API (PATCH)
export const updateVodExposure = async ({ videoNo, isExposed, platform, channelId }: UpdateVodExposureParams) => {
    await api.patch(`/my/vods/${videoNo}/exposure`, {
        isExposed,
        platform,    // Body에 포함
        channelId    // Body에 포함
    });
};
