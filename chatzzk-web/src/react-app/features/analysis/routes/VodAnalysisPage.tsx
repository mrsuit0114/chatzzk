import { useEffect, useMemo, useState } from "react";
import { HighlightView } from "../components/highlight";
import { VodAnalysisHeader } from "../components/header";
import { InsightView } from "../components/insight/InsightView";
import { VIEW_TYPE, ViewType } from "../constants";

import { Lock, AlertTriangle, Loader2 } from "lucide-react";
import { useAnalysisData } from "../hooks/use-analysis-data";
import { transformClipsData, transformHighlightData, transformRawToHeaderData } from "../utils";
import { InsightViewData } from "../types";
import { useParams } from "react-router-dom";
import { useAuthStore } from "@/stores";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export function VodAnalysisPage() {
    const { platformId, videoNo } = useParams<{ platformId: string; videoNo: string }>();
    const queryClient = useQueryClient();
    const { user } = useAuthStore();
    // 1. Hook을 통해 R2 데이터 Fetching
    const { data: rawData, isLoading, isError } = useAnalysisData();

    const [currentView, setCurrentView] = useState<ViewType>(VIEW_TYPE.HIGHLIGHT);

    useEffect(() => {
        if (platformId && videoNo) {
            queryClient.invalidateQueries({
                queryKey: ['vodAnalysis', platformId, videoNo]
            });
        }
    }, [user, queryClient, platformId, videoNo]);

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

    if (isError || !rawData) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background p-4">
                <div className="flex flex-col items-center gap-4 text-center max-w-md p-8 border rounded-xl bg-card shadow-sm">
                    <div className="p-4 bg-destructive/10 text-destructive rounded-full">
                        <AlertTriangle className="h-8 w-8" />
                    </div>
                    <div className="space-y-2">
                        <h2 className="text-xl font-bold">분석 데이터를 불러올 수 없습니다.</h2>
                        <p className="text-muted-foreground text-sm leading-relaxed">
                            권한이 없거나 분석이 완료되지 않았습니다.
                        </p>
                    </div>
                    <Button variant="outline" onClick={() => window.history.back()}>
                        이전 페이지로 돌아가기
                    </Button>
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
        if (view === VIEW_TYPE.INSIGHT && isInsightLocked) {
            toast.warning("분석 결과 공개 대기 중입니다.", {
                description: "채널 설정에 따라 일정 시간 후 공개됩니다.",
                icon: <Lock className="h-4 w-4" />
            });
            return;
        }
        setCurrentView(view);
    };

    return (
        <div className="min-h-screen bg-background pb-6">
            <div className="container mx-auto">
                {/* ✅ 3단 레이아웃 (차트 공간 확보를 위해 max-w-7xl 적용) */}
                <div className="flex justify-center gap-6">

                    {/* [Left Advertisement] - 2xl 이상에서만 표시 */}
                    <aside className="hidden 2xl:block w-[180px] shrink-0">
                        <div className="sticky top-24 w-full h-[600px] bg-muted/30 border border-dashed border-muted-foreground/20 rounded-lg flex items-center justify-center text-xs text-muted-foreground">
                            Advertisement (Left)
                        </div>
                    </aside>

                    {/* [Main Content] */}
                    <main className="flex-1 w-full max-w-7xl min-w-0">

                        {/* 헤더 (제목, 통계, 뷰 스위처) */}
                        <VodAnalysisHeader
                            data={headerData}
                            currentView={currentView}
                            onViewChange={handleViewChange}
                            isInsightLocked={isInsightLocked}
                        />

                        {/* 컨텐츠 뷰 */}
                        <div className="min-h-[500px] animate-in fade-in duration-500 slide-in-from-bottom-2">
                            {currentView === VIEW_TYPE.HIGHLIGHT ? (
                                <HighlightView
                                    segments={highlightData.segments}
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
                        </div>
                    </main>

                    {/* [Right Advertisement] - 2xl 이상에서만 표시 */}
                    <aside className="hidden 2xl:block w-[180px] shrink-0">
                        <div className="sticky top-24 w-full h-[600px] bg-muted/30 border border-dashed border-muted-foreground/20 rounded-lg flex items-center justify-center text-xs text-muted-foreground">
                            Advertisement (Right)
                        </div>
                    </aside>

                </div>
            </div>
        </div>
    );
}
