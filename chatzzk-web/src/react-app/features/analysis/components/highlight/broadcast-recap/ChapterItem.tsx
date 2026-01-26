import { Clock } from "lucide-react";
import { AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { cn } from "@/lib/utils";
import { ChapterSummaryData } from "@/features/analysis/types";
import { formatTime } from "@/utils/time-formatter";

interface ChapterItemProps {
    chapter: ChapterSummaryData;
    isSelected: boolean;
    isOpen: boolean; // 현재 아이템이 열려있는지 여부
    onSelect: () => void;
}

export function ChapterItem({ chapter, isSelected, isOpen, onSelect }: ChapterItemProps) {

    const handleTriggerClick = () => {
        if (!isOpen) {
            onSelect();
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
                <div className="flex flex-col items-start text-left gap-1.5 w-full">
                    <div className="flex items-center justify-between w-full pr-2">
                        <span className={cn(
                            "text-xs font-mono flex items-center gap-1 transition-colors",
                            isSelected ? "text-primary font-bold" : "text-muted-foreground group-hover/item:text-primary"
                        )}>
                            <Clock className="h-3 w-3" />
                            {formatTime(chapter.startTime)} ~ {formatTime(chapter.endTime)}
                        </span>
                    </div>

                    <span className={cn(
                        "text-sm font-semibold leading-tight break-keep transition-all",
                        isOpen ? "line-clamp-none" : "line-clamp-1"
                    )}>
                        {chapter.title}
                    </span>
                </div>
            </AccordionTrigger>

            <AccordionContent
                className="pb-4 cursor-pointer"
                onClick={(e) => {
                    e.stopPropagation(); // 아코디언 동작 방지 (필요 시)
                    onSelect();
                }}
            >
                <div className={cn(
                    "relative transition-all duration-300 text-sm leading-relaxed whitespace-pre-line",
                    // ✅ [요청 반영] 선택 시 텍스트 뚜렷하게 (text-foreground), 아닐 땐 흐리게
                    isSelected
                        ? "border-primary text-foreground font-medium"
                        : "border-border text-muted-foreground hover:text-foreground"
                )}>
                    {chapter.summary}
                </div>
            </AccordionContent>
        </AccordionItem>
    );
}
