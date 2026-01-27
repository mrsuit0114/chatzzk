import { ListFilter, ArrowUpDown, Layers, Info } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    DropdownMenu,
    DropdownMenuCheckboxItem,
    DropdownMenuContent,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

import { SORT_OPTIONS, SortOption } from "@/features/analysis/constants";
import { ATMOSPHERE_LABELS } from "@/constants";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface MomentsToolbarProps {
    // Atmosphere Filter Props
    availableAtmospheres: string[]; // 전체 분위기 목록 (예: ["Funny", "Tension", ...])
    selectedAtmospheres: string[];  // 현재 선택된 분위기들
    onAtmosphereChange: (selected: string[]) => void;

    // Sort Props
    currentSort: SortOption;
    onSortChange: (option: SortOption) => void;

    // Top N Props
    topN: number;
    onTopNChange: (n: number) => void;
}

export function MomentsToolbar({
    availableAtmospheres,
    selectedAtmospheres,
    onAtmosphereChange,
    currentSort,
    onSortChange,
    topN,
    onTopNChange
}: MomentsToolbarProps) {

    // Atmosphere 다중 선택 핸들러
    const handleAtmosphereToggle = (attr: string, checked: boolean) => {
        if (checked) {
            onAtmosphereChange([...selectedAtmospheres, attr]);
        } else {
            onAtmosphereChange(selectedAtmospheres.filter((a) => a !== attr));
        }
    };

    // "전체 선택" 로직
    const isAllSelected = availableAtmospheres.length > 0 && selectedAtmospheres.length === availableAtmospheres.length;
    const handleSelectAll = () => {
        if (isAllSelected) {
            onAtmosphereChange([]); // 전체 해제
        } else {
            onAtmosphereChange([...availableAtmospheres]); // 전체 선택
        }
    };

    const metricIntroMap: Record<SortOption, string> = {
        [SORT_OPTIONS.VOLUME]:
            "전체 방송 기준 시청자의 참여도를 기준으로 선정",
        [SORT_OPTIONS.MOMENTUM]:
            "최근 짧은 시간 내 급격한 참여도 상승을 기준으로 선정",
        [SORT_OPTIONS.SCORE]:
            "AI가 측정한 종합 평점(1~10)을 기준으로 선정",
    };

    return (
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            {/* ---------------------------------------------------------
                [Left] Section Introduction
               --------------------------------------------------------- */}
            <div className="space-y-1">
                <h2 className="text-xl font-bold tracking-tight flex items-center gap-2">
                    이번 방송의 하이라이트
                    <Badge variant="secondary" className="text-xs font-normal">
                        {topN === 0 ? "전체" : `Top ${topN}`}
                    </Badge>
                    <BestMomentsTooltip />
                </h2>
                <p className="text-sm leading-5 text-muted-foreground max-w-md whitespace-pre-line h-[0.5rem]">
                    {metricIntroMap[currentSort]}
                </p>
            </div>

            {/* ---------------------------------------------------------
                [Right] Controls: Filter & Sort
               --------------------------------------------------------- */}
            <div className="flex items-center gap-2">

                {/* 1. Atmosphere Filter (Multi-select Dropdown) */}
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="sm" className="h-9 border-dashed">
                            <ListFilter className="mr-2 h-4 w-4" />
                            분위기
                            {/* 선택된 개수 뱃지 표시 */}
                            {selectedAtmospheres.length > 0 && selectedAtmospheres.length < availableAtmospheres.length && (
                                <>
                                    <Separator orientation="vertical" className="mx-2 h-4" />
                                    <Badge variant="secondary" className="rounded-sm px-1 font-normal lg:hidden">
                                        {selectedAtmospheres.length}
                                    </Badge>
                                    <div className="hidden space-x-1 lg:flex">
                                        {selectedAtmospheres.length > 2 ? (
                                            <Badge variant="secondary" className="rounded-sm px-1 font-normal">
                                                {selectedAtmospheres.length} selected
                                            </Badge>
                                        ) : (
                                            selectedAtmospheres.map((attr) => (
                                                <Badge variant="secondary" key={attr} className="rounded-sm px-1 font-normal">
                                                    {ATMOSPHERE_LABELS[attr as keyof typeof ATMOSPHERE_LABELS]}
                                                </Badge>
                                            ))
                                        )}
                                    </div>
                                </>
                            )}
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-[200px]">

                        {/* Select All Option */}
                        <DropdownMenuCheckboxItem
                            checked={isAllSelected}
                            onCheckedChange={handleSelectAll}
                        >
                            <span className={isAllSelected ? "font-bold" : ""}>전체 선택</span>
                        </DropdownMenuCheckboxItem>
                        <DropdownMenuSeparator />

                        {/* Individual Options */}
                        {availableAtmospheres.map((attr) => (
                            <DropdownMenuCheckboxItem
                                key={attr}
                                checked={selectedAtmospheres.includes(attr)}
                                onCheckedChange={(checked) => handleAtmosphereToggle(attr, checked)}
                            >
                                {ATMOSPHERE_LABELS[attr as keyof typeof ATMOSPHERE_LABELS]}
                            </DropdownMenuCheckboxItem>
                        ))}
                    </DropdownMenuContent>
                </DropdownMenu>

                {/* 2. Sort Select */}
                <Select value={currentSort} onValueChange={(val) => onSortChange(val as SortOption)}>
                    <SelectTrigger className="h-9 w-[130px] text-xs">
                        <div className="flex items-center gap-2">
                            <ArrowUpDown className="h-3.5 w-3.5 text-muted-foreground" />
                            <SelectValue placeholder="Sort by" />
                        </div>
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value={SORT_OPTIONS.VOLUME}>🔥 화력순</SelectItem>
                        <SelectItem value={SORT_OPTIONS.MOMENTUM}>⚡ 급상승순</SelectItem>
                        <SelectItem value={SORT_OPTIONS.SCORE}>⭐ 평점순</SelectItem>
                    </SelectContent>
                </Select>

                {/* 3. Top N Select */}
                <Select value={topN.toString()} onValueChange={(val) => onTopNChange(parseInt(val))}>
                    <SelectTrigger className="h-9 w-[100px] text-xs">
                        <div className="flex items-center gap-2">
                            <Layers className="h-3.5 w-3.5 text-muted-foreground" />
                            <span className="truncate">{topN === 0 ? "전체" : `Top ${topN}`}</span>
                        </div>
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="5">Top 5</SelectItem>
                        <SelectItem value="10">Top 10</SelectItem>
                        <SelectItem value="0">전체</SelectItem>
                    </SelectContent>
                </Select>

            </div>
        </div>
    );
}

