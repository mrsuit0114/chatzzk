import { getVodAnalysis } from "@/features/vod/api/analysis";
import { useAuthStore } from "@/stores";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";


export function useAnalysisData() {
    const { platformId, videoNo } = useParams<{ platformId: string; videoNo: string }>();
    const { user } = useAuthStore();
    const queryClient = useQueryClient();

    return useQuery({
        queryKey: ['vodAnalysis', platformId, videoNo, user?.id],
        queryFn: () => {
            if (!platformId || !videoNo) throw new Error("Invalid URL parameters");
            return getVodAnalysis(platformId, videoNo);
        },
        enabled: !!platformId && !!videoNo,
        retry: 1, // 404/403 등은 재시도 불필요

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
