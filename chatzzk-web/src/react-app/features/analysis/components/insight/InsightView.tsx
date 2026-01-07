import { useState, useEffect, useMemo } from "react";
import { SegmentTrendSection } from "./trend/SegmentTrendSection";
import { RawDashboardResponse } from "../../types/external";
import { mapRawDataToViewData } from "../../utils/mapper";
import { StructureListSection } from "./structure/StructureListSection";


export function InsightView() {
    const [rawData, setRawData] = useState<RawDashboardResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // 1. 데이터 Fetching (API 호출 시뮬레이션)
    useEffect(() => {
        async function loadData() {
            try {
                // public 폴더 기준 경로 입력
                const response = await fetch("/data/analytics.json");
                if (!response.ok) throw new Error("Failed to load data");

                const json = await response.json();
                setRawData(json);
            } catch (error) {
                console.error(error);
            } finally {
                setIsLoading(false);
            }
        }
        loadData();
    }, []);

    // 2. 데이터 매핑 (rawData가 로드된 후에 실행)
    const viewData = useMemo(() => {
        if (!rawData) return null;
        return mapRawDataToViewData(rawData);
    }, [rawData]);

    // 3. 상태 관리: 현재 포커스된 타임스탬프
    const [focusedTimestamp, setFocusedTimestamp] = useState<number | null>(null);

    const handleTrendClick = (timestamp: number) => {
        setFocusedTimestamp(timestamp);
    };

    // 4. 로딩 처리
    if (isLoading || !viewData) {
        return <div className="p-10 text-center">데이터 분석 결과를 불러오는 중...</div>;
    }

    return (
        <div className="flex flex-col gap-3 p-4">

            {/* Top: Trend Section */}
            <SegmentTrendSection
                data={viewData.segments}
                chapters={viewData.chapters}
                intervals={viewData.intervals}
                focusedTimestamp={focusedTimestamp}
                onChartClick={handleTrendClick}
            />

            {/* Bottom Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[60vh] max-h-[800px]">
                <div className="col-span-6 border h-full overflow-hidden">
                    <StructureListSection
                        data={viewData.segments}
                        chapters={viewData.chapters}
                        focusedTimestamp={focusedTimestamp}
                        onSeek={handleTrendClick}
                    />
                </div>
                <div className="col-span-6 border h-full overflow-hidden rounded p-4">
                    Clip Detail Area (Coming Soon)
                    {/* <ClipDetailSection ... /> */}
                </div>
            </div>
        </div>
    );
}
