// src/react-app/app/routes.tsx
import { createBrowserRouter, Route, createRoutesFromElements, RouterProvider, Navigate } from "react-router-dom";
import { MainLayout } from "@/components/layout/MainLayout";

import { HomePage } from "@/features/home/routes/HomePage";
import { SearchPage } from "@/features/search/routes/SearchPage";
import { PlatformPage } from "@/features/platform/routes/PlatformPage";
import { ChannelPage } from "@/features/channel/routes/ChannelPage";
import { LoginPage } from "@/features/auth/routes/LoginPage";
import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute";
import { MyPage } from "@/features/users/routes/MyPage";
import { VodAnalysisPage } from "@/features/analysis/routes/VodAnalysisPage";
import { AdminGuard } from "@/features/admin/AdminGuard";
import { AdminLayout } from "@/features/admin/layout/AdminLayout";
import { ChannelProvisionPage } from "@/features/admin/routes/ChannelProvisionPage";

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
                </Route>

                {/* 4. [동적 경로] 가장 나중에 매칭 (위에서 매칭 안 된 경우 여기로) */}
                <Route path="/:platformId" element={<PlatformPage />} />
                <Route path="/:platformId/channel/:channelId" element={<ChannelPage />} />
                <Route path="/:platformId/analysis/:videoNo" element={<VodAnalysisPage />} />
                <Route path="/admin" element={
                    <AdminGuard>   {/* 2차: 권한 체크 */}
                        <AdminLayout /> {/* 3차: 레이아웃 렌더링 */}
                    </AdminGuard>
                }>
                    {/* /admin 접속 시 자동으로 provision으로 이동 */}
                    <Route index element={<Navigate to="provision" replace />} />

                    {/* /admin/provision 경로 매핑 */}
                    <Route path="provision" element={<ChannelProvisionPage />} />

                    {/* 추후 추가될 경로들 */}
                    {/* <Route path="channels" element={<ChannelListPage />} /> */}
                </Route>
            </Route>


            {/* ✅ Auth Layout (헤더/사이드바 없는 페이지) */}
            <Route path="/login" element={<LoginPage />} />

            {/* ✅ 404 처리 (맨 마지막에 배치) */}
            <Route path="*" element={<Navigate to="/" replace />} />
        </>
    )
);

export const AppRoutes = () => {
    return <RouterProvider router={router} />;
};
