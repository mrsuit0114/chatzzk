import { useState } from "react";
import { useInsightAccess } from "../hooks/use-insight-access";
import { HighlightView } from "../components/highlight";
import { VodAnalysisHeader } from "../components/header";
import { InsightView } from "../components/insight/InsightView";
import { ViewType } from "../constants";

import { Loader2 } from "lucide-react";
import { useAnalysisData } from "../hooks/use-analysis-data";
import { VodMetadataToVodHeaderData } from "../utils/adapter";

export function VodAnalysisPage() {
    const { viewData, isLoading, error } = useAnalysisData();
    const [currentView, setCurrentView] = useState<ViewType>("highlight");

    const MOCK_VOD_DATA = {
        title: "침착맨 삼국지",
        publishDate: "2024-01-01", // 📅 방송일
        ownerId: "chim_owner",     // 👑 소유자 ID
        channelSettings: {
            insightOpenDays: 7     // ⏳ 7일 뒤 공개 설정
        },
        // ... 기타 데이터
    };

    const { isLocked, reason } = useInsightAccess({
        publishDate: MOCK_VOD_DATA.publishDate,
        insightOpenDays: MOCK_VOD_DATA.channelSettings.insightOpenDays,
        channelOwnerId: MOCK_VOD_DATA.ownerId
    });

    const activeView = (currentView === "insight" && isLocked) ? "highlight" : currentView;


    const handleViewChange = (view: ViewType) => {
        if (view === "insight" && isLocked) {
            // 🔒 잠겨있는데 클릭하면 토스트 메시지 띄우기
            alert(reason || "접근 권한이 없습니다."); // 실제로는 toast.error(reason) 사용
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

    // ✅ 3. 에러 처리
    if (error || !viewData) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background text-destructive">
                <p>데이터를 불러오는데 실패했습니다.</p>
            </div>
        );
    }

    const headerData = VodMetadataToVodHeaderData(viewData.metaInfo);

    return (
        <div className="min-h-screen bg-background">
            <VodAnalysisHeader
                data={headerData}
                currentView={activeView}
                onViewChange={handleViewChange}
                isInsightLocked={isLocked} // ✅ Hook 결과 전달
            />

            <main className="container mx-auto py-3">
                {activeView === "highlight" ? (
                    <HighlightView
                        // ✅ 로딩이 끝났으므로 viewData 안전하게 사용 가능
                        segments={viewData.segments}
                        chapters={viewData.chapters}
                    />
                ) : (
                    !isLocked && (
                        // ✅ InsightView에 viewData 전체 전달
                        <InsightView viewData={viewData} intervals={viewData.metaInfo.intervals} />
                    )
                )}
            </main>
        </div>
    );
}
