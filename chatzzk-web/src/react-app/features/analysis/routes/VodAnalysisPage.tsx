import { useState } from "react";
import { HighlightView } from "../components/highlight";
import { VodAnalysisHeader } from "../components/header";
import { InsightView } from "../components/insight/InsightView";
import { ViewType } from "../constants";

import { AlertCircle, Loader2 } from "lucide-react";
import { useAnalysisData } from "../hooks/use-analysis-data";
import { transformRawToHeaderData } from "../utils";
import { useParams } from "react-router-dom";

export function VodAnalysisPage() {
    // const { platform, videoNo } = useParams();

    // 1. Hook을 통해 R2 데이터 Fetching
    const { data: rawData, isLoading, error } = useAnalysisData();

    const [currentView, setCurrentView] = useState<ViewType>("highlight");
    const isInsightLocked = (rawData as any)?._meta?.isInsightLocked ?? false;

    const handleViewChange = (view: ViewType) => {
        if (view === "insight" && isInsightLocked) {
            alert("아직 분석 결과가 공개되지 않았습니다.");
            return;
        }
        setCurrentView(view);
    };

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
                    <p className="font-semibold">분석이 완료되지 않은 데이터입니다.</p>
                </div>
            </div>
        );
    }

    // ✅ 2. 데이터 변환 (metaInfo + stats -> HeaderData)
    // 기존 VodMetadataToVodHeaderData 대신 transformRawToHeaderData 사용
    const headerData = transformRawToHeaderData(rawData.metaInfo, rawData.stats);

    return (
        <div className="min-h-screen bg-background pb-20">
            <VodAnalysisHeader
                data={headerData}
                currentView={currentView}
                onViewChange={handleViewChange}
                isInsightLocked={isInsightLocked}
            />

            {/* <main className="container mx-auto py-6 space-y-8">
                {currentView === "highlight" ? (
                    <HighlightView
                        segments={rawData.segments} // Raw Data 그대로 전달 (필요시 내부에서 변환)
                        chapters={rawData.chapters}
                    />
                ) : (
                    !isInsightLocked && (
                        <InsightView
                            viewData={rawData}
                            intervals={rawData.metaInfo.intervals}
                        />
                    )
                )}
            </main> */}
        </div>
    );
}
