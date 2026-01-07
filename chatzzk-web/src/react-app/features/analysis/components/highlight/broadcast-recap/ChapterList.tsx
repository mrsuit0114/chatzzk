import React from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Accordion } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { ChapterItem } from "./ChapterItem"; // 분리된 컴포넌트 임포트
import { ChapterSummaryData } from "@/features/analysis/types";

interface ChapterListProps {
    chapters: ChapterSummaryData[];
    selectedChapterId: string;
    onSelectChapter: (id: string) => void;
}

export function ChapterList({ chapters, selectedChapterId, onSelectChapter }: ChapterListProps) {
    const [openItems, setOpenItems] = React.useState<string[]>([]);
    const isAllOpen = chapters.length > 0 && openItems.length === chapters.length;

    const handleToggleAll = () => {
        if (isAllOpen) setOpenItems([]);
        else setOpenItems(chapters.map((c) => c.id));
    };

    return (
        <div className="flex flex-col h-full overflow-hidden">
            <div className="flex-none flex items-center justify-between pb-4 border-b bg-background">
                <h3 className="text-lg font-bold">Chapters</h3>
                <Button variant="ghost" size="sm" onClick={handleToggleAll} className="h-7 text-xs text-muted-foreground hover:text-foreground">
                    {isAllOpen ? <><ChevronUp className="mr-1 h-3 w-3" /> 모두 접기</> : <><ChevronDown className="mr-1 h-3 w-3" /> 모두 펴기</>}
                </Button>
            </div>

            <div className="flex-1 overflow-y-auto pt-4 space-y-2 pr-2 custom-scrollbar min-h-0 pb-12">
                <Accordion type="multiple" value={openItems} onValueChange={setOpenItems} className="w-full space-y-2">
                    {chapters.map((chapter) => (
                        <ChapterItem
                            key={chapter.id}
                            chapter={chapter}
                            isSelected={selectedChapterId === chapter.id}
                            isOpen={openItems.includes(chapter.id)} // 열림 상태 전달
                            onSelect={() => onSelectChapter(chapter.id)}
                        />
                    ))}
                </Accordion>
            </div>
        </div>
    );
}
