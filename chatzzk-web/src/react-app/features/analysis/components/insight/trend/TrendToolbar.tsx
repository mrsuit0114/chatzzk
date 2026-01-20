import { BarChart3, Info, LineChart, ZoomIn } from "lucide-react";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Separator } from "@/components/ui/separator";
import { CHART_KEYS, ChartKey, METRIC_LABELS, MetricType } from "@/features/analysis/constants";
import { Slider } from "@/components/ui/slider";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";


interface TrendToolbarProps {
    metricType: MetricType;
    onMetricChange: (value: MetricType) => void;
    isVisible: { [key in ChartKey]: boolean };
    onVisibilityChange: (value: { [key in ChartKey]: boolean }) => void;
    fillBar: boolean;
    onFillBarChange: (value: boolean) => void;
    zoomLevel: number;
    onZoomChange: (value: number) => void;
    minZoom: number;
    maxZoom: number;
}

export function TrendToolbar({
    metricType,
    onMetricChange,
    isVisible,
    onVisibilityChange,
    fillBar,
    onFillBarChange,
    zoomLevel,
    onZoomChange,
    minZoom,
    maxZoom
}: TrendToolbarProps) {

    const handleToggle = (key: ChartKey) => {
        onVisibilityChange({
            ...isVisible,
            [key]: !isVisible[key],
        });
    };
    return (
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6 w-full">

            {/* [LEFT] Title & Description & Tooltip */}
            <div className="space-y-1">
                <div className="flex items-center gap-2">
                    <h3 className="text-xl font-bold tracking-tight">세그먼트 분석</h3>
                    <TrendTooltip />
                </div>
                <p className="text-sm text-muted-foreground max-w-lg break-keep leading-relaxed">
                    상단 타임라인과 차트를 활용해 세그먼트 트렌드를 분석해보세요.
                </p>
            </div>

            {/* [RIGHT] Controls */}
            <div className="flex flex-wrap items-center gap-x-2 gap-y-4">

                {/* 1. Metric Selector */}
                <div className="flex flex-col gap-1.5">
                    <Label className="text-[10px] uppercase text-muted-foreground font-bold tracking-wider">
                        분석 기준
                    </Label>
                    <Select value={metricType} onValueChange={(val) => onMetricChange(val as MetricType)}>
                        <SelectTrigger className="h-8 w-[140px] text-xs">
                            <SelectValue placeholder="Select Metric" />
                        </SelectTrigger>
                        <SelectContent>
                            {(Object.entries(METRIC_LABELS) as [MetricType, string][]).map(([value, label]) => (
                                <SelectItem key={value} value={value} className="text-xs">
                                    {label}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                <Separator orientation="vertical" className="h-8 hidden sm:block bg-border/60" />

                {/* 2. Visibility Toggles */}
                <div className="flex flex-col gap-2">
                    <div className="flex items-center space-x-2">
                        <Checkbox
                            id="show-volume"
                            checked={isVisible[CHART_KEYS.VOLUME]}
                            onCheckedChange={() => handleToggle(CHART_KEYS.VOLUME)}
                            className="h-4 w-4 data-[state=checked]:bg-orange-500 data-[state=checked]:border-orange-500"
                        />
                        <Label htmlFor="show-volume" className="text-xs flex items-center gap-1.5 cursor-pointer font-medium">
                            <BarChart3 className="h-3.5 w-3.5 text-orange-500" />
                            화력
                        </Label>
                    </div>

                    <div className="flex items-center space-x-2">
                        <Checkbox
                            id="show-momentum"
                            checked={isVisible[CHART_KEYS.MOMENTUM]}
                            onCheckedChange={() => handleToggle(CHART_KEYS.MOMENTUM)}
                            className="h-4 w-4 data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600"
                        />
                        <Label htmlFor="show-momentum" className="text-xs flex items-center gap-1.5 cursor-pointer font-medium">
                            <LineChart className="h-3.5 w-3.5 text-blue-600" />
                            변동성
                        </Label>
                    </div>
                </div>

                <Separator orientation="vertical" className="h-8 hidden sm:block bg-border/60" />

                {/* 3. Style & Zoom */}
                <div className="flex flex-col gap-3 min-w-[140px]">
                    {/* Color Bars Toggle */}
                    <div className="flex items-center gap-2">
                        <Checkbox
                            id="fill-bar"
                            checked={fillBar}
                            onCheckedChange={(fillBar) => onFillBarChange(!!fillBar)}
                            className="h-4 w-4 data-[state=checked]:bg-green-600 data-[state=checked]:border-green-600"
                        />
                        <Label htmlFor="fill-bar" className="text-xs cursor-pointer font-medium">
                            분위기 색상 적용
                        </Label>
                    </div>

                    {/* Zoom Slider */}
                    <div className="flex items-center gap-2 w-full">
                        <ZoomIn className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                        <Slider
                            className="flex-1 min-w-[80px]"
                            min={minZoom}
                            max={maxZoom}
                            step={1}
                            value={[zoomLevel]}
                            onValueChange={(vals) => onZoomChange(vals[0])}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}

function TrendTooltip() {
    return (
        <TooltipProvider delayDuration={200}>
            <Tooltip>
                <TooltipTrigger asChild>
                    <button className="p-1 rounded-full hover:bg-muted text-muted-foreground hover:text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-primary/50" aria-label="그래프 도움말">
                        <Info className="h-4 w-4 text-primary" />
                    </button>
                </TooltipTrigger>
                <TooltipContent side="right" align="start" className="max-w-[360px] p-5 text-xs bg-popover/95 backdrop-blur shadow-xl border-border">
                    <div className="space-y-4">
                        <div className="space-y-1">
                            <p className="text-muted-foreground leading-relaxed">
                                방송 전체 흐름 비교를 위해 0~1 사이로 정규화되었습니다.
                            </p>
                        </div>

                        <Separator />

                        <div className="grid grid-cols-[20px_1fr] gap-3 items-start">
                            <BarChart3 className="h-4 w-4 text-orange-500 mt-0.5" />
                            <div className="space-y-1">
                                <span className="font-bold text-foreground">화력 (막대)</span>
                                <p className="text-muted-foreground">채팅 및 후원의 발생 빈도(화력)입니다.</p>
                                <p className="text-muted-foreground">전체 방송을 기준으로 계산된 값입니다.</p>
                                <ul className="list-disc list-inside text-muted-foreground/80 mt-1 pl-1 space-y-0.5">
                                    <li><span className="font-semibold text-foreground">1.0</span> : 방송 최고 화력 시점</li>
                                    <li><span className="font-semibold text-foreground">0.5</span> : 평균적인 수준</li>
                                    <li><span className="font-semibold text-foreground">0.0</span> : 가장 조용한 시점</li>
                                </ul>
                            </div>

                            <LineChart className="h-4 w-4 text-blue-600 mt-0.5" />
                            <div className="space-y-1">
                                <span className="font-bold text-foreground">변동성 (선)</span>
                                <p className="text-muted-foreground">화력의 변화 수치이며 괄호의 값은 참고용 실제 값입니다.</p>
                                <p className="text-muted-foreground">인접 구간을 반영하여 시청자 수 변화를 고려하였습니다.</p>
                                <ul className="list-disc list-inside text-muted-foreground/80 mt-1 pl-1 space-y-0.5">
                                    <li><span className="font-semibold text-foreground">0.8↑</span> : 폭발적인 급상승</li>
                                    <li><span className="font-semibold text-foreground">0.5↑</span> : 화력 증가 추세</li>
                                    <li><span className="font-semibold text-foreground">0.5↓</span> : 화력 감소 추세</li>
                                </ul>
                            </div>
                        </div>

                        <div className="pt-3 border-t bg-muted/20 -mx-5 mb-5 p-4 rounded-b-md">
                            <span className="font-semibold text-foreground block mb-1.5 text-[11px] uppercase tracking-wider">데이터 기준 옵션</span>
                            <ul className="grid grid-rows-2 gap-2 text-muted-foreground">
                                <li>
                                    <span className="font-medium text-foreground mr-1">세그먼트:</span>
                                    5분 단위 기준
                                </li>
                                <li>
                                    <span className="font-medium text-foreground mr-1">피크:</span>
                                    세그먼트 내 최고 시점(30초 단위)
                                </li>
                            </ul>
                        </div>
                    </div>
                    <div className="pt-3 border-t bg-muted/10 -mx-5 -mb-5 p-4 rounded-b-md">
                        <span className="font-semibold text-foreground block mb-2 text-[11px] uppercase tracking-wider">
                            분석 하는 법
                        </span>

                        <ul className="space-y-1.5 text-muted-foreground leading-relaxed">
                            <li className="flex gap-2">
                                <span className="mt-[3px] h-1.5 w-1.5 rounded-full bg-foreground/60 shrink-0" />
                                <span>
                                    상단 그래프에서 큰 단위로 탐색하고 30초 단위로 표현된 하단 그래프에서 세부 변화를 확인하세요.
                                </span>
                            </li>

                            <li className="flex gap-2">
                                <span className="mt-[3px] h-1.5 w-1.5 rounded-full bg-foreground/60 shrink-0" />
                                <span>
                                    차트와 타임라인을 클릭하여 해당 시점으로 즉시 이동할 수 있습니다.
                                </span>
                            </li>
                        </ul>
                    </div>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    )
}
