import { useState } from "react";
import { VodCard, VodCardSkeleton } from "@/features/vod/components/VodCard";
import { VodListToolbar } from "@/features/vod/components/VodListToolbar";
import { BasePagination } from "@/components/ui/base-pagination";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Lock, Unlock, Loader2, AlertCircle, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { useUrlParams } from "@/hooks/use-url-params";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { MyVodData } from "@shared/types/vod";
import { getMyVods, updateVodExposure } from "../api/myVods";
import { AlertDialogHeader, AlertDialogFooter, AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { VOD_ITEMS_PER_PAGE } from "@shared/constants/ui";
import { cn } from "@/lib/utils";
import { VOD_PIPELINE_STATUS } from "@shared/constants/service_codes";

interface Props {
    isOwner: boolean; // MyPage에서 받음
}

export function MyVodTab({ isOwner }: Props) {
    const queryClient = useQueryClient();
    const { query, fromDate, toDate } = useUrlParams();
    const [page, setPage] = useState(1);

    // ✅ 필터: 공개 여부 (ALL | PUBLIC | PRIVATE)
    const [visibilityFilter, setVisibilityFilter] = useState<'ALL' | 'PUBLIC' | 'PRIVATE'>('ALL');

    const { data: vodResponse, isLoading, isFetching } = useQuery({
        queryKey: ['myVods', page, query, visibilityFilter, fromDate, toDate],
        queryFn: () => getMyVods({
            page,
            query,
            visibility: visibilityFilter,
            fromDate,
            toDate
        }),
        placeholderData: (previousData) => previousData, // 페이지 전환 시 깜빡임 방지
    });

    const vods = vodResponse?.data || [];
    const totalPages = vodResponse?.meta.totalPages || 0;

    const [targetVod, setTargetVod] = useState<{
        id: string;
        currentExposed: boolean;
        title: string;
        platform: string;   // 추가
        channelId: string;  // 추가
    } | null>(null);

    // 2. 변경 Mutation
    const { mutate: toggleExposure, isPending: isUpdating } = useMutation({
        mutationFn: (params: { id: string; isExposed: boolean; platform: string; channelId: string }) =>
            updateVodExposure({ // API 함수 호출 형태 변경
                videoNo: params.id,
                isExposed: params.isExposed,
                platform: params.platform,
                channelId: params.channelId
            }),

        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['myVods'] });

            const statusText = variables.isExposed ? "공개" : "비공개";
            toast.success(`${statusText} 상태로 변경되었습니다.`);

            setTargetVod(null); // 다이얼로그 닫기
        },
        onError: () => {
            toast.error("설정 변경에 실패했습니다. 권한을 확인해주세요.");
            setTargetVod(null);
        }
    });

    // 3. 핸들러: 다이얼로그 열기
    const handleInitiateToggle = (vod: MyVodData) => {
        if (!isOwner) return;

        setTargetVod({
            id: vod.videoNo,
            currentExposed: vod.isExposed,
            title: vod.title,
            platform: vod.platform,    // ✅ 데이터 저장
            channelId: vod.channelId   // ✅ 데이터 저장
        });
    };

    // 4. 핸들러: 변경 확정 (API 호출)
    const handleConfirmToggle = () => {
        if (!targetVod) return;
        toggleExposure({
            id: targetVod.id,
            isExposed: !targetVod.currentExposed,
            platform: targetVod.platform,    // ✅ 전달
            channelId: targetVod.channelId   // ✅ 전달
        });
    };

    // 상태 배지 렌더러
    const renderStatusBadge = (status: string) => {
        if (status === VOD_PIPELINE_STATUS.COMPLETED) return null;
        if (status === VOD_PIPELINE_STATUS.FAILED) {
            return <Badge variant="destructive" className="gap-1 h-6"><AlertCircle className="w-3 h-3" /> 분석 불가</Badge>;
        }
        return <Badge variant="secondary" className="gap-1 h-6 bg-blue-100 text-blue-700 hover:bg-blue-100"><Loader2 className="w-3 h-3 animate-spin" /> 분석 중...</Badge>;
    };


    return (
        <div className="space-y-6 pb-8">
            <div className="flex flex-col gap-4">
                <div className="flex flex-col md:flex-row justify-between items-end gap-4">
                    <div className="space-y-1 ps-2">
                        <div className="flex items-center gap-2">
                            <h2 className="text-xl font-bold">내 영상 관리</h2>
                        </div>
                        <p className="text-sm text-muted-foreground">
                            {isOwner
                                ? "영상의 공개 여부를 제어할 수 있습니다."
                                : "채널에 등록된 영상 목록입니다 (읽기 전용)."}
                        </p>
                    </div>
                    <div className="w-full md:w-auto">
                        <VodListToolbar placeholder="영상 제목 검색" />
                    </div>
                </div>

                {/* 필터 탭 */}
                <div className="flex gap-2">
                    {[
                        { value: "ALL", label: "전체" },
                        { value: "PUBLIC", label: "공개됨" },
                        { value: "PRIVATE", label: "비공개" },
                    ].map((f) => (
                        <Button
                            key={f.value}
                            variant={visibilityFilter === f.value ? "default" : "outline"}
                            size="sm"
                            onClick={() => {
                                setVisibilityFilter(f.value as any);
                                setPage(1);
                            }}
                            className={cn(
                                "min-w-[80px] transition-all",
                                visibilityFilter === f.value && "shadow-sm"
                            )}
                        >
                            {f.label}
                        </Button>
                    ))}
                </div>
            </div>

            {/* VOD 리스트 */}
            {isLoading ? (
                // 로딩 스켈레톤
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {Array.from({ length: VOD_ITEMS_PER_PAGE }).map((_, i) => (
                        <VodCardSkeleton key={i} />
                    ))}
                </div>
            ) : vods.length > 0 ? (
                <div className="relative min-h-[400px]">
                    <div className={cn(
                        "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 transition-opacity duration-200",
                        isFetching ? "opacity-50 pointer-events-none" : "opacity-100"
                    )}>
                        {vods.map((item) => (
                            <div key={item.videoNo} className="relative group">
                                {/* 카드 본체 */}
                                <div className={cn(
                                    "transition-all duration-300 rounded-xl overflow-hidden",
                                    (!item.isExposed || item.status !== 'COMPLETED') && "grayscale-[0.5] opacity-80 ring-1 ring-border"
                                )}>
                                    <VodCard data={item} />
                                </div>

                                {/* [좌측 상단] 분석 상태 배지 (최우선 순위) */}
                                <div className="absolute top-12 left-2 z-20 pointer-events-none">
                                    {renderStatusBadge(item.status)}
                                </div>

                                {/* [우측 상단] 공개/비공개 제어 버튼 (Owner Only) */}
                                <div className="absolute top-2 right-2 z-10">
                                    <Button
                                        variant="secondary"
                                        size="sm"
                                        disabled={!isOwner}
                                        className={`h-8 px-3 shadow-sm backdrop-blur-md border transition-all duration-200
                                        ${item.isExposed
                                                ? "bg-white/90 text-green-700 border-green-200 hover:bg-green-50"
                                                : "bg-white/90 text-orange-600 border-orange-200 hover:bg-orange-50"}
                                    `}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleInitiateToggle(item);
                                        }}
                                    >
                                        {item.isExposed ? (
                                            <><Unlock className="h-3.5 w-3.5 mr-1.5" /><span className="text-xs font-bold">Public</span></>
                                        ) : (
                                            <><Lock className="h-3.5 w-3.5 mr-1.5" /><span className="text-xs font-bold">Private</span></>
                                        )}
                                    </Button>
                                </div>

                                {/* 비공개 상태일 때 오버레이 힌트 (선택 사항) */}
                                {!item.isExposed && (
                                    <div className="absolute inset-0 z-0 pointer-events-none bg-black/5 rounded-xl" />
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            ) : (
                <div className="py-24 flex flex-col items-center justify-center border-2 border-dashed rounded-xl bg-secondary/5 text-muted-foreground gap-3">
                    <div className="p-3 bg-background rounded-full shadow-sm">
                        <AlertCircle className="h-6 w-6 opacity-30" />
                    </div>
                    <p>조건에 맞는 영상이 없습니다.</p>
                </div>
            )}

            {totalPages > 1 && (
                <div className="flex justify-center pt-4">
                    <BasePagination
                        total={totalPages}
                        page={page}
                        onChange={(p) => {
                            setPage(p);
                            window.scrollTo({ top: 0, behavior: 'smooth' }); // 페이지 이동 시 상단 스크롤
                        }}
                    />
                </div>
            )}

            {/* 변경 확인 모달 */}
            <AlertDialog open={!!targetVod} onOpenChange={(open) => !open && setTargetVod(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle className="flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-orange-500" />
                            공개 설정 변경
                        </AlertDialogTitle>
                        <AlertDialogDescription asChild>
                            <div className="text-sm text-muted-foreground space-y-3 pt-2">
                                <p>다음 영상의 공개 상태를 변경하시겠습니까?</p>

                                <div className="font-medium text-foreground p-3 bg-secondary/30 rounded-md border border-border/50">
                                    {targetVod?.title}
                                </div>

                                <div className="grid grid-cols-2 gap-4 text-center">
                                    <div className="p-2 rounded border bg-background">
                                        <div className="text-xs text-muted-foreground mb-1">현재 상태</div>
                                        <div className="font-bold">
                                            {targetVod?.currentExposed ? "공개 (Public)" : "비공개 (Private)"}
                                        </div>
                                    </div>
                                    <div className={`p-2 rounded border bg-background ${!targetVod?.currentExposed ? "border-green-200 text-green-700" : "border-orange-200 text-orange-700"}`}>
                                        <div className="text-xs text-muted-foreground mb-1">변경 후</div>
                                        <div className="font-bold">
                                            {!targetVod?.currentExposed ? "공개 (Public)" : "비공개 (Private)"}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel disabled={isUpdating}>취소</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleConfirmToggle}
                            disabled={isUpdating}
                            className={targetVod?.currentExposed
                                ? "bg-orange-600 hover:bg-orange-700"
                                : "bg-green-600 hover:bg-green-700"}
                        >
                            {isUpdating ? "처리 중..." : (targetVod?.currentExposed ? "비공개로 전환" : "공개로 전환")}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