function BestMomentsTooltip() {
    return (
        <TooltipProvider delayDuration={100}>
            <Tooltip>
                <TooltipTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-5 w-5 rounded-full text-muted-foreground hover:text-primary">
                        <Info className="h-4 w-4" />
                    </Button>
                </TooltipTrigger>
                <TooltipContent side="right" align="start" className="max-w-sm p-4 bg-popover/95 backdrop-blur shadow-xl text-xs space-y-4">

                    {/* 1. 분석 기준 */}
                    <div className="space-y-1">
                        <h4 className="font-bold text-foreground">📊 분석 및 정렬 기준</h4>
                        <p className="text-muted-foreground leading-relaxed">
                            요약과 평점은 <span className="text-foreground font-medium">5분 단위 데이터(세그먼트)</span>를 기준으로 산출됩니다.
                        </p>
                        <p className="text-muted-foreground leading-relaxed">
                            화력과 변동성 순위는 각 피크를 기준으로 정렬됩니다. <br />예를 들어 화력순 정렬 시, 각 구간의 <span className="text-red-500 font-medium">화력 피크</span> 값을 기준으로 순위가 매겨집니다.
                        </p>
                    </div>

                    {/* 2. 지표 상세 */}
                    <div className="space-y-2">
                        <h4 className="font-bold text-foreground">💡 지표 설명</h4>
                        <ul className="space-y-1.5 text-muted-foreground">
                            <li>
                                <span className="text-red-500 font-bold">화력 (시청자 참여도):</span> 0~1 사이의 상대값.
                                <br />1에 가까울수록 이번 방송 중 가장 활발했음을 의미합니다.
                            </li>
                            <li>
                                <span className="text-blue-500 font-bold">변동 (화력의 변화):</span> 약 -3~3 사이의 값.
                                <br />0보다 큰 경우는 상승, 작은 경우는 하락을 의미합니다.
                                <br />0에서 멀어질수록 급격한 변화를 의미합니다.
                            </li>
                            <li>
                                <span className="text-yellow-500 font-bold">평점 (Score):</span> 10점 만점.
                                <br />상황, 스트리머와 시청자의 반응을 종합적으로<br /> 고려하여 매겨진 점수입니다.
                                <br />AI가 평가한 점수입니다. (방송 역량과는 무관)
                            </li>
                        </ul>
                    </div>

                    {/* 3. PEAK 정보 */}
                    <div className="space-y-1">
                        <h4 className="font-bold text-foreground">📈 PEAK 구간</h4>
                        <p className="text-muted-foreground leading-relaxed">
                            5분 구간 내에서 <span className="text-foreground font-medium">30초 단위</span>로 가장 높은 지점을 대푯값으로 사용합니다.
                            <br />화력 피크와 변동 피크의 시점은 다를 수 있습니다.
                        </p>
                    </div>

                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    )
}
