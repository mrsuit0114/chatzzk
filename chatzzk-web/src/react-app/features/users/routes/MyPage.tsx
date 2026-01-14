import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { useAuthStore } from "@/stores/auth.store";
import { MyVodTab } from "../components/MyVodTab";
import { MyProfile } from "../components/MyProfile";
import { MyChannelInfoTab } from "../components/MyChannelInfoTab";
import { useSearchParams, Navigate } from "react-router-dom";
import { USER_ROLE } from "@shared/constants/service_codes";
import { useQuery } from "@tanstack/react-query";
import { getMyChannel } from "../api/myChannel";
import { MySettingsTab } from "../components/MySettingsTab";


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
            <div className="container mx-auto py-20 text-center space-y-4">
                <h2 className="text-2xl font-bold">접근 권한이 없습니다.</h2>
                <p className="text-muted-foreground">
                    일반 회원은 채널 관리 페이지를 이용할 수 없습니다.<br />
                    스트리머 등록 문의는 고객센터를 이용해 주세요.
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
                    채널이 존재하지 않거나 접근 권한이 없습니다.<br />
                    문제가 지속될 경우 고객센터로 문의해 주세요.
                </p>
            </div>
        )
    }

    return (
        <div className="container mx-auto max-w-5xl">
            {/* 상단 프로필 영역 */}
            <MyProfile user={userProfile} channel={myChannel} />

            <Separator />

            {/* 탭 영역 */}
            <Tabs
                value={currentTab}
                onValueChange={handleTabChange}
                className="w-full mt-2"
            >
                <TabsList className={`grid w-full grid-cols-3`}>
                    <TabsTrigger value={MY_PAGE_TABS.VODS}>영상 관리</TabsTrigger>
                    <TabsTrigger value={MY_PAGE_TABS.INFO}>채널 정보</TabsTrigger>
                    <TabsTrigger value={MY_PAGE_TABS.SETTINGS}>채널 설정</TabsTrigger>
                </TabsList>

                <TabsContent value={MY_PAGE_TABS.VODS} className="mt-6">
                    <MyVodTab isOwner={isOwner} />
                </TabsContent>

                <TabsContent value={MY_PAGE_TABS.INFO} className="mt-6">
                    <MyChannelInfoTab channel={myChannel} isOwner={isOwner} />
                </TabsContent>

                <TabsContent value={MY_PAGE_TABS.SETTINGS} className="mt-6">
                    <MySettingsTab channel={myChannel} isOwner={isOwner} />
                </TabsContent>

            </Tabs>

        </div>
    );
}
