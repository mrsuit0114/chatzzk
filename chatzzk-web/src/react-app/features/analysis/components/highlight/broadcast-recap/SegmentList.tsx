import { SegmentSummaryData } from "@/features/analysis/types";
import { SegmentDetailCard } from "../../common/SegmentDetailCard";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ArrowUp } from "lucide-react";
import { useRef, useState } from "react";

interface SegmentListProps {
    segments: SegmentSummaryData[];
}

export function SegmentList({ segments }: SegmentListProps) {
    // 1. 스크롤 컨테이너를 제어하기 위한 Ref
    const scrollRef = useRef<HTMLDivElement>(null);

    // 2. 버튼 표시 여부 상태
    const [showScrollTop, setShowScrollTop] = useState(false);

    // 3. 스크롤 이벤트 핸들러: 스크롤 위치 감지
    const handleScroll = () => {
        if (scrollRef.current) {
            // 300px 이상 내려가면 버튼 표시
            const { scrollTop } = scrollRef.current;
            setShowScrollTop(scrollTop > 300);
        }
    };

    // 4. 맨 위로 스크롤하는 함수
    const scrollToTop = () => {
        if (scrollRef.current) {
            scrollRef.current.scrollTo({
                top: 0,
            });
        }
    };

    return (
        // ✅ [중요] relative 추가: 내부 absolute 버튼의 기준점이 됨
        <div className="flex flex-col h-full relative group/list">

            {/* Header */}
            <div className="flex items-center justify-between pb-4 border-b shrink-0 bg-background z-10">
                <h3 className="text-lg font-bold">세그먼트</h3>
                <span className="text-xs text-muted-foreground font-medium">
                    Total {segments.length} items
                </span>
            </div>

            {/* Scrollable Content Area */}
            {/* ✅ Ref 연결 및 onScroll 이벤트 추가 */}
            <div
                ref={scrollRef}
                onScroll={handleScroll}
                className="flex-1 overflow-y-auto py-4 pr-2 space-y-4 min-h-0 custom-scrollbar pb-12"
            >
                {segments.length > 0 ? (
                    segments.map((segment) => (
                        <SegmentDetailCard key={segment.id} data={segment} />
                    ))
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-muted-foreground text-sm border-2 border-dashed rounded-lg">
                        <p>해당 챕터에 포함된 세그먼트가 없습니다.</p>
                    </div>
                )}
            </div>

            {/* ✅ Scroll To Top Button */}
            <Button
                size="icon"
                variant="secondary"
                onClick={scrollToTop}
                className={cn(
                    "absolute bottom-6 right-6 z-50 rounded-full shadow-lg border transition-all duration-300",
                    "hover:bg-primary hover:text-white",
                    // 스크롤이 내려갔을 때만 보이도록 처리 (opacity & translate)
                    showScrollTop
                        ? "opacity-100 translate-y-0"
                        : "opacity-0 translate-y-4 pointer-events-none"
                )}
                aria-label="맨 위로 스크롤"
            >
                <ArrowUp className="h-5 w-5" />
            </Button>
        </div>
    );
}
