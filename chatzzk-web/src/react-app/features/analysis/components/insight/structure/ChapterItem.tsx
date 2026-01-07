import { Clock } from "lucide-react";
import { AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { formatTime } from "@/features/analysis/utils";
import { cn } from "@/lib/utils";
import { ChapterSummaryData } from "@/features/analysis/types";

interface StructureChapterItemProps {
    chapter: ChapterSummaryData;
    isActive: boolean; // 현재 타임스탬프가 이 챕터에 포함되는지 여부 (스타일링용)
    children: React.ReactNode; // 내부에 들어갈 SegmentDetailCard 리스트
    rootRef?: (node: HTMLDivElement | null) => void;
}

export function ChapterItem({ chapter, isActive, children, rootRef }: StructureChapterItemProps) {
    return (
        <AccordionItem
            value={chapter.id}
            ref={rootRef}
            className={cn(
                "border rounded-lg px-3 transition-all duration-200 bg-card",
                // 활성화된 챕터(현재 재생 중)일 때 강조 스타일
                isActive
                    ? "bg-primary/5 border-primary ring-1 ring-primary/30 shadow-sm"
                    : "hover:border-primary/50"
            )}
        >
            {/* group 클래스 추가:
              내부 요소들이 AccordionTrigger의 상태(open/closed)에 반응하도록 함
            */}
            <AccordionTrigger className="py-3 hover:no-underline group text-left">
                <div className="flex flex-col items-start gap-1 w-full">
                    {/* 시간 정보 */}
                    <span className="text-xs font-mono text-muted-foreground flex items-center gap-1 group-hover:text-primary transition-colors">
                        <Clock className="h-3 w-3" />
                        {formatTime(chapter.startTime)} ~ {formatTime(chapter.endTime)}
                    </span>

                    {/* ✅ [제목 길이 제어]
                      기본: line-clamp-2 (2줄 제한)
                      Open 상태: line-clamp-none (제한 해제, 전체 표시)
                    */}
                    <span className="font-semibold text-sm line-clamp-2 break-keep group-data-[state=open]:line-clamp-none transition-all">
                        {chapter.title}
                    </span>
                </div>
            </AccordionTrigger>

            <AccordionContent className="pb-3 cursor-default">
                {/* 1. 챕터 요약문 (Insight View 전용) */}
                <div className="mb-4 p-3 bg-muted/30 rounded-md border-l-2 border-primary/40 text-sm text-muted-foreground leading-relaxed">
                    <span className="font-bold text-foreground/80 block mb-1 text-xs">Chapter Summary</span>
                    {chapter.summary}
                </div>

                {/* 2. Segment Detail Cards (children으로 주입) */}
                <div className="space-y-3 pl-1">
                    {children}
                </div>
            </AccordionContent>
        </AccordionItem>
    );
}
