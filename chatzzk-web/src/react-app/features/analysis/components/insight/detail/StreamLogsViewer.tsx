import { useEffect, useRef } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { StreamLogItem } from "./StreamLogItem";
import { Loader2 } from "lucide-react";
import { useStreamLogs } from "@/features/analysis/hooks/use-stream-logs";
import { findLogIndex } from "@/features/analysis/utils";

interface StreamLogsViewerProps {
    chapterIndex: number;
    focusedTimestamp: number | null;
}

export function StreamLogsViewer({ chapterIndex, focusedTimestamp }: StreamLogsViewerProps) {
    const { logs, isLoading, error } = useStreamLogs(chapterIndex);
    const parentRef = useRef<HTMLDivElement>(null);

    // 1. 가상 스크롤 설정
    const rowVirtualizer = useVirtualizer({
        // ✅ [안전장치] 로딩 중일 때는 아이템 개수를 0으로 처리하여 계산 방지
        count: isLoading ? 0 : logs.length,
        getScrollElement: () => parentRef.current,
        estimateSize: () => 80,
        overscan: 5,
    });

    // 2. 자동 스크롤 동기화
    useEffect(() => {
        // 로딩 중이거나, DOM이 없으면 중단
        if (isLoading || !parentRef.current || logs.length === 0) return;
        if (focusedTimestamp === null || Number.isNaN(focusedTimestamp)) return;

        const targetIndex = findLogIndex(logs, focusedTimestamp);

        if (targetIndex !== -1 && !Number.isNaN(targetIndex) && targetIndex < logs.length) {
            // ✅ [Fix] setTimeout을 사용하여 Virtualizer가 업데이트된 후 실행되도록 지연
            const timer = setTimeout(() => {
                // 안전장치: 마운트 된 상태에서만 실행 (optional chaining)
                rowVirtualizer?.scrollToIndex(targetIndex, { align: 'start', behavior: 'auto' });
            }, 0);

            return () => clearTimeout(timer);
        }
    }, [focusedTimestamp, logs, isLoading, rowVirtualizer]);

    // 3. 렌더링 (Early Return 제거 및 구조 변경)
    return (
        // ✅ [Fix] 스크롤 컨테이너(parentRef)는 항상 렌더링되어야 합니다.
        <div
            ref={parentRef}
            className="h-full w-full overflow-y-auto bg-slate-50/50 relative"
        >
            {/* 내부 컨텐츠 분기 처리 */}
            {isLoading ? (
                <div className="flex h-full items-center justify-center text-muted-foreground absolute inset-0">
                    <Loader2 className="h-6 w-6 animate-spin mr-2" />
                    Loading logs...
                </div>
            ) : error ? (
                <div className="flex h-full items-center justify-center text-destructive text-sm absolute inset-0">
                    Failed to load stream logs.
                </div>
            ) : logs.length === 0 ? (
                <div className="flex h-full items-center justify-center text-muted-foreground text-sm absolute inset-0">
                    No logs available for this chapter.
                </div>
            ) : (
                // 실제 로그 리스트
                <div
                    style={{
                        height: `${rowVirtualizer.getTotalSize()}px`,
                        width: '100%',
                        position: 'relative',
                    }}
                >
                    {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                        const log = logs[virtualRow.index];
                        return (
                            <StreamLogItem
                                key={virtualRow.index}
                                log={log}
                                index={virtualRow.index}
                                measureRef={rowVirtualizer.measureElement}
                                style={{
                                    position: 'absolute',
                                    top: 0,
                                    left: 0,
                                    width: '100%',
                                    transform: `translateY(${virtualRow.start}px)`,
                                }}
                            />
                        );
                    })}
                </div>
            )}
        </div>
    );
}
