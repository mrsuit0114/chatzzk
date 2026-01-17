import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "@/stores/auth.store";
import { ReactNode } from "react";

interface ProtectedRouteProps {
    children?: ReactNode; // ✅ children을 받을 수 있도록 타입 정의
}

export const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
    const { user, isInitialized } = useAuthStore();
    const location = useLocation();

    // 1. 초기화 중일 때
    if (!isInitialized) {
        return <div className="flex h-screen items-center justify-center">인증 정보 확인 중...</div>;
    }

    // 2. 로그인 안 된 경우 리다이렉트
    if (!user) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    // 3. ✅ children이 있으면 그걸 보여주고(Wrapper 방식), 없으면 Outlet(Layout 방식) 사용
    return children ? <>{children}</> : <Outlet />;
};
