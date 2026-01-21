import { api } from "@/lib/api";
import { RawDashboardResponse, StreamLogResponse } from "@shared/schemas/vod-analysis"; // 이전에 정의한 Zod 추론 타입

type AnalysisResponseWithMeta = RawDashboardResponse & {
    _meta: {
        isInsightLocked: boolean;
        insightReleaseAt: string;
    }
};

export const getVodAnalysis = async (platform: string, videoNo: string): Promise<AnalysisResponseWithMeta> => {
    // axios는 기본적으로 JSON을 자동 파싱해줍니다. (data는 이미 객체임)
    const response = await api.get<RawDashboardResponse>(`/vods/analysis/${platform}/${videoNo}`);

    // 1. 헤더에서 메타데이터 추출
    // Axios 헤더는 소문자로 접근하는 것이 안전합니다.
    const isLockedHeader = response.headers['x-insight-locked'];
    const releaseAtHeader = response.headers['x-insight-release-at'];

    const isInsightLocked = isLockedHeader === 'true';
    const insightReleaseAt = releaseAtHeader || '';

    // 2. 바디(JSON)와 헤더 정보를 병합하여 반환
    return {
        ...response.data,
        _meta: {
            isInsightLocked,
            insightReleaseAt
        }
    };
};

// export const getVodAnalysis = async (platform: string, videoNo: string): Promise<RawDashboardResponse> => {
//     const { data } = await api.get<RawDashboardResponse>(`/vods/analysis/${platform}/${videoNo}`);
//     return data;
// };

export const getStreamLog = async (platform: string, videoNo: string, index: number): Promise<StreamLogResponse> => {
    if (index < 0) throw new Error("Invalid log index");

    const { data } = await api.get<StreamLogResponse>(`/vods/logs/${platform}/${videoNo}/${index}`);
    return data;
};
