import { useParams } from "react-router-dom";
import { VodCard } from "@/features/vod/components/VodCard";
import { ChannelProfile } from "../components/ChannelProfile";
import { VodListToolbar } from "@/features/vod/components/VodListToolbar";
import { BasePagination } from "@/components/ui/base-pagination"; // 파일명 수정 반영
import { useUrlParams } from "@/hooks/use-url-params";
import { getVods } from "@/features/vod/api/getVods";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { getChannelDetail } from "../api/getChannelDetail";


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
    const { data: vodData, isLoading: isVodLoading } = useQuery({
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

    return (
        <div className="container mx-auto py-8 space-y-8">
            {/* 1. 채널 프로필 */}
            {isChannelLoading ? (
                <div className="h-48 bg-muted animate-pulse rounded-lg" />
            ) : (
                channel && <ChannelProfile channel={channel} />
            )}

            {/* 2. VOD 리스트 */}
            <div className="space-y-6">
                <div className="flex flex-col md:flex-row justify-between items-end gap-4">
                    <div>
                        <h2 className="text-xl font-bold">영상 아카이브</h2>
                        <p className="text-sm text-muted-foreground">
                            총 {totalCount}개의 분석 영상
                        </p>
                    </div>
                    <div className="w-full md:w-auto">
                        <VodListToolbar placeholder="영상 제목 검색" />
                    </div>
                </div>

                {isVodLoading ? (
                    <div className="py-20 text-center">로딩 중...</div>
                ) : vods.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {vods.map((item) => (
                            <VodCard key={item.videoNo} data={item} />
                        ))}
                    </div>
                ) : (
                    <div className="py-20 text-center border rounded-lg bg-secondary/10 text-muted-foreground">
                        해당 조건의 영상이 없습니다.
                    </div>
                )}

                {totalPages > 1 && (
                    <BasePagination
                        total={totalPages}
                        page={page}
                        onChange={(p) => setParams({ page: p })}
                    />
                )}
            </div>
        </div>
    );
}
