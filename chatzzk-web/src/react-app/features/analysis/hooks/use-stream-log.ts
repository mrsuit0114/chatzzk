import { getStreamLog } from "@/features/vod/api/analysis";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

export function useStreamLog(chapterIndex: number | null) {
    const { platformId, videoNo } = useParams<{ platformId: string; videoNo: string }>();

    return useQuery({
        // 키에 index를 포함시켜서 변경 시 자동 리패칭
        queryKey: ['vodStreamLog', platformId, videoNo, chapterIndex],
        queryFn: () => {
            if (!platformId || !videoNo || chapterIndex === null) throw new Error("Invalid parameters");
            return getStreamLog(platformId, videoNo, chapterIndex);
        },
        // index가 유효할 때만 요청 보냄
        enabled: !!platformId && !!videoNo && chapterIndex !== null && chapterIndex >= 0,

        // 로그 데이터는 불변(Immutable)하므로 캐시를 길게 유지
        staleTime: Infinity,
        gcTime: 1000 * 60 * 60,
        retry: 1,
    });
}
