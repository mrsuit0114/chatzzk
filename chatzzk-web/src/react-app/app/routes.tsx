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

const router = createBrowserRouter(
    createRoutesFromElements(
        <>
            <Route element={<MainLayout />}>
                {/* 1. 홈 */}
                <Route path="/" element={<HomePage />} />
                <Route path="/:platformId" element={<PlatformPage />} />
                <Route path="/search" element={<SearchPage />} />
                <Route path="/:platformId/channel/:channelId" element={<ChannelPage />} />
                <Route path="/:platformId/analysis/:videoNo" element={<VodAnalysisPage />} />
                <Route element={<ProtectedRoute />}>
                    {/* 이 안에 있는 경로는 로그인해야만 접근 가능 */}
                    <Route path="/mypage" element={<MyPage />} />
                </Route>
            </Route>

            <Route path="/login" element={<LoginPage />} />
        </>
    )
);

export const AppRoutes = () => {
    return <RouterProvider router={router} />;
};
