import { Check, Clock, Copy } from "lucide-react";
import { AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { cn } from "@/lib/utils";
import { ChapterSummaryData } from "@/features/analysis/types";
import { formatTime } from "@/utils/time-formatter";
import { useState } from "react";
import { toast } from "sonner";
import { buttonVariants } from "@/components/ui/button";

interface StructureChapterItemProps {
    chapter: ChapterSummaryData;
    isActive: boolean; // 현재 타임스탬프가 이 챕터에 포함되는지 여부 (스타일링용)
    children: React.ReactNode; // 내부에 들어갈 SegmentDetailCard 리스트
    rootRef?: (node: HTMLDivElement | null) => void;
}

export function ChapterItem({ chapter, isActive, children, rootRef }: StructureChapterItemProps) {
    const [isCopied, setIsCopied] = useState(false);
    const hasTopics = chapter.keyTopics && chapter.keyTopics.length > 0;


    const handleCopy = (e: React.MouseEvent) => {
        e.stopPropagation(); // 아코디언 토글 방지

        if (!hasTopics) {
            toast.error("복사할 내용이 없습니다.");
            return;
        }

        // 포맷팅: HH:MM:00 내용
        const textToCopy = chapter.keyTopics?.map(topicItem => {
            const timeStr = topicItem.timestamp;
            const contentStr = topicItem.topic;
            // ss는 00으로 고정
            return `${timeStr}:00 ${contentStr}`;
        }).join('\n');

        if (textToCopy) {
            navigator.clipboard.writeText(textToCopy);
            setIsCopied(true);
            toast.success("타임라인이 복사되었습니다.");

            // 2초 후 아이콘 원상복구
            setTimeout(() => setIsCopied(false), 2000);
        }
    };

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
                    <div className="flex items-center justify-between w-full pr-2">
                        <span className="text-xs font-mono px-2 text-muted-foreground flex items-center gap-1 group-hover:text-primary transition-colors">
                            <Clock className="h-3 w-3" />
                            {formatTime(chapter.startTime)} ~ {formatTime(chapter.endTime)}
                        </span>

                        {/* ✅ 복사 버튼 추가 */}
                        <span
                            role="button"
                            tabIndex={0}
                            className={cn(
                                // Button 컴포넌트의 스타일(ghost, icon)을 그대로 가져옴
                                buttonVariants({ variant: "ghost", size: "icon" }),
                                "h-6 w-6 text-muted-foreground hover:text-foreground hover:bg-muted cursor-pointer"
                            )}
                            onClick={handleCopy}
                            title="타임라인 복사"
                        >
                            {isCopied ? (
                                <Check className="h-3.5 w-3.5 text-green-500" />
                            ) : (
                                <Copy className="h-3.5 w-3.5" />
                            )}
                        </span>
                    </div>
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
                            {chapter.keyTopics.map((topicItem, index) => {
                                const timeStr = topicItem ? topicItem.timestamp : '';
                                const contentStr = topicItem ? topicItem.topic : '';

                                return (
                                    <li key={index} className="flex items-start gap-2 text-sm">
                                        {/* 토픽 내용 */}
                                        <span className="text-foreground/90 leading-relaxed break-keep">
                                            [{timeStr}]: {contentStr}
                                        </span>
                                    </li>
                                );
                            })}
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
