import { useParams } from "react-router-dom";
import { VodCard, VodCardSkeleton } from "@/features/vod/components/VodCard";
import { ChannelProfile, ChannelProfileSkeleton } from "../components/ChannelProfile";
import { VodListToolbar } from "@/features/vod/components/VodListToolbar";
import { BasePagination } from "@/components/ui/base-pagination"; // 파일명 수정 반영
import { useUrlParams } from "@/hooks/use-url-params";
import { getVods } from "@/features/vod/api/getVods";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { getChannelDetail } from "../api/getChannelDetail";
import { cn } from "@/lib/utils";


export function ChannelPage() {
    const { platformId, channelId } = useParams<{ platformId: string; channelId: string }>();
    const { query, fromDate, toDate, page, setParams } = useUrlParams();

    const platformCode = platformId?.toUpperCase() || '';

    // 1. [Query] 채널 상세 정보 조회
    const { data: channelData, isLoading: isChannelLoading, isError: isChannelError } = useQuery({
        queryKey: ['channel', platformCode, channelId],
        queryFn: () => getChannelDetail(channelId!, platformCode),
        enabled: !!channelId,
    });

    // 2. [Query] VOD 리스트 조회 (필터링 적용)
    const { data: vodData, isLoading: isVodLoading, isFetching: isVodFetching } = useQuery({
        queryKey: ['channelVods', channelId, page, query, fromDate, toDate],
        queryFn: () => getVods({
            platform: platformId!.toUpperCase(),
            channelId: channelId, // ✅ 채널 ID 전달
            page,
            query,
            from: fromDate,
            to: toDate
        }),
        enabled: !!channelId,
        placeholderData: keepPreviousData,
    });

    const channel = channelData?.data;
    const vods = vodData?.data || [];
    const totalCount = vodData?.meta.total || 0;
    const totalPages = vodData?.meta.totalPages || 0;

    // 예외 처리
    if (isChannelError || (!isChannelLoading && !channel)) {
        return <div className="container py-20 text-center">존재하지 않는 채널입니다.</div>;
    }

    if (isChannelError || (!isChannelLoading && !channel)) {
        return <div className="container py-32 text-center text-muted-foreground">존재하지 않는 채널이거나 삭제되었습니다.</div>;
    }

    return (
        <div className="container mx-auto">
            {/* ✅ 3단 레이아웃 적용 */}
            <div className="flex justify-center gap-6">

                {/* [좌측 광고] */}
                <aside className="hidden 2xl:block w-[160px] shrink-0">
                    <div className="sticky top-24 w-full h-[600px] bg-muted/30 border border-dashed border-muted-foreground/20 rounded-lg flex items-center justify-center text-xs text-muted-foreground">
                        Advertisement(Left)
                    </div>
                </aside>

                {/* [메인 콘텐츠] */}
                <main className="flex-1 w-full max-w-5xl space-y-8">

                    {/* 1. 채널 프로필 */}
                    {isChannelLoading ? (
                        <ChannelProfileSkeleton />
                    ) : (
                        channel && <ChannelProfile channel={channel} />
                    )}

                    {/* 2. VOD 리스트 영역 */}
                    <div className="space-y-6">
                        <div className="flex flex-col gap-4">
                            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                                <div>
                                    <h2 className="text-xl font-bold flex items-center gap-2">
                                        영상 아카이브
                                        <span className="text-sm font-normal text-muted-foreground ml-1 bg-secondary px-2 py-0.5 rounded-full">
                                            {totalCount.toLocaleString()}
                                        </span>
                                    </h2>
                                </div>
                            </div>

                            {/* 툴바: 상단 배치 */}
                            <VodListToolbar placeholder="이 채널의 영상 검색..." />
                        </div>

                        {/* 리스트 (로딩/데이터/없음 분기) */}
                        {isVodLoading ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                                {Array.from({ length: 8 }).map((_, i) => (
                                    <VodCardSkeleton key={i} />
                                ))}
                            </div>
                        ) : vods.length > 0 ? (
                            <div className="relative">
                                <div className={cn(
                                    "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 transition-opacity duration-200",
                                    isVodFetching ? "opacity-50 pointer-events-none" : "opacity-100"
                                )}>
                                    {vods.map((item) => (
                                        <VodCard key={item.videoNo} data={item} />
                                    ))}
                                </div>

                                {totalPages > 1 && (
                                    <div className="flex justify-center pt-8">
                                        <BasePagination
                                            total={totalPages}
                                            page={page}
                                            onChange={(p) => setParams({ page: p })}
                                        />
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="py-24 text-center border-2 border-dashed rounded-xl bg-muted/10 text-muted-foreground">
                                <p>해당 조건의 영상이 없습니다.</p>
                            </div>
                        )}
                    </div>
                </main>

                {/* [우측 광고] */}
                <aside className="hidden 2xl:block w-[160px] shrink-0">
                    <div className="sticky top-24 w-full h-[600px] bg-muted/30 border border-dashed border-muted-foreground/20 rounded-lg flex items-center justify-center text-xs text-muted-foreground">
                        Advertisement(Right)
                    </div>
                </aside>
            </div>
        </div>
    );
}
