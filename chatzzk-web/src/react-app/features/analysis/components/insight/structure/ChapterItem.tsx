import { ChevronRight, Clock } from "lucide-react";
import { AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { cn } from "@/lib/utils";
import { ChapterSummaryData } from "@/features/analysis/types";
import { formatTime } from "@/utils/time-formatter";

interface StructureChapterItemProps {
    chapter: ChapterSummaryData;
    isActive: boolean; // 현재 타임스탬프가 이 챕터에 포함되는지 여부 (스타일링용)
    children: React.ReactNode; // 내부에 들어갈 SegmentDetailCard 리스트
    rootRef?: (node: HTMLDivElement | null) => void;
}

export function ChapterItem({ chapter, isActive, children, rootRef }: StructureChapterItemProps) {
    const hasTopics = chapter.keyTopics && chapter.keyTopics.length > 0;

    return (
        <AccordionItem
            value={chapter.id}
            ref={rootRef}
            className={cn(
                "border rounded-lg px-1 transition-all duration-200 bg-card",
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
                    <span className="text-xs font-mono px-2 text-muted-foreground flex items-center gap-1 group-hover:text-primary transition-colors">
                        <Clock className="h-3 w-3" />
                        {formatTime(chapter.startTime)} ~ {formatTime(chapter.endTime)}
                    </span>

                    {/* ✅ [제목 길이 제어]
                      기본: line-clamp-2 (2줄 제한)
                      Open 상태: line-clamp-none (제한 해제, 전체 표시)
                    */}
                    <span className="font-semibold text-sm px-2 line-clamp-2 break-keep group-data-[state=open]:line-clamp-none transition-all">
                        {chapter.title}
                    </span>
                </div>
            </AccordionTrigger>

            <AccordionContent className="pb-2 cursor-default">
                {/* 1. Key Topics Area (기존 Summary 대체) */}
                {hasTopics && (
                    <div className="mb-4 mx-1 p-3 bg-muted/40 rounded-md border border-border/50">
                        <span className="font-bold text-muted-foreground/80 block mb-2 text-[11px] uppercase tracking-wider">
                            Key Topics
                        </span>

                        <ul className="flex flex-col gap-2">
                            {chapter.keyTopics.map((topic, index) => (
                                <li key={index} className="flex items-start gap-2 text-sm">
                                    {/* 불릿 아이콘 (RecapSection과 스타일 통일) */}
                                    <div className="mt-[5px] min-w-[12px] flex justify-center">
                                        <ChevronRight className="h-4 w-4 text-primary/70 stroke-[2.5px]" />
                                    </div>

                                    {/* 토픽 내용 */}
                                    <span className="text-foreground/90 leading-relaxed break-keep">
                                        {topic}
                                    </span>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* 2. Segment Detail Cards (children으로 주입) */}
                <div className="space-y-3">
                    {children}
                </div>
            </AccordionContent>
        </AccordionItem>
    );
}
