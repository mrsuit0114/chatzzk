import { useEffect, useState } from "react";
import { VodAnalysisHeader, ViewType } from "../components/header";
import { useInsightAccess } from "../hooks/useInsightAccess";
import { MOCK_SEGMENTS } from "../components/highlight/mock";
import { BestMomentsSection } from "../components/highlight/best-moments/BestMomentsSection";

export function VodAnalysisPage() {
    const [currentView, setCurrentView] = useState<ViewType>("highlight");

    // Mock Data
    const headerData = {
        title: "침착맨의 삼국지 완전 정복 1부 [풀버전]",
        vodUrl: "https://chzzk.naver.com/video/...",
        platform: "chzzk" as const,
        platformChannelUrl: "https://chzzk.naver.com/...",
        channelName: "침착맨",
        channelId: "chzzk_channel_001",
        publishDate: "2024-01-01",
        duration: "04:12:30",
        avgScore: 8.5,
        sentiments: [
            { label: "재미", score: 41.3, color: "text-blue-500" },
            { label: "감동", score: 22.5, color: "text-pink-500" },
            { label: "지루함", score: 5, color: "text-gray-500" },
            { label: "분노", score: 13.4, color: "text-red-500" },
            { label: "흥미", score: 17.8, color: "text-green-500" },
        ]
    };

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

                    <BestMomentsSection data={MOCK_SEGMENTS} />

                ) : (
                    // 🔒 여기서도 한번 더 방어 (데이터 요청 자체를 안 보내도록)
                    !isLocked && <div>
                        인사이트 뷰
                    </div>
                )}
            </main>
        </div>
    );
}
