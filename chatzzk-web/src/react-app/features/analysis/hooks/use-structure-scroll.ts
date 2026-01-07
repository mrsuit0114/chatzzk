import { useRef } from "react";
import { SegmentSummaryData } from "../types";

export function useStructureScroll(data: SegmentSummaryData[]) {
    // 1. Refs 관리 (로직 이동)
    const scrollAreaRef = useRef<HTMLDivElement>(null);
    const segmentRefs = useRef<Map<string, HTMLDivElement>>(new Map());
    const chapterRefs = useRef<Map<string, HTMLDivElement>>(new Map());

    // 2. 스크롤 계산 로직 (로직 이동)
    const scrollToTarget = (element: HTMLElement, blockType: 'start' | 'nearest') => {
        const viewport = scrollAreaRef.current?.querySelector('[data-radix-scroll-area-viewport]') as HTMLElement;
        if (!viewport || !element) return;

        const viewportRect = viewport.getBoundingClientRect();
        const elementRect = element.getBoundingClientRect();
        const currentScrollTop = viewport.scrollTop;
        const relativeTop = elementRect.top - viewportRect.top;

        let targetScrollTop = currentScrollTop;

        if (blockType === 'start') {
            targetScrollTop = currentScrollTop + relativeTop;
        } else if (blockType === 'nearest') {
            const elementHeight = elementRect.height;
            const viewportHeight = viewportRect.height;

            if (relativeTop < 0) {
                targetScrollTop = currentScrollTop + relativeTop;
            } else if (relativeTop + elementHeight > viewportHeight) {
                targetScrollTop = currentScrollTop + relativeTop - (viewportHeight - elementHeight);
            }
        }
        viewport.scrollTo({ top: targetScrollTop, behavior: 'smooth' });
    };

    // 3. 헬퍼 함수 (로직 이동)
    const scrollToSegment = (timestampOrId: number | string, blockType: 'start' | 'nearest') => {
        let targetId: string | undefined;
        if (typeof timestampOrId === 'number') {
            const activeSegment = data.find(
                seg => timestampOrId >= seg.startTime && timestampOrId < seg.endTime
            );
            targetId = activeSegment?.id;
        } else {
            targetId = timestampOrId;
        }

        if (targetId) {
            const element = segmentRefs.current.get(targetId);
            if (element) scrollToTarget(element, blockType);
        }
    };

    // 4. UI에서 필요한 것들만 반환
    return {
        scrollAreaRef,
        segmentRefs,
        chapterRefs,
        scrollToTarget,
        scrollToSegment
    };
}
