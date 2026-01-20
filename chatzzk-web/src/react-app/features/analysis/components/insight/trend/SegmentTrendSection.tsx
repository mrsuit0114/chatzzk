import { useState, useMemo, useRef, useEffect } from "react";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { TrendChart } from "./TrendChart";

import { TrendToolbar } from "./TrendToolbar";
import { SegmentSummaryData, ChapterSummaryData } from "../../../types";
import { ChapterBlockRow } from "./ChapterBlockRow";
import { TrendYAxis } from "./TrendYAxis";
import { CHART_KEYS, METRIC_TYPES, MetricType } from "@/features/analysis/constants";
import { findSegmentIndexBinary, scaleMomentum } from "@/features/analysis/utils/chart-helper";

const CHART_HEIGHT = 250;
const FIXED_Y_DOMAIN: [number, number] = [0, 1.1];
const MIN_ITEM_WIDTH = 5;
const MAX_ITEM_WIDTH = 50;
const INITIAL_ITEM_WIDTH = 20;


interface AnalysisIntervals {
    chapterStep: number; // ms
    segmentStep: number; // ms
}

interface SegmentTrendSectionProps {
    data: SegmentSummaryData[];
    chapters: ChapterSummaryData[];
    intervals: AnalysisIntervals;
    focusedTimestamp: number | null;
    onChartClick: (timestamp: number) => void;
}

export function SegmentTrendSection({
    data,
    chapters,
    intervals,
    focusedTimestamp,
    onChartClick
}: SegmentTrendSectionProps) {
    const [metricType, setMetricType] = useState<MetricType>(METRIC_TYPES.SUMMARY);
    const [isVisible, setIsVisible] = useState({ [CHART_KEYS.VOLUME]: true, [CHART_KEYS.MOMENTUM]: true });
    const [fillBar, setFillBar] = useState(false);

    const [itemWidth, setItemWidth] = useState(INITIAL_ITEM_WIDTH);

    // ✅ [추가] 컨테이너 너비 감지용 Ref
    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const [containerWidth, setContainerWidth] = useState(800);

    useEffect(() => {
        if (scrollContainerRef.current) {
            setContainerWidth(scrollContainerRef.current.clientWidth);
        }
        const handleResize = () => {
            if (scrollContainerRef.current) {
                setContainerWidth(scrollContainerRef.current.clientWidth);
            }
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    // 1. Data Processing
    // Recharts가 Index 기반으로 X축을 잡도록 index 필드 추가
    const chartData = useMemo(() => {
        return data.map((seg, idx) => {
            // Metric 선택 로직
            let volValue = seg.volume;
            let mmtValue = seg.momentum;
            let timestamp = seg.startTime;
            let peakTimestamp: number | null = null;

            if (metricType === "volPeak") {
                volValue = seg.volPeak.volume;
                mmtValue = seg.volPeak.momentum;
                peakTimestamp = seg.volPeak.timestamp;
            } else if (metricType === "mmtPeak") {
                volValue = seg.mmtPeak.volume;
                mmtValue = seg.mmtPeak.momentum;
                peakTimestamp = seg.mmtPeak.timestamp;
            }
            const segmentDuration = seg.endTime - seg.startTime;
            const midTimestamp = seg.startTime + (segmentDuration / 2);
            return {
                ...seg,
                index: idx,
                activeTimestamp: midTimestamp,  // x축 양 끝값 그래프 잘림 방지용
                originalTimestamp: timestamp,  // 실제 타임스탬프
                activeVolume: volValue,
                activeMomentum: scaleMomentum(mmtValue), // 그래프용 (0~1)
                originalMomentum: mmtValue,              // 툴팁용 (원본)
                score: seg.score,
                keywords: seg.keywords,
                peakTimestamp: peakTimestamp
            };
        });
    }, [data, metricType]);

    const { xDomain, xTicks, calculatedWidth } = useMemo(() => {
        if (chapters.length === 0) return { xDomain: [0, 0] as [number, number], xTicks: [], calculatedWidth: 0 };

        // 마지막 챕터의 종료 시간을 전체 길이로 간주
        const totalDuration = chapters[chapters.length - 1].endTime;
        const ticks = data.map(seg => seg.startTime);

        // ✅ [수정] 전체 슬롯(세그먼트) 개수 계산
        // 데이터 개수(data.length)가 아니라 전체 시간 / 세그먼트 간격으로 계산해야 정확함
        const totalSlots = Math.ceil(totalDuration / intervals.segmentStep);

        // 데이터 기반 너비 계산
        const dataWidth = totalSlots * itemWidth;

        return {
            xDomain: [0, totalDuration] as [number, number],
            xTicks: ticks,
            calculatedWidth: dataWidth
        };
    }, [chapters, intervals.segmentStep, itemWidth]);

    // 2. 현재 선택된 세그먼트 찾기
    const activeSegmentIndex = useMemo(() => {
        if (focusedTimestamp === null) return null;
        return findSegmentIndexBinary(chartData, focusedTimestamp);
    }, [focusedTimestamp, chartData]);

    const totalWidth = Math.max(calculatedWidth, containerWidth);

    return (
        <section className="space-y-4 p-4 border rounded-lg bg-card shadow-sm flex flex-col">
            <div className="flex flex-col gap-4 shrink-0">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <TrendToolbar
                        metricType={metricType}
                        onMetricChange={setMetricType}
                        isVisible={isVisible}
                        onVisibilityChange={setIsVisible}
                        fillBar={fillBar}
                        onFillBarChange={setFillBar}
                        zoomLevel={itemWidth}
                        onZoomChange={setItemWidth}
                        minZoom={MIN_ITEM_WIDTH}
                        maxZoom={MAX_ITEM_WIDTH}
                    />
                </div>
            </div>


            <div className="flex flex-1 w-full border rounded-md bg-white/50 overflow-hidden relative">

                {/* Sticky Left Y-Axis */}
                <div className="shrink-0 pt-8 bg-background border-r z-20 shadow-[4px_0_10px_-5px_rgba(0,0,0,0.1)]">
                    <TrendYAxis
                        height={CHART_HEIGHT}
                        yDomain={FIXED_Y_DOMAIN}
                    />
                </div>

                {/* Horizontal Scroll Area */}
                {/* ref 추가하여 너비 감지 */}
                <ScrollArea className="flex-1" ref={scrollContainerRef}>
                    <div style={{ width: totalWidth, height: '100%' }} className="flex flex-col">

                        {/* Chapter Block */}
                        <ChapterBlockRow
                            chapters={chapters}
                            itemNum={intervals.chapterStep / intervals.segmentStep} // 챕터당 세그먼트 수
                            itemWidth={itemWidth} // 동적 너비 전달
                            onChapterClick={onChartClick}
                        />

                        {/* Main Chart */}
                        <div className="flex-1">
                            <TrendChart
                                data={chartData}
                                activeIndex={activeSegmentIndex}
                                showVolume={isVisible[CHART_KEYS.VOLUME]}
                                showMomentum={isVisible[CHART_KEYS.MOMENTUM]}
                                fillBar={fillBar}
                                onChartClick={onChartClick}
                                width={calculatedWidth}
                                height={CHART_HEIGHT}
                                yDomain={FIXED_Y_DOMAIN}
                                xDomain={xDomain}
                                xTicks={xTicks}
                                barSize={itemWidth - 2} // 여백 확보
                            />
                        </div>
                    </div>
                    <ScrollBar orientation="horizontal" />
                </ScrollArea>
            </div>
        </section>
    );
}
