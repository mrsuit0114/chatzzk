import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { useAuthStore } from "@/stores/auth.store";
import { MyVodTab } from "../components/MyVodTab";
import { MyProfile } from "../components/MyProfile";
import { MyChannelInfoTab } from "../components/MyChannelInfoTab";
import { useSearchParams, Navigate } from "react-router-dom";
import { CONTACT_EMAIL, USER_ROLE } from "@shared/constants/service_codes";
import { useQuery } from "@tanstack/react-query";
import { getMyChannel } from "../api/myChannel";
import { MySettingsTab } from "../components/MySettingsTab";
import { AlertTriangle } from "lucide-react";


export function MyPage() {
    // 1. Store에서 동기화된 유저 프로필 가져오기
    const { userProfile } = useAuthStore();
    const [searchParams, setSearchParams] = useSearchParams();

    const canFetchChannel = !!userProfile && (userProfile.role === USER_ROLE.OWNER || userProfile.role === USER_ROLE.EDITOR);

    const { data: myChannelRes, isLoading } = useQuery({
        queryKey: ['myChannel', userProfile?.id],
        queryFn: getMyChannel,
        enabled: canFetchChannel, // 조건 충족 시에만 API 호출
    });

    // 2. 권한 체크 로직
    // ProtectedRoute를 통과했지만, 타입 안전성을 위해 null 체크
    if (!userProfile) return null;

    if (userProfile.role === USER_ROLE.ADMIN) {
        return <Navigate to="/admin" replace />;
    }

    // ✅ [추가] USER 처리: 채널 권한이 없는 경우 안내 메시지
    if (userProfile.role === USER_ROLE.USER) {
        return (
            <div className="container mx-auto py-32 flex flex-col items-center text-center space-y-4">
                <div className="p-4 bg-red-50 text-red-600 rounded-full">
                    <AlertTriangle className="h-10 w-10" />
                </div>
                <h2 className="text-2xl font-bold">접근 권한이 없습니다.</h2>
                <p className="text-muted-foreground max-w-md">
                    일반 회원은 채널 관리 페이지를 이용할 수 없습니다.<br />
                    스트리머 등록은 {CONTACT_EMAIL}에 문의바랍니다.
                </p>
            </div>
        );
    }

    const myChannel = myChannelRes?.data;
    const isOwner = userProfile.role === USER_ROLE.OWNER;

    // 탭 관련 로직
    const MY_PAGE_TABS = {
        VODS: "vods",
        INFO: "info",
        SETTINGS: "settings",
    } as const;


    // 3. 탭 상태 관리
    const currentTab = searchParams.get("tab") || MY_PAGE_TABS.VODS;

    const handleTabChange = (value: string) => {
        setSearchParams({ tab: value });
    };

    if (isLoading) return <div className="container mx-auto py-20 text-center">로딩 중...</div>;

    if (!myChannel) {
        return (
            <div className="container mx-auto py-20 text-center space-y-4">
                <h2 className="text-2xl font-bold">채널 정보를 불러올 수 없습니다.</h2>
                <p className="text-muted-foreground">
                    연결된 채널이 없거나 일시적인 오류일 수 있습니다.
                </p>
            </div>
        )
    }

    return (
        <div className="container mx-auto">
            {/* ✅ 3단 레이아웃 적용 (광고 공간 확보) */}
            <div className="flex justify-center gap-6">

                {/* [좌측 광고] - 2xl 이상에서 노출 */}
                <aside className="hidden 2xl:block w-[160px] shrink-0">
                    <div className="sticky top-24 w-full h-[600px] bg-muted/30 border border-dashed border-muted-foreground/20 rounded-lg flex items-center justify-center text-xs text-muted-foreground">
                        Advertisement(Left)
                    </div>
                </aside>

                {/* [메인 콘텐츠] */}
                <main className="flex-1 w-full max-w-5xl space-y-8">
                    {/* 상단 프로필 영역 */}
                    <MyProfile user={userProfile} channel={myChannel} />

                    <Separator />

                    {/* 탭 영역 */}
                    <Tabs
                        value={currentTab}
                        onValueChange={handleTabChange}
                        className="w-full"
                    >
                        {/* 탭 리스트 디자인 폴리싱 (배경색 추가) */}
                        <TabsList className="grid w-full grid-cols-3 h-12 items-stretch p-1 bg-muted/50">
                            <TabsTrigger value={MY_PAGE_TABS.VODS}>영상 관리</TabsTrigger>
                            <TabsTrigger value={MY_PAGE_TABS.INFO}>채널 정보</TabsTrigger>
                            <TabsTrigger value={MY_PAGE_TABS.SETTINGS}>채널 설정</TabsTrigger>
                        </TabsList>

                        <div className="mt-6">
                            <TabsContent value={MY_PAGE_TABS.VODS}>
                                <MyVodTab isOwner={isOwner} />
                            </TabsContent>

                            <TabsContent value={MY_PAGE_TABS.INFO}>
                                <MyChannelInfoTab channel={myChannel} isOwner={isOwner} />
                            </TabsContent>

                            <TabsContent value={MY_PAGE_TABS.SETTINGS}>
                                <MySettingsTab channel={myChannel} isOwner={isOwner} />
                            </TabsContent>
                        </div>
                    </Tabs>
                </main>

                {/* [우측 광고] - 2xl 이상에서 노출 */}
                <aside className="hidden 2xl:block w-[160px] shrink-0">
                    <div className="sticky top-24 w-full h-[600px] bg-muted/30 border border-dashed border-muted-foreground/20 rounded-lg flex items-center justify-center text-xs text-muted-foreground">
                        Advertisement(Right)
                    </div>
                </aside>

            </div>
        </div>
    );
}
