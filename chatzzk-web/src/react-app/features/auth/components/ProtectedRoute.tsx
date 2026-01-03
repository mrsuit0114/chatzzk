import { useAuthStore } from "@/lib/stores";
import { Navigate, Outlet } from "react-router-dom";

export function ProtectedRoute() {
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

    // 1. 로그인을 안 했다면? -> 로그인 페이지로 쫓아냄
    // replace: 뒤로가기 눌렀을 때 다시 여기로 못 오게 기록을 덮어씀
    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    // 2. 로그인을 했다면? -> 자식 컴포넌트(Outlet) 보여줌
    return <Outlet />;
}
