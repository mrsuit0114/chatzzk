import { getVodAnalysis } from "@/features/vod/api/analysis";
import { useAuthStore } from "@/stores";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { MOCK_ANALYSIS_DATA } from "../__mocks__/mockAnalysisData";

const USE_MOCK = import.meta.env.VITE_USE_MOCK_ANALYSIS === "true";

export function useAnalysisData() {
    const { platformId, videoNo } = useParams<{ platformId: string; videoNo: string }>();
    const { user } = useAuthStore();
    const queryClient = useQueryClient();

    return useQuery({
        queryKey: ['vodAnalysis', platformId, videoNo, user?.id],
        queryFn: async () => {
            if (USE_MOCK) {
                await new Promise((r) => setTimeout(r, 400)); // 로딩 스피너 확인용
                return { ...MOCK_ANALYSIS_DATA, _meta: { isInsightLocked: false, insightReleaseAt: "" } };
            }
            if (!platformId || !videoNo) throw new Error("Invalid URL parameters");
            return getVodAnalysis(platformId, videoNo);
        },
        enabled: !!platformId && !!videoNo,
        retry: 1,

        placeholderData: (previousData) => {
            if (previousData) return previousData;
            const cachedData = queryClient.getQueryData<any>([
                'vodAnalysis',
                platformId,
                videoNo,
                undefined
            ]);
            return cachedData;
        },
    });
}
