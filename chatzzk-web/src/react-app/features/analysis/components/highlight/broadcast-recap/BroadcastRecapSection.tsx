import { useState, useMemo } from "react";
import { ChapterList } from "./ChapterList";
import { SegmentList } from "./SegmentList";
import { ChapterSummaryData, SegmentSummaryData } from "@/features/analysis/types";
import { Button } from "@/components/ui/button";
import { Info } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

interface BroadcastRecapSectionProps {
    chapters: ChapterSummaryData[];
    allSegments: SegmentSummaryData[];
}

export function BroadcastRecapSection({ chapters, allSegments }: BroadcastRecapSectionProps) {
    const [selectedChapterId, setSelectedChapterId] = useState<string>("");

    // 선택된 챕터에 해당하는 세그먼트 필터링
    const currentSegments = useMemo(() => {
        if (!selectedChapterId) return [];
        return allSegments.filter((seg) => seg.chapterId === selectedChapterId);
    }, [selectedChapterId, allSegments]);

    return (
        <section className="space-y-4 pt-6 border-t">
            <div className="space-y-1 px-1">
                <h2 className="text-xl font-bold tracking-tight flex items-center gap-2">
                    방송 전체 요약
                    <RecapTooltip />
                </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-12 gap-4 h-[80vh] min-h-[600px]">

                {/* [Left] Chapter List Container */}
                <div className="md:col-span-6 lg:col-span-6 h-full border-r pr-2 overflow-hidden">
                    <ChapterList
                        chapters={chapters}
                        selectedChapterId={selectedChapterId}
                        onSelectChapter={setSelectedChapterId}
                    />
                </div>

                {/* [Right] Segment List Container */}
                <div className="md:col-span-6 lg:col-span-6 h-full overflow-hidden -pl-2">
                    <SegmentList segments={currentSegments} />
                </div>

            </div>
        </section>
    );
}

function RecapTooltip() {
    return (
        <Popover>
            <PopoverTrigger asChild>
                <Button
                    variant="ghost"
                    size="icon"
                    className="h-5 w-5 rounded-full text-muted-foreground hover:text-primary transition-colors"
                >
                    <Info className="h-4 w-4" />
                    <span className="sr-only">요약 구성 도움말</span>
                </Button>
            </PopoverTrigger>

            <PopoverContent
                side="bottom"
                align="start"
                sideOffset={8}
                collisionPadding={10}
                className="w-[90vw] max-w-[320px] p-4 bg-popover/95 backdrop-blur shadow-xl text-xs space-y-4 border"
            >

                {/* 1. 구조 설명 */}
                <div className="space-y-2">
                    <h4 className="font-bold text-foreground flex items-center gap-1.5">
                        📚 요약 구성 단위
                    </h4>
                    <ul className="space-y-2 text-muted-foreground">
                        <li className="flex gap-2 items-start">
                            <span className="bg-primary/10 text-primary px-1.5 py-0.5 rounded text-[10px] font-bold shrink-0 mt-0.5">
                                1시간
                            </span>
                            <div className="leading-relaxed">
                                <span className="text-foreground font-medium">챕터 (Chapter)</span>
                                <br />방송의 전체적인 큰 흐름을 파악하는 단위입니다.
                            </div>
                        </li>
                        <li className="flex gap-2 items-start">
                            <span className="bg-secondary text-secondary-foreground px-1.5 py-0.5 rounded text-[10px] font-bold shrink-0 mt-0.5">
                                5분
                            </span>
                            <div className="leading-relaxed">
                                <span className="text-foreground font-medium">세그먼트 (Segment)</span>
                                <br />주요 사건과 대화를 상세하게 기록한 단위입니다.
                            </div>
                        </li>
                    </ul>
                </div>

                {/* 2. 사용 방법 (인터랙션) */}
                <div className="space-y-1 pt-2 border-t border-border/50">
                    <h4 className="font-bold text-foreground mb-1">💡 사용 팁</h4>
                    <p className="text-muted-foreground leading-relaxed">
                        흥미로워 보이는 <span className="text-foreground font-semibold decoration-wavy decoration-primary/50">챕터를 클릭</span>해보세요.
                        <br />
                        해당 시간대에 포함된 상세 세그먼트들이 <span className="text-foreground font-medium">화면</span>에 나타납니다.
                    </p>
                </div>

            </PopoverContent>
        </Popover>
    )
}
