import { useAuthStore } from '@/stores';
import { USER_ROLE } from '@shared/constants/service_codes';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';


export const AdminGuard = ({ children }: { children: React.ReactNode }) => {
    const navigate = useNavigate();
    // ✅ Supabase 직접 호출 대신 Store의 상태를 구독합니다.
    const { userProfile, isInitialized } = useAuthStore();

    useEffect(() => {
        // 1. 아직 초기화(세션 확인) 중이면 대기
        if (!isInitialized) return;

        // 2. 비로그인 상태 -> 로그인 페이지로
        if (!userProfile) {
            navigate('/login');
            return;
        }

        // 3. 권한 체크 (Store에 저장된 user 객체 안에 role이 있다고 가정)
        // 만약 user 객체에 role이 없다면, fetchUserProfile 로직에서 role을 포함하도록 수정해야 합니다.
        if (userProfile.role !== USER_ROLE.ADMIN) {
            alert("관리자 권한이 없습니다.");
            navigate('/');
        }
    }, [userProfile, isInitialized, navigate]);

    // 로딩 중이거나 권한이 없는 찰나의 순간에는 아무것도 보여주지 않음 (혹은 스피너)
    if (!isInitialized || !userProfile || userProfile.role !== USER_ROLE.ADMIN) {
        return <div className="p-10 text-center">권한 확인 중...</div>;
    }

    return <>{children}</>;
};
