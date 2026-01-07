import { BarChart3, HelpCircle, LineChart, ZoomIn } from "lucide-react";
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
        <div className="flex flex-wrap items-center gap-4 p-1">

            {/* 1. Metric Selector */}
            <div className="flex items-center gap-2">
                <Label className="text-xs text-muted-foreground font-medium whitespace-nowrap">
                    Data Basis
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

            <Separator orientation="vertical" className="h-4 hidden sm:block" />

            {/* 2. Visibility Toggles */}
            <div className="flex flex-col gap-4">
                {/* Volume Toggle */}
                <div className="flex items-center space-x-2">
                    <Checkbox
                        id="show-volume"
                        checked={isVisible[CHART_KEYS.VOLUME]}
                        onCheckedChange={() => handleToggle(CHART_KEYS.VOLUME)}
                        className="data-[state=checked]:bg-orange-500 data-[state=checked]:border-orange-500"
                    />
                    <Label
                        htmlFor="show-volume"
                        className="text-xs flex items-center gap-1.5 cursor-pointer font-medium"
                    >
                        <BarChart3 className="h-3.5 w-3.5 text-orange-500" />
                        Volume
                    </Label>
                </div>

                {/* Momentum Toggle */}
                <div className="flex items-center space-x-2">
                    <Checkbox
                        id="show-momentum"
                        checked={isVisible[CHART_KEYS.MOMENTUM]}
                        onCheckedChange={() => handleToggle(CHART_KEYS.MOMENTUM)}
                        className="data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600"
                    />
                    <Label
                        htmlFor="show-momentum"
                        className="text-xs flex items-center gap-1.5 cursor-pointer font-medium"
                    >
                        <LineChart className="h-3.5 w-3.5 text-blue-600" />
                        Momentum
                    </Label>
                </div>
            </div>
            <Separator orientation="vertical" className="h-4 hidden sm:block" />

            {/* ✅ 3. Zoom Slider (Toolbar 내부로 이동) */}
            <div className="flex flex-col gap-2 min-w-[140px]">
                <div className="flex items-center gap-2">
                    <Checkbox
                        id="fill-bar"
                        checked={fillBar}
                        onCheckedChange={(fillBar) => onFillBarChange(!!fillBar)}
                        className="data-[state=checked]:bg-green-500 data-[state=checked]:border-green-500"
                    />
                    <Label
                        htmlFor="fill-bar"
                        className="text-xs flex items-center gap-1 cursor-pointer font-medium"
                    >
                        Color Bars
                    </Label>
                </div>
                <div className="flex items-center gap-2 w-full">
                    <ZoomIn className="h-3.5 w-3.5 text-muted-foreground" />
                    <Slider
                        className="w-[100px]" // 툴바 내부에 맞게 너비 고정
                        min={minZoom}
                        max={maxZoom}
                        step={1}
                        value={[zoomLevel]}
                        onValueChange={(vals) => onZoomChange(vals[0])}
                    />
                </div>
            </div>
            <TooltipProvider delayDuration={300}>
                <Tooltip>
                    <TooltipTrigger asChild>
                        {/* 아이콘 버튼 형태로 스타일링 */}
                        <div className="p-1 rounded-full hover:bg-slate-100 cursor-help transition-colors">
                            <HelpCircle className="h-4 w-4 text-slate-400" />
                        </div>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" align="end" className="max-w-[280px] p-4 text-xs bg-white/95 backdrop-blur-sm">
                        <div className="space-y-3">
                            <div>
                                <h4 className="font-bold text-slate-900 mb-1">그래프 보는 법</h4>
                                <p className="text-slate-600 leading-relaxed">
                                    방송의 흐름을 한눈에 파악할 수 있는 지표입니다.
                                    막대를 클릭하면 해당 시점으로 이동합니다.
                                    데이터는 정규화되어 있으므로 각 지표 설명을 참고하십시오.
                                </p>
                            </div>

                            <div className="grid grid-cols-[16px_1fr] gap-2 items-start">
                                <BarChart3 className="h-3.5 w-3.5 text-orange-500 mt-0.5" />
                                <div>
                                    <span className="font-bold text-slate-800">Volume (막대)</span>
                                    <p className="text-slate-500 mt-0.5">채팅 및 후원의 발생 횟수(화력)를 의미합니다. 0은 방송에서 가장 적은 활동 구간을 나타내고 1은 방송에서 가장 활발한 활동 구간을 나타냅니다. 0.5는 해당 방송의 평균값을 의미합니다.</p>
                                </div>

                                <LineChart className="h-3.5 w-3.5 text-blue-600 mt-0.5" />
                                <div>
                                    <span className="font-bold text-slate-800">Momentum (선)</span>

                                    <p className="text-slate-500 mt-0.5">
                                        채팅 및 후원의 변화율을 의미합니다.
                                    </p>

                                    <p className="text-slate-500 mt-1">
                                        그래프에서 표현된 값과 실제 값(툴팁에서 확인 가능)이 다릅니다.
                                    </p>

                                    <p className="text-slate-500 mt-1">
                                        0.5 → 변화 없음<br />
                                        0.5초과 → 증가<br />
                                        0.8이상 → 폭발적 증가<br />
                                        0.5미만 → 감소
                                    </p>
                                </div>
                            </div>

                            <div className="pt-2 border-t border-slate-100">
                                <span className="font-semibold text-slate-800 block mb-1">Data Basis</span>
                                <ul className="list-disc list-inside text-slate-500 space-y-0.5">
                                    <li><span className="font-medium text-slate-700">Summary:</span> 구간 합</li>
                                    <li><span className="font-medium text-slate-700">Peak:</span> 구간 내 화력 또는 변화율의 최댓값</li>
                                </ul>
                            </div>
                        </div>
                    </TooltipContent>
                </Tooltip>
            </TooltipProvider>
        </div>
    );
}
