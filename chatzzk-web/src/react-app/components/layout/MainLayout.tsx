import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { Footer } from "./Footer"; // 추가

export function MainLayout() {
    return (
        // min-h-screen: 전체 화면 높이 확보
        // flex flex-col: 세로 배치
        <div className="min-h-screen flex flex-col bg-background font-sans antialiased">

            {/* 상단 헤더 */}
            <Header />

            {/* flex-1: 남은 공간을 모두 차지함
               -> 콘텐츠가 적어도 Footer를 바닥으로 밀어냄
            */}
            <main className="flex-1">
                <Outlet />
            </main>

            {/* 하단 푸터 */}
            <Footer />
        </div>
    );
}
