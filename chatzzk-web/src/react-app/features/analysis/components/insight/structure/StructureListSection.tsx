import { useEffect, useState, useMemo } from "react";
import { Accordion } from "@/components/ui/accordion";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChapterItem } from "./ChapterItem";
import { SegmentDetailCard } from "../../common/SegmentDetailCard";
import { cn } from "@/lib/utils";
import { useStructureScroll } from "@/features/analysis/hooks/use-structure-scroll";
import { ChapterSummaryData, SegmentSummaryData } from "@/features/analysis/types";

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

        // 1. 맵 초기화
        chapters.forEach(ch => map.set(ch.id, []));

        // 2. 세그먼트 분류 (O(N))
        // data가 시간순 정렬되어 있고, chapters도 시간순이라 가정하면 더 최적화 가능하지만
        // 현재 로직(시간 비교)으로도 충분히 빠릅니다.
        data.forEach(seg => {
            // 해당 세그먼트가 속할 챕터를 찾습니다.
            // (대부분의 경우 segment 데이터에 chapterId가 있다면 그걸 쓰는 게 가장 빠릅니다)
            // 현재는 시간 기준으로 매칭합니다.
            const targetChapter = chapters.find(
                ch => seg.startTime >= ch.startTime && seg.endTime <= ch.endTime
            );

            if (targetChapter) {
                const list = map.get(targetChapter.id);
                if (list) list.push(seg);
            }
        });

        return map;
    }, [chapters, data]);

    // 1. [동기화] 외부 타임스탬프 변경 감지
    useEffect(() => {
        if (focusedTimestamp === null) return;

        const activeChapter = chapters.find(
            ch => focusedTimestamp >= ch.startTime && focusedTimestamp < ch.endTime
        );

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
            <div className="p-4">
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
                                                isSegmentActive
                                                    ? "border-primary/60 bg-primary/5 ring-1 ring-primary/20"
                                                    : "border-transparent hover:bg-muted/50"
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
