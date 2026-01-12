import { useSearchParams } from "react-router-dom";
import { Search } from "lucide-react";

// 컴포넌트 & 데이터
import { ChannelCard } from "@/features/channel/components/ChannelCard";
import { BasePagination } from "@/components/ui/base-pagination";
import { PLATFORM_LABELS } from "@/constants";
import { getChannels } from "@/features/channel/api/getChannels";
import { useQuery, keepPreviousData } from "@tanstack/react-query";

export function SearchPage() {
    const [searchParams, setSearchParams] = useSearchParams();

    // 1. URL 파라미터 읽기
    const query = searchParams.get("q") || "";
    const platform = searchParams.get("platform") || "all";
    const page = parseInt(searchParams.get("page") || "1", 10);

    // 2. [React Query] 데이터 fetching
    const { data, isLoading, isError } = useQuery({
        queryKey: ['channels', platform, query, page],
        queryFn: () => getChannels({ platform, query, page }),
        enabled: !!query, // 검색어가 있을 때만 실행 (선택 사항, 없으면 전체 목록 보여줄지 결정)
        placeholderData: keepPreviousData,
        staleTime: 1000 * 60 * 5,
    });

    // 데이터 추출
    const channels = data?.data || [];
    const totalCount = data?.meta.total || 0;
    const totalPages = data?.meta.totalPages || 0;

    const handlePageChange = (newPage: number) => {
        setSearchParams({
            q: query,
            platform,
            page: newPage.toString()
        });
        window.scrollTo({ top: 0, behavior: "smooth" });
    };

    // 검색어가 없을 때
    if (!query) {
        return (
            <div className="container mx-auto py-20 flex flex-col items-center justify-center text-muted-foreground space-y-4">
                <Search className="h-12 w-12 opacity-20" />
                <p>검색어를 입력하여 채널을 찾아보세요.</p>
            </div>
        );
    }

    return (
        <div className="container mx-auto py-8 space-y-8">
            {/* 페이지 헤더 */}
            <div className="flex flex-col gap-2 border-b pb-6">
                <h1 className="text-2xl font-bold flex items-center gap-2">
                    "<span className="text-primary">{query}</span>" 검색 결과
                </h1>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>
                        플랫폼: <span className="font-medium text-foreground">
                            {platform === "all" ? "전체" : PLATFORM_LABELS[platform.toUpperCase()]}
                        </span>
                    </span>
                    <span className="w-px h-3 bg-border" />
                    <span>
                        검색된 채널: <span className="font-medium text-foreground">{totalCount}개</span>
                    </span>
                </div>
            </div>

            {/* 검색 결과 영역 */}
            <section className="space-y-8">
                {isLoading ? (
                    <div className="py-20 text-center">로딩 중...</div>
                ) : isError ? (
                    <div className="py-20 text-center text-red-500">채널 정보를 불러오는 중 오류가 발생했습니다.</div>
                ) : channels.length > 0 ? (
                    <>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {channels.map((channel) => (
                                <ChannelCard key={`${channel.platform}-${channel.channelId}`} data={channel} />
                            ))}
                        </div>

                        {totalPages > 1 && (
                            <div className="flex justify-center pt-4">
                                <BasePagination
                                    total={totalPages}
                                    page={page}
                                    onChange={handlePageChange}
                                />
                            </div>
                        )}
                    </>
                ) : (
                    <div className="py-20 flex flex-col items-center justify-center text-center space-y-3 bg-secondary/5 rounded-lg border border-dashed">
                        <div className="p-3 bg-background rounded-full shadow-sm">
                            <Search className="h-6 w-6 text-muted-foreground" />
                        </div>
                        <div className="space-y-1">
                            <p className="text-lg font-medium text-foreground">검색 결과가 없습니다.</p>
                            <p className="text-sm text-muted-foreground">
                                다른 키워드나 채널 ID로 검색해 보시거나,<br />
                                플랫폼 필터를 변경해 보세요.
                            </p>
                        </div>
                    </div>
                )}
            </section>
        </div>
    );
}
