import { useParams } from "react-router-dom";
import { VodCard } from "@/features/vod/components/VodCard";
import { MOCK_VOD_DATA } from "@/features/vod/api/mock";
import { MOCK_CHANNEL_DATA } from "@/features/channel/api/mock";
import { ChannelProfile } from "../components/ChannelProfile";
import { VodListToolbar } from "@/features/vod/components/VodListToolbar";
import { BasePagination } from "@/components/ui/base-pagination"; // 파일명 수정 반영
import { useUrlParams } from "@/lib/hooks";

const ITEMS_PER_PAGE = 12;

export function ChannelPage() {
    const { channelId } = useParams<{ channelId: string }>();
    const { query, fromDate, toDate, page, setParams } = useUrlParams();

    // 1. 채널 정보 찾기 (Mock Data에서 ID로 조회)
    const channel = MOCK_CHANNEL_DATA.find((c) => c.id === Number(channelId));

    // 2. VOD 필터링 로직
    const filteredItems = MOCK_VOD_DATA.filter((item) => {
        // A. [필수] 현재 채널의 영상인가?
        // (Mock Data의 channelId는 number, URL param은 string이므로 형변환 주의)
        const isChannelMatch = String(item.channelId) === channelId;

        // B. 검색어 (채널 내에서는 '제목'만 검색하면 됨)
        const isQueryMatch = !query || item.title.toLowerCase().includes(query.toLowerCase());

        // C. 날짜 범위
        const isAfterFrom = !fromDate || item.publishDate >= fromDate;
        const isBeforeTo = !toDate || item.publishDate <= toDate;

        return isChannelMatch && isQueryMatch && isAfterFrom && isBeforeTo;
    });

    // 3. 정렬 (최신순)
    const sortedItems = [...filteredItems].sort((a, b) =>
        b.publishDate.localeCompare(a.publishDate)
    );

    // 4. 페이지네이션 계산
    const totalCount = sortedItems.length;
    const totalPages = Math.ceil(totalCount / ITEMS_PER_PAGE);
    const safePage = page > totalPages && totalPages > 0 ? 1 : page;

    const startIndex = (safePage - 1) * ITEMS_PER_PAGE;
    const currentPageItems = sortedItems.slice(startIndex, startIndex + ITEMS_PER_PAGE);

    // 예외 처리: 채널이 없는 경우
    if (!channel) {
        return <div className="container py-20 text-center">존재하지 않는 채널입니다.</div>;
    }

    return (
        <div className="container mx-auto py-8 space-y-8">
            {/* 1. 채널 프로필 영역 */}
            <ChannelProfile channel={channel} />

            {/* 2. VOD 리스트 영역 */}
            <div className="space-y-6">
                <div className="flex flex-col md:flex-row justify-between items-end gap-4">
                    <div>
                        <h2 className="text-xl font-bold">영상 아카이브</h2>
                        <p className="text-sm text-muted-foreground">
                            총 {totalCount}개의 분석 영상
                        </p>
                    </div>
                    {/* 재사용된 툴바 (플레이스홀더 변경) */}
                    <div className="w-full md:w-auto">
                        <VodListToolbar placeholder="영상 제목 검색" />
                    </div>
                </div>

                {/* 리스트 그리드 */}
                {currentPageItems.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {currentPageItems.map((item) => (
                            <VodCard key={item.vodId} data={item} />
                        ))}
                    </div>
                ) : (
                    <div className="py-20 text-center border rounded-lg bg-secondary/10 text-muted-foreground">
                        해당 조건의 영상이 없습니다.
                    </div>
                )}

                {/* 페이지네이션 */}
                {totalPages > 1 && (
                    <BasePagination
                        total={totalPages}
                        page={safePage}
                        onChange={(p) => setParams({ page: p })}
                    />
                )}
            </div>
        </div>
    );
}
