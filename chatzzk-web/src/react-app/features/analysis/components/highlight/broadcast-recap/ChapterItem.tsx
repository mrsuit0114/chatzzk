import { Clock } from "lucide-react";
import { AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { cn, formatTime } from "@/lib/utils";
import type { ChapterSummaryData } from "../../types";

interface ChapterItemProps {
    chapter: ChapterSummaryData;
    isSelected: boolean;
    isOpen: boolean; // 현재 아이템이 열려있는지 여부
    onSelect: () => void;
}

export function ChapterItem({ chapter, isSelected, isOpen, onSelect }: ChapterItemProps) {

    // 헤더 클릭 핸들러: 닫혀있을 때만 선택(Focus) 트리거
    const handleTriggerClick = () => {
        if (!isOpen) {
            onSelect();
        }
    };

    return (
        <AccordionItem
            value={chapter.id}
            className={cn(
                "border rounded-lg px-3 transition-all duration-200 bg-card",
                isSelected
                    ? "bg-primary/5 border-primary ring-1 ring-primary/30 shadow-sm"
                    : "hover:border-primary/50"
            )}
        >
            <AccordionTrigger
                onClick={handleTriggerClick}
                className="py-3 hover:no-underline group"
            >
                <div className="flex flex-col items-start text-left gap-1">
                    <span className="text-xs font-mono text-muted-foreground flex items-center gap-1 group-hover:text-primary transition-colors">
                        <Clock className="h-3 w-3" />
                        {formatTime(chapter.startTime)} ~ {formatTime(chapter.endTime)}
                    </span>
                    <span className="font-semibold text-sm">{chapter.title}</span>
                </div>
            </AccordionTrigger>

            <AccordionContent
                className="pb-3 cursor-default"
                // 내용은 보이는 상태에서 클릭하는 것이므로 무조건 선택(Focus)
                onClick={onSelect}
            >
                <p className="text-sm text-muted-foreground leading-relaxed hover:text-foreground transition-colors cursor-pointer">
                    {chapter.summary}
                </p>
            </AccordionContent>
        </AccordionItem>
    );
}
