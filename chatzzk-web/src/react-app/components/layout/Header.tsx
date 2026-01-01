import { Link } from "react-router-dom";
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

export function Header() {
    // 나중엔 로그인 상태(AuthContext)를 가져와서 분기 처리
    const isLoggedIn = true;

    return (
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container mx-auto flex h-14 items-center justify-between">
                {/* 1. 서비스 로고 (클릭 시 홈/대시보드로 이동하며 상태 초기화) */}
                <div className="flex items-center">
                    <Link to="/" className="mr-6 flex items-center space-x-2">
                        <span className="text-xl font-bold whitespace-nowrap">Stream Analytics</span>
                    </Link>
                </div>

                {/* 2. [추가됨] 중앙 검색바 영역 */}
                {/* flex-1을 주어 남은 공간을 차지하게 하고, max-w로 너무 넓어지지 않게 제한 */}
                <div className="flex-1 flex justify-center max-w-2xl">
                    <GlobalSearchBar />
                </div>

                {/* 2. 우측 사용자 메뉴 */}
                <div className="flex items-center gap-2">
                    {isLoggedIn ? (
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="rounded-full">
                                    <User className="h-5 w-5" />
                                    <span className="sr-only">사용자 메뉴</span>
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                <DropdownMenuLabel>내 계정</DropdownMenuLabel>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem asChild>
                                    <Link to="/mypage" className="cursor-pointer">
                                        <Settings className="mr-2 h-4 w-4" />
                                        <span>마이페이지</span>
                                    </Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem className="text-red-600 cursor-pointer">
                                    <LogOut className="mr-2 h-4 w-4" />
                                    <span>로그아웃</span>
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    ) : (
                        <Button asChild variant="default" size="sm">
                            <Link to="/login">로그인</Link>
                        </Button>
                    )}
                </div>
            </div>
        </header>
    );
}
