import { useMemo, useState } from "react";
import { MomentsToolbar } from "./MomentsToolbar";
import { MomentCard } from "./MomentCard";
import { SegmentSummarySheet } from "./SegmentSummarySheet";
import { SORT_OPTIONS, SortOption } from "@/features/analysis/constants";
import { SegmentSummaryData } from "@/features/analysis/types";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";

interface BestMomentsSectionProps {
    data: SegmentSummaryData[];
}

export function BestMomentsSection({ data }: BestMomentsSectionProps) {
    // 1. 상태 관리
    const [topN, setTopN] = useState(5);
    const [currentSort, setCurrentSort] = useState<SortOption>(SORT_OPTIONS.VOLUME);
    // 초기에는 모든 분위기 선택 (빈 배열([])은 '모두 선택'으로 간주하거나, 아래 useEffect로 초기화 가능)
    // 여기서는 로직 단순화를 위해 '초기값 = 전체 목록' 전략을 사용
    const [selectedSegment, setSelectedSegment] = useState<SegmentSummaryData | null>(null);

    const handleCardClick = (item: SegmentSummaryData) => {
        setSelectedSegment(item);
    };

    // ✅ 3. 시트 닫기 핸들러
    const handleCloseSheet = () => {
        setSelectedSegment(null);
    };
    // 2. 전체 Atmosphere 목록 추출 (데이터 기반)
    const availableAtmospheres = useMemo(() => {
        const unique = new Set(data.map(item => item.atmosphere));
        return Array.from(unique).sort();
    }, [data]);

    const [selectedAtmospheres, setSelectedAtmospheres] = useState<string[]>(availableAtmospheres);

    // 3. 데이터 필터링 & 정렬 로직 (Core Logic)
    const processedData = useMemo(() => {
        let result = [...data];

        // A. Filter by Atmosphere
        if (selectedAtmospheres.length > 0) {
            result = result.filter(item => selectedAtmospheres.includes(item.atmosphere));
        } else {
            // 선택된 게 없으면 아무것도 안 보여줌? 아니면 전체?
            // 보통 UI상 '모두 해제'면 아무것도 안 나오는 게 맞음.
            result = [];
        }

        // B. Sort
        result.sort((a, b) => {
            if (currentSort === SORT_OPTIONS.VOLUME) return b.volPeak.volume - a.volPeak.volume;
            if (currentSort === SORT_OPTIONS.MOMENTUM) return b.mmtPeak.momentum - a.mmtPeak.momentum;
            return b.score - a.score; // score
        });

        // C. Limit (Top N)
        if (topN > 0)
            return result.slice(0, topN);
        return result;
    }, [data, selectedAtmospheres, currentSort, topN]);

    return (
        <section className="space-y-4">
            {/* Toolbar */}
            <MomentsToolbar
                availableAtmospheres={availableAtmospheres}
                selectedAtmospheres={selectedAtmospheres}
                onAtmosphereChange={setSelectedAtmospheres}
                currentSort={currentSort}
                onSortChange={setCurrentSort}
                topN={topN}
                onTopNChange={setTopN}
            />

            {/* ✅ [수정] Horizontal Scroll View */}
            {processedData.length > 0 ? (
                <ScrollArea className="w-full rounded-md border">
                    {/* flex: 가로 배치
                        w-max: 자식 요소들의 너비만큼 늘어나도록 설정 (가로 스크롤 핵심)
                        space-x-4: 아이템 간 간격
                        p-4: 패딩
                    */}
                    <div className="flex w-max space-x-4 p-4">
                        {processedData.map((item) => (
                            // shrink-0: 공간이 부족해도 카드가 찌그러지지 않도록 설정
                            <div key={item.id} className="shrink-0">
                                <MomentCard
                                    data={item}
                                    interval={item.endTime - item.startTime}
                                    sortBy={currentSort}
                                    onClick={() => handleCardClick(item)}
                                />
                            </div>
                        ))}
                    </div>
                    {/* 가로 스크롤바 명시 */}
                    <ScrollBar orientation="horizontal" />
                </ScrollArea>
            ) : (
                <div className="py-20 text-center text-muted-foreground border-2 border-dashed rounded-xl bg-secondary/10">
                    조건에 맞는 하이라이트가 없습니다. 필터를 변경해보세요.
                </div>
            )}
            <SegmentSummarySheet
                data={selectedSegment}
                isOpen={!!selectedSegment} // 데이터가 있으면 true
                onClose={handleCloseSheet}
            />
        </section>
    );
}
