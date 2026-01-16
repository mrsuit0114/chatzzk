import { api } from "@/lib/api";
import { RawDashboardResponse, StreamLogResponse } from "@shared/schemas/vod-analysis"; // 이전에 정의한 Zod 추론 타입

export const getVodAnalysis = async (platform: string, videoNo: string): Promise<RawDashboardResponse> => {
    const { data } = await api.get<RawDashboardResponse>(`/vods/analysis/${platform}/${videoNo}`);
    return data;
};

export const getStreamLog = async (platform: string, videoNo: string, index: number): Promise<StreamLogResponse> => {
    if (index < 0) throw new Error("Invalid log index");

    const { data } = await api.get<StreamLogResponse>(`/vods/logs/${platform}/${videoNo}/${index}`);
    return data;
};
