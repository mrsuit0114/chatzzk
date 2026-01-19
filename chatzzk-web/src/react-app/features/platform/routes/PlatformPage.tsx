import { useParams } from "react-router-dom";
import { VodCard, VodCardSkeleton } from "@/features/vod/components/VodCard";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { useUrlParams } from "@/hooks/use-url-params";
import { BasePagination } from "@/components/ui/base-pagination";
import { VodListToolbar } from "@/features/vod/components/VodListToolbar";
import { PLATFORM_LABELS } from "@/constants";
import { getVods } from "@/features/vod/api/getVods";
import { VOD_ITEMS_PER_PAGE } from "@shared/constants/ui";
import { cn } from "@/lib/utils";

export function PlatformPage() {
    const { platformId } = useParams<{ platformId: string }>();
    const { query, fromDate, toDate, page, setParams } = useUrlParams();

    // --- [React Query 적용] ---
    const { data, isLoading, isError, isFetching } = useQuery({
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
        <div className="container mx-auto py-8">
            {/* ✅ 광고 배치를 위한 Flex 레이아웃 적용 */}
            <div className="flex justify-center gap-6">

                {/* [좌측 광고 영역] - 2xl(1536px) 이상에서만 표시 */}
                <aside className="hidden 2xl:block w-[160px] shrink-0">
                    <div className="sticky top-24 w-full h-[600px] bg-muted/30 border border-dashed border-muted-foreground/20 rounded-lg flex items-center justify-center text-xs text-muted-foreground">
                        Advertisement (Left)
                    </div>
                </aside>

                {/* [메인 콘텐츠 영역] - 최대 너비 제한으로 가독성 유지 */}
                <main className="flex-1 w-full max-w-5xl space-y-6">
                    <div>
                        <div className="flex items-center gap-3">
                            <h1 className="text-3xl font-bold">{platformName} 분석 아카이브</h1>
                        </div>
                        <p className="text-muted-foreground mt-2">
                            검색 결과: <span className="font-bold text-foreground">{totalCount.toLocaleString()}</span>건
                        </p>
                    </div>

                    <VodListToolbar placeholder="제목 또는 채널명 검색" />

                    {isLoading ? (
                        // ✅ 스켈레톤 UI 적용
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {Array.from({ length: VOD_ITEMS_PER_PAGE }).map((_, i) => (
                                <VodCardSkeleton key={i} />
                            ))}
                        </div>
                    ) : isError ? (
                        <div className="py-20 text-center text-red-500 bg-red-50 rounded-lg">
                            데이터를 불러오는 중에 오류가 발생했습니다.
                        </div>
                    ) : (
                        <>
                            {vods.length > 0 ? (
                                <div className="relative">
                                    {/* ✅ 리스트 영역에 opacity 및 pointer-events 제어 적용 */}
                                    <div className={cn(
                                        "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 transition-opacity duration-200",
                                        isFetching ? "opacity-50 pointer-events-none" : "opacity-100"
                                    )}>
                                        {vods.map((item) => (
                                            <VodCard key={item.videoNo} data={item} />
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div className="py-32 text-center border-2 border-dashed rounded-xl bg-muted/10 text-muted-foreground">
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
                </main>

                {/* [우측 광고 영역] */}
                <aside className="hidden 2xl:block w-[160px] shrink-0">
                    <div className="sticky top-24 w-full h-[600px] bg-muted/30 border border-dashed border-muted-foreground/20 rounded-lg flex items-center justify-center text-xs text-muted-foreground">
                        Advertisement (Right)
                    </div>
                </aside>

            </div>
        </div>
    );
}
