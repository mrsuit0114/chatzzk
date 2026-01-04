import React, { useMemo, useState } from "react";
import { MomentsToolbar } from "./MomentsToolbar";
import { MomentCard } from "./MomentCard";
import { SORT_OPTIONS, type SegmentSummaryData, type SortOption } from "../types";
import { SegmentSummarySheet } from "./SegmentSummarySheet";

function HorizontalScrollContainer({ children }: { children: React.ReactNode }) {
    return (
        // overflow-x-auto: 가로 스크롤 허용
        // pb-4: 스크롤바와 카드 사이의 여백 및 그림자 잘림 방지
        // snap-x: 스크롤 시 카드가 딱딱 맞춰서 멈추도록 (Carousel 느낌)
        <div className="flex overflow-x-auto pb-4 gap-4 snap-x snap-mandatory scrollbar-hide md:scrollbar-default">
            {children}
        </div>
    );
}
interface BestMomentsSectionProps {
    data: SegmentSummaryData[];
}

export function BestMomentsSection({ data }: BestMomentsSectionProps) {
    // 1. 상태 관리
    const [topN, setTopN] = useState(6);
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
        return result.slice(0, topN);
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
                <HorizontalScrollContainer>
                    {processedData.map((item) => (
                        <div key={item.id} className="snap-start">
                            <MomentCard
                                data={item}
                                interval={item.endTime - item.startTime}
                                sortBy={currentSort}
                                onClick={() => handleCardClick(item)}
                            />
                        </div>
                    ))}
                    {/* 우측 끝 여백 확보용 더미 요소 (선택사항) */}
                    <div className="w-1 shrink-0" />
                </HorizontalScrollContainer>
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
