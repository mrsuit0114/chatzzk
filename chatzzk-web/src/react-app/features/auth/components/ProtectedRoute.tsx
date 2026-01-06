import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "@/stores/auth.store";

export function ProtectedRoute() {
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
    const location = useLocation();

    if (!isAuthenticated) {
        // 로그인 안 된 경우, 현재 위치(location)를 state에 담아 로그인 페이지로 보냄
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    // 라우터에서 <Route element={<ProtectedRoute />}> 안에 넣은 자식 라우트들이 여기에 표시됨
    return <Outlet />;
}
