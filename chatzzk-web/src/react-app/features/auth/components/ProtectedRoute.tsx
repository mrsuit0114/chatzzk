import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "@/stores/auth.store";

export const ProtectedRoute = () => {
    const { user, isInitialized } = useAuthStore();
    const location = useLocation();

    // 1. 아직 로그인 체크가 안 끝났으면 아무것도 안 보여줌 (App.tsx의 로딩이 처리하겠지만 안전장치)
    if (!isInitialized) {
        return <div>인증 정보 확인 중...</div>;
    }

    if (!user) {
        // 로그인 안 된 경우, 현재 위치(location)를 state에 담아 로그인 페이지로 보냄
        return <Navigate to="/login" state={{ from: location }} replace />;
    }
    return <Outlet />;
}
