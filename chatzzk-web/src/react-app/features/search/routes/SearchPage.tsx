import { useSearchParams } from "react-router-dom";
import { Search } from "lucide-react";

// 컴포넌트 & 데이터
import { ChannelCard } from "@/features/channel/components/ChannelCard";
import { BasePagination } from "@/components/ui/base-pagination";
import { MOCK_CHANNEL_DATA } from "@/features/channel/api/mock";
import { PLATFORM_LABELS } from "@/constants";


const ITEMS_PER_PAGE = 18; // 한 페이지당 보여줄 채널 수

export function SearchPage() {
    const [searchParams, setSearchParams] = useSearchParams();

    // 1. URL 파라미터 읽기
    const query = searchParams.get("q") || "";
    const platform = searchParams.get("platform") || "all";

    // 페이지 번호는 URL에서 가져오며, 없으면 1페이지로 설정
    const currentPage = parseInt(searchParams.get("page") || "1", 10);

    // [검색 로직]
    // 1) 플랫폼 필터링
    // 2) 검색어 필터링 (채널명 OR 플랫폼 채널 ID)
    const filteredChannels = MOCK_CHANNEL_DATA.filter((channel) => {
        // A. 플랫폼 체크
        if (platform !== "all" && channel.platform !== platform) {
            return false;
        }

        // B. 검색어 체크 (이름 또는 플랫폼 ID 포함 여부)
        const lowerQuery = query.toLowerCase();
        const matchName = channel.name.toLowerCase().includes(lowerQuery);
        // channelId가 있는 경우(mock 데이터 구조 가정) 함께 검색
        const matchId = channel.channelId
            ? channel.channelId.toLowerCase() === lowerQuery
            : false;

        return matchName || matchId;
    });

    // [페이지네이션 계산]
    const totalCount = filteredChannels.length;
    const totalPages = Math.ceil(totalCount / ITEMS_PER_PAGE);

    // 현재 페이지가 전체 페이지보다 크다면 조정 (검색어 변경 등으로 인한 범위 초과 방지)
    const safePage = (totalPages > 0 && currentPage > totalPages) ? totalPages : currentPage;

    const startIndex = (safePage - 1) * ITEMS_PER_PAGE;
    const currentItems = filteredChannels.slice(startIndex, startIndex + ITEMS_PER_PAGE);

    // 검색 조건이 바뀔 때 페이지를 1로 리셋하는 로직은
    // 검색바(VodListToolbar 등)에서 검색 시 page=1로 넘겨주는 것이 정석이나,
    // 여기서 방어적으로 처리할 수도 있습니다. (현재는 URL 제어권을 검색바가 가졌다고 가정)

    const handlePageChange = (newPage: number) => {
        // 기존 쿼리 파라미터(q, platform)는 유지하고 page만 변경
        setSearchParams({
            q: query,
            platform,
            page: newPage.toString()
        });
        // 페이지 이동 시 상단 스크롤
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
                        플랫폼: <span className="font-medium text-foreground">{platform === "all" ? "전체" : PLATFORM_LABELS[platform]}</span>
                    </span>
                    <span className="w-px h-3 bg-border" />
                    <span>
                        검색된 채널: <span className="font-medium text-foreground">{totalCount}개</span>
                    </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                    * 채널 이름 및 채널 ID(식별자)를 기준으로 검색합니다.
                </p>
            </div>

            {/* 검색 결과 영역 */}
            <section className="space-y-8">
                {currentItems.length > 0 ? (
                    <>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {currentItems.map((channel) => (
                                <ChannelCard key={`${channel.platform}-${channel.channelId}`} data={channel} />
                            ))}
                        </div>

                        {/* 페이지네이션 (페이지가 1개 이상일 때만 표시) */}
                        {totalPages > 1 && (
                            <div className="flex justify-center pt-4">
                                <BasePagination
                                    total={totalPages}
                                    page={safePage}
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
