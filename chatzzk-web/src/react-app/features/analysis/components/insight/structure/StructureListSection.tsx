import { useEffect, useState, useMemo } from "react";
import { Accordion } from "@/components/ui/accordion";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChapterItem } from "./ChapterItem";
import { SegmentDetailCard } from "../../common/SegmentDetailCard";
import { cn } from "@/lib/utils";
import { useStructureScroll } from "@/features/analysis/hooks/use-structure-scroll";
import { ChapterSummaryData, SegmentSummaryData } from "@/features/analysis/types";
import { findSegmentIndexBinary } from "@/features/analysis/utils/chart-helper";

interface StructureListSectionProps {
    chapters: ChapterSummaryData[];
    data: SegmentSummaryData[];
    focusedTimestamp: number | null;
    onSeek: (timestamp: number) => void;
}

export function StructureListSection({
    chapters,
    data,
    focusedTimestamp,
    onSeek,
}: StructureListSectionProps) {
    // 제어된 아코디언 상태
    const [openItemId, setOpenItemId] = useState<string>("");

    const {
        scrollAreaRef,
        segmentRefs,
        chapterRefs,
        scrollToSegment,
        scrollToTarget
    } = useStructureScroll(data);


    // ✅ [성능 개선] 챕터별 세그먼트 그룹화 (Memoization)
    // 렌더링마다 filter를 돌리지 않고, 데이터가 변경될 때만 한 번 계산합니다.
    const segmentsByChapter = useMemo(() => {
        const map = new Map<string, SegmentSummaryData[]>();

        // 1. 맵 초기화 (챕터 순서 보장 및 빈 배열 생성)
        chapters.forEach(ch => map.set(ch.id, []));

        // 2. 세그먼트 분류 (chapterId 이용)
        data.forEach(seg => {
            // 시간 비교 로직 제거 -> ID로 바로 조회
            const list = map.get(seg.chapterId);

            // 데이터 무결성을 위해 list가 존재할 때만 push
            if (list) {
                list.push(seg);
            }
        });

        return map;
    }, [chapters, data]);

    // 1. [동기화] 외부 타임스탬프 변경 감지
    useEffect(() => {
        if (focusedTimestamp === null) return;

        const activeIndex = findSegmentIndexBinary(chapters, focusedTimestamp);
        const activeChapter = activeIndex !== -1 ? chapters[activeIndex] : null;

        if (activeChapter) {
            if (activeChapter.id !== openItemId) {
                setOpenItemId(activeChapter.id);
                setTimeout(() => {
                    scrollToSegment(focusedTimestamp, 'nearest');
                }, 300);
            } else {
                // ✅ [수정됨] 즉시 이동 시에도 커스텀 함수 사용
                scrollToSegment(focusedTimestamp, 'nearest');
            }
        }
    }, [focusedTimestamp, chapters, data]); // openItemId 의존성 제외 (무한루프 방지)


    // 2. [사용자 상호작용] 아코디언 헤더 클릭 핸들러
    const handleAccordionChange = (value: string) => {
        setOpenItemId(value);

        if (value) {
            const chapterElement = chapterRefs.current.get(value);
            if (chapterElement) {
                setTimeout(() => {
                    scrollToTarget(chapterElement, 'start');
                }, 300);
            }
        }
    };

    return (
        <ScrollArea className="flex flex-col h-full border bg-card shadow-sm overflow-hidden" ref={scrollAreaRef}>
            <div className="p-2">
                <Accordion
                    type="single"
                    collapsible
                    value={openItemId}
                    onValueChange={handleAccordionChange}
                    className="space-y-2"
                >
                    {chapters.map((chapter) => {
                        // ✅ [성능 개선] 미리 계산된 맵에서 가져오기 (O(1))
                        const chapterSegments = segmentsByChapter.get(chapter.id) || [];

                        const isChapterActive = focusedTimestamp !== null &&
                            focusedTimestamp >= chapter.startTime &&
                            focusedTimestamp < chapter.endTime;

                        return (
                            <ChapterItem
                                key={chapter.id}
                                chapter={chapter}
                                isActive={isChapterActive}
                                rootRef={(el) => {
                                    if (el) chapterRefs.current.set(chapter.id, el);
                                    else chapterRefs.current.delete(chapter.id);
                                }}
                            >
                                {chapterSegments.map((seg) => {
                                    const isSegmentActive = focusedTimestamp !== null &&
                                        focusedTimestamp >= seg.startTime &&
                                        focusedTimestamp < seg.endTime;

                                    return (
                                        <div
                                            key={seg.id}
                                            ref={(el) => {
                                                if (el) segmentRefs.current.set(seg.id, el);
                                                else segmentRefs.current.delete(seg.id);
                                            }}
                                            onClick={() => onSeek(seg.startTime)}
                                            className={cn(
                                                "cursor-pointer transition-all duration-200 rounded-lg border-2 mb-2 last:mb-0",
                                                // ✅ [수정] 호버 효과 강화 그룹
                                                "hover:border-primary/45 hover:bg-muted hover:shadow-sm",

                                                // 활성/비활성 상태 스타일
                                                isSegmentActive
                                                    ? "border-primary/60 bg-primary/5 shadow-sm"
                                                    : "border-transparent" // 평소에는 투명 테두리 (레이아웃 밀림 방지)
                                            )}
                                        >
                                            <SegmentDetailCard data={seg} />
                                        </div>
                                    );
                                })}
                            </ChapterItem>
                        );
                    })}
                </Accordion>
            </div>
        </ScrollArea>
    );
}
