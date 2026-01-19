import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { User, LogOut, Settings, ShieldCheck } from "lucide-react";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { GlobalSearchBar } from "@/features/search/components/GlobalSearchBar";
import { useAuthStore } from "@/stores/auth.store";
import { supabase } from "@/lib/supabase";
import { USER_ROLE } from "@shared/constants/service_codes";

export function Header() {
    const navigate = useNavigate();
    const location = useLocation();
    const { userProfile, clearSession } = useAuthStore();

    // ✅ 관리자 여부 체크 (옵션)
    const isAdmin = userProfile?.role === USER_ROLE.ADMIN;

    const handleLogout = async () => {
        // 1. Supabase 서버에 로그아웃 요청 (필수!)
        await supabase.auth.signOut();

        // 2. 클라이언트 상태 비우기
        clearSession();

        // 3. 홈으로 이동
        navigate("/");
    };

    return (
        <header className="sticky top-0 z-50 w-full border-b bg-background">
            <div className="container mx-auto flex h-14 items-center justify-between gap-4">

                {/* 1. 로고 */}
                <div className="flex items-center">
                    <Link to="/" className="mr-6 flex items-center ps-2 space-x-2">
                        <span className="text-xl font-bold whitespace-nowrap">CHATZZK</span>
                    </Link>
                </div>

                {/* 2. 검색바 */}
                <div className="flex-1 flex justify-center max-w-2xl">
                    <GlobalSearchBar />
                </div>

                {/* 3. 우측 사용자 메뉴 (동적 렌더링) */}
                <div className="flex items-center gap-2">
                    {userProfile ? (
                        // ✅ 로그인 상태: 드롭다운 메뉴 표시
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="rounded-full">
                                    <User className="h-5 w-5" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                <DropdownMenuLabel>
                                    {userProfile?.userName || "사용자"}님
                                </DropdownMenuLabel>
                                <DropdownMenuSeparator />
                                {isAdmin && (
                                    <>
                                        <DropdownMenuItem asChild>
                                            <Link to="/admin" className="text-amber-600 cursor-pointer">
                                                <ShieldCheck className="mr-2 h-4 w-4" />
                                                <span>관리자 페이지</span>
                                            </Link>
                                        </DropdownMenuItem>
                                        <DropdownMenuSeparator />
                                    </>
                                )}
                                <DropdownMenuItem asChild>
                                    <Link to="/mypage" className="cursor-pointer">
                                        <Settings className="mr-2 h-4 w-4" />
                                        <span>마이페이지</span>
                                    </Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={handleLogout} className="text-red-600 cursor-pointer">
                                    <LogOut className="mr-2 h-4 w-4" />
                                    <span>로그아웃</span>
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    ) : (
                        // ✅ 로그아웃 상태: 로그인 버튼 표시
                        <Button asChild variant="default" size="sm">
                            <Link to="/login" state={{ from: location }}>
                                로그인
                            </Link>
                        </Button>
                    )}
                </div>
            </div>
        </header>
    );
}
