import { api } from "@/lib/api";
import { RawDashboardResponse } from "@shared/schemas/vod-analysis"; // 이전에 정의한 Zod 추론 타입

export const getVodAnalysis = async (platform: string, videoNo: string): Promise<RawDashboardResponse> => {
    const { data } = await api.get<RawDashboardResponse>(`/vods/analysis/${platform}/${videoNo}`);
    return data;
};
