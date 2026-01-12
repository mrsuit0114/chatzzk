// src/react-app/app/routes.tsx
import { createBrowserRouter, Route, createRoutesFromElements, RouterProvider } from "react-router-dom";
import { MainLayout } from "@/components/layout/MainLayout";

// 각 Feature의 Route 컴포넌트 import
import { HomePage } from "@/features/home/routes/HomePage";
import { SearchPage } from "@/features/search/routes/SearchPage";
import { PlatformPage } from "@/features/platform/routes/PlatformPage";
import { ChannelPage } from "@/features/channel/routes/ChannelPage";
// import { AnalysisPage } ...

import { LoginPage } from "@/features/auth/routes/LoginPage";
import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute";
import { MyPage } from "@/features/users/routes/MyPage";
import { VodAnalysisPage } from "@/features/analysis/routes/VodAnalysisPage";
import { AdminGuard } from "@/features/admin/components/AdminGuard";

const router = createBrowserRouter(
    createRoutesFromElements(
        <>
            {/* ✅ Main Layout (헤더/사이드바가 필요한 페이지들) */}
            <Route element={<MainLayout />}>

                {/* 1. [공개/고정 경로] 가장 먼저 매칭되어야 하는 페이지들 */}
                <Route path="/" element={<HomePage />} />
                <Route path="/search" element={<SearchPage />} />

                {/* 2. [로그인 필수 경로] ProtectedRoute로 감싸기 */}
                <Route element={<ProtectedRoute />}>
                    <Route path="/mypage" element={<MyPage />} />

                    {/* 3. [관리자 전용 경로] 로그인 필수 + 관리자 권한 필수 (이중 보안) */}
                    <Route path="/admin" element={
                        <AdminGuard>
                            {/* 추후 AdminLayout 등을 여기에 넣을 수도 있음 */}
                            <div>Admin Page</div>
                        </AdminGuard>
                    } />
                </Route>

                {/* 4. [동적 경로] 가장 나중에 매칭 (위에서 매칭 안 된 경우 여기로) */}
                <Route path="/:platformId" element={<PlatformPage />} />
                <Route path="/:platformId/channel/:channelId" element={<ChannelPage />} />
                <Route path="/:platformId/analysis/:videoNo" element={<VodAnalysisPage />} />
            </Route>

            {/* ✅ Auth Layout (헤더/사이드바 없는 페이지) */}
            <Route path="/login" element={<LoginPage />} />

            {/* ✅ 404 처리 (맨 마지막에 배치) */}
            <Route path="*" element={<div className="p-10 text-center">페이지를 찾을 수 없습니다.</div>} />
        </>
    )
);

export const AppRoutes = () => {
    return <RouterProvider router={router} />;
};
