import { useParams } from "react-router-dom";
import { VodCard } from "@/features/vod/components/VodCard";
import { MOCK_VOD_DATA } from "@/features/vod/api/mock";
import { useUrlParams } from "@/hooks/use-url-params";
import { BasePagination } from "@/components/ui/base-pagination";
import { VodListToolbar } from "@/features/vod/components/VodListToolbar";
import { PLATFORM_LABELS } from "@/constants";
import { ITEMS_PER_PAGE } from "../constants";


export function PlatformPage() {
    const { platformId } = useParams<{ platformId: string }>();
    // sort 제거됨, page 추가
    const { query, fromDate, toDate, page, setParams } = useUrlParams();

    // --- [Mocking Logic] ---
    const filteredItems = MOCK_VOD_DATA.filter((item) => {
        // 1. 플랫폼 체크
        const isPlatformMatch = item.platform.toLowerCase() === platformId?.toLowerCase();

        // 2. 검색어 체크
        const isQueryMatch = !query ||
            item.title.toLowerCase().includes(query.toLowerCase()) ||
            item.channelName.toLowerCase().includes(query.toLowerCase());

        // 3. 날짜 체크
        const isAfterFrom = !fromDate || item.publishDate >= fromDate;
        const isBeforeTo = !toDate || item.publishDate <= toDate;

        return isPlatformMatch && isQueryMatch && isAfterFrom && isBeforeTo;
    });

    // 4. 정렬 (최신순 고정)
    const sortedItems = [...filteredItems].sort((a, b) => {
        return b.publishDate.localeCompare(a.publishDate);
    });

    // --- [페이지네이션 계산] ---
    const totalCount = sortedItems.length;
    const totalPages = Math.ceil(totalCount / ITEMS_PER_PAGE);

    // 현재 페이지가 전체 페이지보다 크다면 1페이지로 보정 (예: 필터링으로 개수가 줄었을 때)
    const safePage = page > totalPages && totalPages > 0 ? 1 : page;

    const startIndex = (safePage - 1) * ITEMS_PER_PAGE;
    const currentPageItems = sortedItems.slice(startIndex, startIndex + ITEMS_PER_PAGE);

    // --- [렌더링] ---
    if (!platformId || !PLATFORM_LABELS[platformId.toLowerCase()]) {
        return <div className="container py-20 text-center">존재하지 않는 플랫폼입니다.</div>;
    }

    const platformName = PLATFORM_LABELS[platformId.toLowerCase()];

    return (
        <div className="container mx-auto py-8 space-y-6">
            {/* 타이틀 */}
            <div>
                <h1 className="text-3xl font-bold">{platformName} 분석 아카이브</h1>
                <p className="text-muted-foreground mt-2">
                    총 <span className="font-bold text-foreground">{totalCount}</span>개의 영상이 검색되었습니다.
                </p>
            </div>

            {/* 제어 툴바 */}
            <VodListToolbar placeholder="제목 또는 채널명 검색" />

            {/* VOD 리스트 Grid */}
            {currentPageItems.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {currentPageItems.map((item) => (
                        <VodCard key={item.videoNo} data={item} />
                    ))}
                </div>
            ) : (
                <div className="py-20 text-center border rounded-lg bg-secondary/10 text-muted-foreground">
                    조건에 맞는 영상이 없습니다.
                </div>
            )}

            {/* ✅ Shadcn 페이지네이션 적용 */}
            {totalPages > 1 && (
                <BasePagination
                    total={totalPages}
                    page={safePage}
                    onChange={(newPage) => setParams({ page: newPage })}
                />
            )}
        </div>
    );
}
