import { cn } from "@/lib/utils";
import { ChapterSummaryData } from "../../../types";
import { formatVideoTime } from "@/features/analysis/utils";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface ChapterBlockRowProps {
    chapters: ChapterSummaryData[];
    itemNum: number;
    itemWidth: number;
    onChapterClick: (timestamp: number) => void;
}

export function ChapterBlockRow({
    chapters,
    itemNum,
    itemWidth,
    onChapterClick
}: ChapterBlockRowProps) {
    const chapterWidth = itemNum * itemWidth

    return (
        <div className="flex h-8 w-full border-b shrink-0">
            <TooltipProvider delayDuration={200}>
                {chapters.map((chapter, idx) => (
                    <Tooltip key={chapter.id}>
                        <TooltipTrigger asChild>
                            <div
                                style={{ width: chapterWidth }}
                                className={cn(
                                    "flex items-center px-2 text-xs font-semibold truncate cursor-pointer transition-colors border-r last:border-r-0",
                                    idx % 2 === 0
                                        ? "bg-slate-100/80 hover:bg-slate-200 text-slate-700"
                                        : "bg-white hover:bg-slate-100 text-slate-600"
                                )}
                                onClick={() => onChapterClick(chapter.startTime)}
                            >
                                <span className="truncate w-full block">
                                    {chapter.title}
                                </span>
                            </div>
                        </TooltipTrigger>
                        <TooltipContent side="bottom" align="start" className="text-xs p-2">
                            <div className="text-muted-foreground">
                                {formatVideoTime(chapter.startTime)} ~ {formatVideoTime(chapter.endTime)}
                            </div>
                            <div className="font-bold mb-1">{chapter.title}</div>
                        </TooltipContent>
                    </Tooltip>
                ))}
            </TooltipProvider>
        </div>
    );
}
