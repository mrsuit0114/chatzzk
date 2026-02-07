import { Check, Clock, Copy } from "lucide-react";
import { AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { cn } from "@/lib/utils";
import { ChapterSummaryData } from "@/features/analysis/types";
import { formatTime } from "@/utils/time-formatter";
import { toast } from "sonner";
import { useState } from "react";
import { buttonVariants } from "@/components/ui/button";

interface ChapterItemProps {
    chapter: ChapterSummaryData;
    isSelected: boolean;
    isOpen: boolean; // 현재 아이템이 열려있는지 여부
    onSelect: () => void;
}

export function ChapterItem({ chapter, isSelected, isOpen, onSelect }: ChapterItemProps) {
    const [isCopied, setIsCopied] = useState(false);
    const hasTopics = chapter.keyTopics && chapter.keyTopics.length > 0;

    const handleTriggerClick = () => {
        if (!isOpen) {
            onSelect();
        }
    };

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
            className={cn(
                "group/item border rounded-lg px-3 transition-all duration-300 mb-2 overflow-hidden",
                // ✅ 선택된 상태 디자인 강화
                isSelected
                    ? "border-primary shadow-sm ring-1 ring-primary/20"
                    : "bg-card hover:border-primary/50"
            )}
        >
            <AccordionTrigger
                onClick={handleTriggerClick}
                className="py-3 hover:no-underline"
            >
                <div className="flex flex-col items-start text-left gap-2 w-full">
                    {/* 시간 표시줄 */}
                    <div className="flex items-center justify-between w-full pr-2">
                        <span className={cn(
                            "text-xs font-mono flex items-center gap-1.5 transition-colors",
                            isSelected ? "text-primary font-bold" : "text-muted-foreground group-hover/item:text-primary"
                        )}>
                            <Clock className="h-4 w-4" />
                            {formatTime(chapter.startTime)} ~ {formatTime(chapter.endTime)}
                        </span>

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

                    {/* 챕터 제목 */}
                    <span className={cn(
                        "text-sm font-semibold leading-snug break-keep transition-colors",
                        // 항상 잘 보이도록 text-foreground 사용, 선택되지 않았을 때만 아주 약간 힘을 뺌
                        isSelected ? "text-foreground" : "text-foreground/90 group-hover/item:text-foreground",
                        isOpen ? "line-clamp-none" : "line-clamp-2"
                    )}>
                        {chapter.title}
                    </span>
                </div>
            </AccordionTrigger>

            <AccordionContent
                className="pb-4 pt-1"
                onClick={(e) => {
                    e.stopPropagation();
                    onSelect();
                }}
            >
                {hasTopics && (
                    <div className="mx-1 p-3 bg-muted/40 rounded-md border border-border/50">
                        <span className="font-bold text-muted-foreground/80 block mb-2 text-[11px] uppercase tracking-wider">
                            Key Topics
                        </span>
                        {/* Key Topics 리스트 영역 */}
                        <ul className="flex flex-col gap-2.5 pl-1">
                            {chapter.keyTopics?.map((topicItem, index) => {
                                const timeStr = topicItem ? topicItem.timestamp : '';
                                const contentStr = topicItem ? topicItem.topic : '';

                                return (
                                    <li key={index} className="flex items-start gap-2.5 text-sm group/topic">
                                        <div className="flex flex-col items-start gap-1 leading-relaxed">
                                            <span className={cn(
                                                "transition-colors",
                                                isSelected ? "text-foreground" : "text-muted-foreground"
                                            )}>
                                                [{timeStr}]: {contentStr}
                                            </span>
                                        </div>
                                    </li>
                                );
                            })}
                        </ul>
                    </div>
                )}
            </AccordionContent>
        </AccordionItem>
    );
}
