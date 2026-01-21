// src/react-app/app/routes.tsx
import { createBrowserRouter, Route, createRoutesFromElements, RouterProvider, Navigate } from "react-router-dom";
import { lazy, Suspense } from "react"

import { MainLayout } from "@/components/layout/MainLayout";
import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute";
import { AdminGuard } from "@/features/admin/AdminGuard";
import { AdminLayout } from "@/features/admin/layout/AdminLayout";
import { Loader2 } from "lucide-react";

const HomePage = lazy(() => import("@/features/home/routes/HomePage").then(m => ({ default: m.HomePage })));
const SearchPage = lazy(() => import("@/features/search/routes/SearchPage").then(m => ({ default: m.SearchPage })));
const PlatformPage = lazy(() => import("@/features/platform/routes/PlatformPage").then(m => ({ default: m.PlatformPage })));
const ChannelPage = lazy(() => import("@/features/channel/routes/ChannelPage").then(m => ({ default: m.ChannelPage })));
const LoginPage = lazy(() => import("@/features/auth/routes/LoginPage").then(m => ({ default: m.LoginPage })));
const MyPage = lazy(() => import("@/features/users/routes/MyPage").then(m => ({ default: m.MyPage })));
const VodAnalysisPage = lazy(() => import("@/features/analysis/routes/VodAnalysisPage").then(m => ({ default: m.VodAnalysisPage })));
const ChannelProvisionPage = lazy(() => import("@/features/admin/routes/ChannelProvisionPage").then(m => ({ default: m.ChannelProvisionPage })));

const router = createBrowserRouter(
    createRoutesFromElements(
        <>
            {/* ✅ Main Layout (헤더/사이드바가 필요한 페이지들) */}
            <Route element={<MainLayout />}>

                {/* 1. [공개/고정 경로] 가장 먼저 매칭되어야 하는 페이지들 */}
                <Route path="/" element={
                    <Suspense fallback={null}><HomePage /></Suspense>
                } />
                <Route path="/search" element={
                    <Suspense fallback={null}><SearchPage /></Suspense>
                } />

                {/* 2. [로그인 필수 경로] ProtectedRoute로 감싸기 */}
                <Route element={<ProtectedRoute />}>
                    <Route path="/mypage" element={
                        <Suspense fallback={null}><MyPage /></Suspense>
                    } />
                </Route>

                {/* 4. [동적 경로] 가장 나중에 매칭 (위에서 매칭 안 된 경우 여기로) */}
                <Route path="/:platformId" element={
                    <Suspense fallback={null}><PlatformPage /></Suspense>
                } />
                <Route path="/:platformId/channel/:channelId" element={
                    <Suspense fallback={null}><ChannelPage /></Suspense>
                } />
                <Route
                    path="/:platformId/analysis/:videoNo"
                    element={
                        <Suspense fallback={
                            <div className="min-h-screen flex items-center justify-center">
                                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                            </div>
                        }>
                            <VodAnalysisPage />
                        </Suspense>
                    }
                />
                <Route path="/admin" element={
                    <AdminGuard><AdminLayout /></AdminGuard>
                }>
                    <Route index element={<Navigate to="provision" replace />} />
                    <Route path="provision" element={
                        <Suspense fallback={null}><ChannelProvisionPage /></Suspense>
                    } />
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
