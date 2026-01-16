import { useMemo, useState } from "react";
import { HighlightView } from "../components/highlight";
import { VodAnalysisHeader } from "../components/header";
import { InsightView } from "../components/insight/InsightView";
import { ViewType } from "../constants";

import { AlertCircle, Loader2 } from "lucide-react";
import { useAnalysisData } from "../hooks/use-analysis-data";
import { transformClipsData, transformHighlightData, transformRawToHeaderData } from "../utils";
import { InsightViewData } from "../types";

export function VodAnalysisPage() {
    // const { platform, videoNo } = useParams();

    // 1. Hook을 통해 R2 데이터 Fetching
    const { data: rawData, isLoading, error } = useAnalysisData();

    const [currentView, setCurrentView] = useState<ViewType>("highlight");

    const highlightData = useMemo(() => {
        if (!rawData) return { segments: [], chapters: [] };
        return transformHighlightData(rawData);
    }, [rawData]);

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background">
                <div className="flex flex-col items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-8 w-8 animate-spin" />
                    <p>분석 데이터를 불러오는 중입니다...</p>
                </div>
            </div>
        );
    }

    if (error || !rawData) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background text-destructive">
                <div className="flex flex-col items-center gap-2">
                    <AlertCircle className="h-10 w-10" />
                    <p className="font-semibold">권한이 없거나 분석이 완료되지 않은 데이터입니다.</p>
                </div>
            </div>
        );
    }

    // ✅ 2. 데이터 변환 (metaInfo + stats -> HeaderData)
    const headerData = transformRawToHeaderData(rawData.metaInfo, rawData.stats);
    const isInsightLocked = (rawData as any)?._meta?.isInsightLocked ?? false;

    const insightViewData: InsightViewData = {
        chapters: highlightData.chapters,
        segments: highlightData.segments,
        clips: transformClipsData(rawData), // 새로 만든 변환 함수 사용
    };

    const handleViewChange = (view: ViewType) => {
        if (view === "insight" && isInsightLocked) {
            alert("아직 분석 결과가 공개되지 않았습니다.");
            return;
        }
        setCurrentView(view);
    };

    return (
        <div className="min-h-screen bg-background pb-20">
            <VodAnalysisHeader
                data={headerData}
                currentView={currentView}
                onViewChange={handleViewChange}
                isInsightLocked={isInsightLocked}
            />

            <main className="container mx-auto py-6 space-y-8">
                {currentView === "highlight" ? (
                    <HighlightView
                        segments={highlightData.segments} // Raw Data 그대로 전달 (필요시 내부에서 변환)
                        chapters={highlightData.chapters}
                    />
                ) : (
                    !isInsightLocked && (
                        <InsightView
                            viewData={insightViewData}
                            intervals={rawData.metaInfo.intervals}
                        />
                    )
                )}
            </main>
        </div>
    );
}
