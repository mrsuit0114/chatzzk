import { ListFilter, ArrowUpDown, Layers } from "lucide-react";

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

    return (
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 pb-2 border-b mb-6">
            {/* ---------------------------------------------------------
                [Left] Section Introduction
               --------------------------------------------------------- */}
            <div className="space-y-1">
                <h2 className="text-xl font-bold tracking-tight flex items-center gap-2">
                    Best Moments
                    <Badge variant="secondary" className="text-xs font-normal text-muted-foreground">
                        {topN === 0 ? "all" : `Top ${topN}`}
                    </Badge>
                </h2>
                <p className="text-sm text-muted-foreground max-w-md break-keep">
                    시청자 참여도의 화력과 급상승 지표를 분석하여 선정한 하이라이트 구간입니다. 평점은 내부 지표에 따라 AI가 산출한 값입니다.
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
                            <span className="truncate">{topN === 0 ? "all" : `Top ${topN}`}</span>
                        </div>
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="5">Top 5</SelectItem>
                        <SelectItem value="10">Top 10</SelectItem>
                        <SelectItem value="0">all</SelectItem>
                    </SelectContent>
                </Select>

            </div>
        </div>
    );
}
