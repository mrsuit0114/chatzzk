import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { User, LogOut, Settings } from "lucide-react";
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

export function Header() {
    const navigate = useNavigate();
    const location = useLocation();
    // ✅ 전역 로그인 상태 및 액션 구독
    const { isAuthenticated, user, logout } = useAuthStore();

    const handleLogout = () => {
        logout();
        navigate("/"); // 로그아웃 후 홈으로 리다이렉트
    };

    return (
        <header className="sticky top-0 z-50 w-full border-b bg-background">
            <div className="container mx-auto flex h-14 items-center justify-between gap-4">

                {/* 1. 로고 */}
                <div className="flex items-center">
                    <Link to="/" className="mr-6 flex items-center space-x-2">
                        <span className="text-xl font-bold whitespace-nowrap">Stream Analytics</span>
                    </Link>
                </div>

                {/* 2. 검색바 */}
                <div className="flex-1 flex justify-center max-w-2xl">
                    <GlobalSearchBar />
                </div>

                {/* 3. 우측 사용자 메뉴 (동적 렌더링) */}
                <div className="flex items-center gap-2">
                    {isAuthenticated ? (
                        // ✅ 로그인 상태: 드롭다운 메뉴 표시
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="rounded-full">
                                    <User className="h-5 w-5" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                <DropdownMenuLabel>
                                    {user?.id || "사용자"}님
                                </DropdownMenuLabel>
                                <DropdownMenuSeparator />
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
