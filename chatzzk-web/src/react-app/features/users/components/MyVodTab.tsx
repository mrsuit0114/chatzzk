import { useEffect, useState } from "react";
import { VodCard } from "@/features/vod/components/VodCard";
import { VodListToolbar } from "@/features/vod/components/VodListToolbar";
import { BasePagination } from "@/components/ui/base-pagination";
import { MOCK_VOD_DATA } from "@/features/vod/api/mock";
import { Button } from "@/components/ui/button";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Eye, EyeOff, Lock, Unlock, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { useAuthStore } from "@/lib/stores";
import { USER_ROLE } from "@/types";
import { useUrlParams } from "@/lib/hooks";

const ITEMS_PER_PAGE = 8; // 페이지 당 8개

const INITIAL_DATA = MOCK_VOD_DATA.map((item, idx) => ({
    ...item,
    isPublic: idx % 3 !== 0,
}));

export function MyVodTab() {
    const [filter, setFilter] = useState<"all" | "public" | "private">("all");

    // 권한 체크
    const user = useAuthStore((state) => state.user);
    const isEditor = user?.role === USER_ROLE.EDITOR;
    const [vods, setVods] = useState(INITIAL_DATA);
    const { query } = useUrlParams();

    const [page, setPage] = useState(1);

    // ✅ 다이얼로그 상태 관리 (어떤 VOD를 변경하려고 하는지 저장)
    const [targetVod, setTargetVod] = useState<{ id: number; currentStatus: boolean; title: string } | null>(null);

    const filteredVods = vods.filter((item) => {
        // A. 공개/비공개 탭 필터
        if (filter === "public" && !item.isPublic) return false;
        if (filter === "private" && item.isPublic) return false;

        // B. 검색어 필터
        if (query) {
            const lowerQuery = query.toLowerCase();
            const matchTitle = item.title.toLowerCase().includes(lowerQuery);
            if (!matchTitle) return false;
        }

        return true;
    });

    useEffect(() => {
        setPage(1);
    }, [filter, query]);

    const totalCount = filteredVods.length;
    const totalPages = Math.ceil(totalCount / ITEMS_PER_PAGE);
    const safePage = (totalPages > 0 && page > totalPages) ? totalPages : page;

    const startIndex = (safePage - 1) * ITEMS_PER_PAGE;
    const currentPageItems = filteredVods.slice(startIndex, startIndex + ITEMS_PER_PAGE);

    // 1️⃣ [Trigger] 버튼 클릭 시 다이얼로그 열기
    const handleInitiateToggle = (vodId: number, currentStatus: boolean, title: string) => {
        if (isEditor) return;
        setTargetVod({ id: vodId, currentStatus, title });
    };

    // 2️⃣ [Action] 다이얼로그에서 확인 눌렀을 때 실행되는 실제 로직
    const handleConfirmToggle = () => {
        if (!targetVod) return;

        const { id, currentStatus, title } = targetVod;
        const nextStatus = !currentStatus;

        // Optimistic Update
        setVods((prevVods) =>
            prevVods.map((vod) =>
                vod.vodId === id ? { ...vod, isPublic: nextStatus } : vod
            )
        );

        const isRemovedFromList = filter !== "all";

        toast.success(nextStatus ? "공개로 전환되었습니다." : "비공개로 전환되었습니다.", {
            description: isRemovedFromList
                ? "현재 목록 필터와 일치하지 않아 목록에서 제외되었습니다."
                : title,
            icon: nextStatus ? <Unlock className="h-4 w-4 text-green-500" /> : <Lock className="h-4 w-4 text-orange-500" />,
            duration: isRemovedFromList ? 4000 : 2000,
        });

        // 처리 후 다이얼로그 닫기
        setTargetVod(null);
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-4">
                <div className="flex flex-col md:flex-row justify-between items-end gap-4">
                    <div>
                        <h2 className="text-xl font-bold">내 영상 관리</h2>
                        <p className="text-sm text-muted-foreground">
                            {isEditor ? "편집자 권한으로 영상을 관리합니다 (공개 설정 변경 불가)." : "영상의 공개 범위를 설정하고 관리합니다."}
                        </p>
                    </div>
                    <div className="w-full md:w-auto">
                        <VodListToolbar placeholder="내 영상 검색" />
                    </div>
                </div>

                <div className="flex gap-2">
                    {(["all", "public", "private"] as const).map((type) => (
                        <Button
                            key={type}
                            variant={filter === type ? "default" : "outline"}
                            size="sm"
                            onClick={() => setFilter(type)}
                            className="capitalize"
                        >
                            {type === "all" ? "전체" : type === "public" ? "공개됨" : "비공개"}
                        </Button>
                    ))}
                </div>
            </div>

            {currentPageItems.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {currentPageItems.map((item) => (
                        <div key={item.vodId} className="relative group">

                            {/* VOD 카드 */}
                            <div className={`transition-opacity duration-200 ${!item.isPublic ? "opacity-60 grayscale" : ""}`}>
                                <VodCard data={item} />
                            </div>

                            {/* 공개/비공개 제어 버튼 */}
                            <div className="absolute top-2 right-2 z-10">
                                <Button
                                    variant="secondary"
                                    size="sm"
                                    disabled={isEditor}
                                    className={`h-8 px-2 shadow-sm backdrop-blur-md bg-background/80 hover:bg-background border transition-colors ${item.isPublic ? "text-green-600 border-green-200" : "text-orange-600 border-orange-200"
                                        }`}
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        // 바로 변경하지 않고 확인 요청
                                        handleInitiateToggle(item.vodId, item.isPublic, item.title);
                                    }}
                                >
                                    {item.isPublic ? (
                                        <>
                                            <Unlock className="h-4 w-4 mr-1.5" />
                                            <span className="text-xs font-semibold">Public</span>
                                        </>
                                    ) : (
                                        <>
                                            <Lock className="h-4 w-4 mr-1.5" />
                                            <span className="text-xs font-semibold">Private</span>
                                        </>
                                    )}
                                </Button>
                            </div>

                        </div>
                    ))}
                </div>
            ) : (
                <div className="py-20 text-center border rounded-lg bg-secondary/10 text-muted-foreground">
                    검색 결과가 없습니다.
                </div>
            )}

            {totalPages > 1 && (
                <BasePagination
                    total={totalPages}
                    page={safePage}
                    onChange={(p) => setPage(p)}
                />
            )}

            {/* ✅ 변경 확인 다이얼로그 (AlertDialog) */}
            <AlertDialog open={!!targetVod} onOpenChange={(open) => !open && setTargetVod(null)}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle className="flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-orange-500" />
                            공개 설정 변경
                        </AlertDialogTitle>
                        <AlertDialogDescription>
                            다음 영상의 공개 설정을 변경하시겠습니까?
                            <br />
                            <span className="font-semibold text-foreground block mt-2 p-2 bg-muted rounded-md">
                                {targetVod?.title}
                            </span>
                            <div className="mt-2 text-sm">
                                현재 상태: <span className="font-bold">{targetVod?.currentStatus ? "공개 (Public)" : "비공개 (Private)"}</span>
                                <br />
                                변경 후: <span className={`font-bold ${!targetVod?.currentStatus ? "text-green-600" : "text-orange-600"}`}>
                                    {!targetVod?.currentStatus ? "공개 (Public)" : "비공개 (Private)"}
                                </span>
                            </div>
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>취소</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleConfirmToggle}
                            className={targetVod?.currentStatus ? "bg-orange-600 hover:bg-orange-700" : "bg-green-600 hover:bg-green-700"}
                        >
                            {targetVod?.currentStatus ? "비공개로 전환" : "공개로 전환"}
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
