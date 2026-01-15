import { getVodAnalysis } from "@/features/vod/api/analysis";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";


export function useAnalysisData() {
    const { platformId, videoNo } = useParams<{ platformId: string; videoNo: string }>();

    return useQuery({
        queryKey: ['vodAnalysis', platformId, videoNo],
        queryFn: () => {
            if (!platformId || !videoNo) throw new Error("Invalid URL parameters");
            return getVodAnalysis(platformId, videoNo);
        },
        enabled: !!platformId && !!videoNo,
        retry: 1, // 404/403 등은 재시도 불필요
    });
}
