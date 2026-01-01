// src/react-app/app/routes.tsx
import { createBrowserRouter, Route, createRoutesFromElements, RouterProvider } from "react-router-dom";
import { MainLayout } from "@/components/layout/MainLayout";

// 각 Feature의 Route 컴포넌트 import
import { HomePage } from "@/features/home/routes/HomePage";
import { SearchPage } from "@/features/search/routes/SearchPage";
import { PlatformPage } from "@/features/platform/routes/PlatformPage";
import { ChannelPage } from "@/features/channel/routes/ChannelPage";
// import { AnalysisPage } ...

const router = createBrowserRouter(
    createRoutesFromElements(
        <Route element={<MainLayout />}>
            {/* 1. 홈 */}
            <Route path="/" element={<HomePage />} />

            {/* 2. 플랫폼별 VOD 리스트 (로컬 검색) */}
            <Route path="/platform/:platformId" element={<PlatformPage />} />

            {/* 3. 통합 검색 결과 (헤더 검색 시 이동) */}
            <Route path="/search" element={<SearchPage />} />

            {/* 4. 채널 상세 */}
            <Route path="/channel/:channelId" element={<ChannelPage />} />

            {/* 5. 분석 상세 */}
            <Route path="/analysis/:vodId" element={<div>분석 페이지</div>} />
        </Route>
    )
);

export const AppRoutes = () => {
    return <RouterProvider router={router} />;
};
