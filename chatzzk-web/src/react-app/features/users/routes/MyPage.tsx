import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { useAuthStore } from "@/lib/stores";
import { MyVodTab } from "../components/MyVodTab";
import { MySettingsTab } from "../components/MySettingsTab";
import { MyProfile } from "../components/MyProfile";
import { MyChannelInfoTab } from "../components/MyChannelInfoTab";
import { useSearchParams, Navigate } from "react-router-dom"; // ✅ Navigate 추가
import { USER_ROLE } from "@/types";

export function MyPage() {
    const user = useAuthStore((state) => state.user);
    const isEditor = user?.role === USER_ROLE.EDITOR; // 'editor' 문자열 대신 Enum 사용 권장

    const [searchParams, setSearchParams] = useSearchParams();

    // 1. 현재 탭 가져오기 (없으면 기본값 'vods')
    const currentTab = searchParams.get("tab") || "vods";

    const handleTabChange = (value: string) => {
        setSearchParams({ tab: value });
    };

    // 2. [보안 및 리다이렉트] 편집자가 'settings' 탭에 접근 시
    // useEffect 대신 <Navigate /> 컴포넌트를 리턴하여 즉시 이동시킵니다.
    // replace={true} 옵션을 주어 뒤로가기 시 다시 잘못된 탭으로 오지 않게 합니다.
    if (isEditor && currentTab === "settings") {
        return <Navigate to="?tab=vods" replace />;
    }

    // 유저 정보가 로딩 안됐을 때 (로그인 페이지 등으로 튕겨내는 로직은 ProtectedRoute에 있다고 가정)
    if (!user) return null;

    return (
        <div className="container mx-auto py-10 max-w-5xl space-y-8">
            {/* 상단 프로필 영역 */}
            <MyProfile user={user} />

            <Separator />

            {/* 탭 영역 */}
            <Tabs
                value={currentTab}
                onValueChange={handleTabChange}
                className="w-full"
            >
                <TabsList className={`grid w-full max-w-[600px] ${isEditor ? "grid-cols-2" : "grid-cols-3"}`}>
                    <TabsTrigger value="vods">영상 관리</TabsTrigger>
                    <TabsTrigger value="info">채널 정보</TabsTrigger>

                    {!isEditor && (
                        <TabsTrigger value="settings">채널 설정</TabsTrigger>
                    )}
                </TabsList>

                <TabsContent value="vods" className="mt-6">
                    <MyVodTab />
                </TabsContent>

                <TabsContent value="info" className="mt-6">
                    <MyChannelInfoTab />
                </TabsContent>

                {!isEditor && (
                    <TabsContent value="settings" className="mt-6">
                        <MySettingsTab />
                    </TabsContent>
                )}
            </Tabs>
        </div>
    );
}
