import { Outlet } from "react-router-dom";
import { Header } from "./Header";

export function MainLayout() {
    return (
        <div className="min-h-screen bg-background font-sans antialiased">
            {/* 1. 모든 페이지 공통 헤더 */}
            <Header />

            {/* 2. 각 페이지의 콘텐츠가 들어갈 자리 */}
            <main className="flex-1">
                <Outlet />
            </main>
        </div>
    );
}
