import { useParams } from "react-router-dom";
import { VodCard } from "@/features/vod/components/VodCard";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { useUrlParams } from "@/hooks/use-url-params";
import { BasePagination } from "@/components/ui/base-pagination";
import { VodListToolbar } from "@/features/vod/components/VodListToolbar";
import { PLATFORM_LABELS } from "@/constants";
import { getVods } from "@/features/vod/api/getVods";

export function PlatformPage() {
    const { platformId } = useParams<{ platformId: string }>();
    const { query, fromDate, toDate, page, setParams } = useUrlParams();

    // --- [React Query 적용] ---
    const { data, isLoading, isError } = useQuery({
        // 1. Query Key: 이 배열이 '캐시의 이름표'가 됩니다.
        // 이 값들이 똑같으면 API 요청을 안 하고 캐시된 데이터를 줍니다.
        queryKey: ['vods', platformId, page, query, fromDate, toDate],

        // 2. Query Function: 데이터가 없을 때 실행할 함수
        queryFn: () => getVods({
            platform: platformId!,
            page,
            query,
            from: fromDate,
            to: toDate
        }),

        // 3. 옵션 설정
        enabled: !!platformId, // platformId가 있을 때만 실행
        placeholderData: keepPreviousData, // ✅ 페이지 넘길 때 "깜빡임" 방지 (이전 데이터 유지)
        staleTime: 1000 * 60 * 5, // ✅ 5분 동안은 "신선한 데이터"로 취급 (뒤로가기 시 재요청 안 함)
    });

    // 데이터 추출 (없으면 기본값)
    const vods = data?.data || [];
    const totalCount = data?.meta.total || 0;
    const totalPages = data?.meta.totalPages || 0;

    // --- [렌더링] ---
    if (!platformId || !PLATFORM_LABELS[platformId.toUpperCase()]) {
        return <div className="container py-20 text-center">존재하지 않는 플랫폼입니다.</div>;
    }

    const platformName = PLATFORM_LABELS[platformId.toUpperCase()];

    return (
        <div className="container mx-auto py-8 space-y-6">
            <div>
                <h1 className="text-3xl font-bold">{platformName} 분석 아카이브</h1>
                <p className="text-muted-foreground mt-2">
                    총 <span className="font-bold text-foreground">{totalCount}</span>개의 영상이 검색되었습니다.
                </p>
            </div>

            <VodListToolbar placeholder="제목 또는 채널명 검색" />

            {/* 로딩 중일 때 UI 처리 (Skeleton 등 사용 가능) */}
            {isLoading ? (
                <div className="py-20 text-center">로딩 중...</div>
            ) : isError ? (
                <div className="py-4 text-center text-red-500">데이터를 불러오는 중에 오류가 발생했습니다.</div>
            ) : (
                <>
                    {vods.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                            {vods.map((item) => (
                                <VodCard key={item.videoNo} data={item} />
                            ))}
                        </div>
                    ) : (
                        <div className="py-20 text-center border rounded-lg bg-secondary/10 text-muted-foreground">
                            조건에 맞는 영상이 없습니다.
                        </div>
                    )}
                </>
            )}

            {totalPages > 1 && (
                <BasePagination
                    total={totalPages}
                    page={page}
                    onChange={(newPage) => setParams({ page: newPage })}
                />
            )}
        </div>
    );
}
