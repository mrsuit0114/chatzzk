import { useAuthStore } from '@/stores';
import { USER_ROLE } from '@shared/constants/service_codes';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';


export const AdminGuard = ({ children }: { children: React.ReactNode }) => {
    const navigate = useNavigate();
    // ✅ Supabase 직접 호출 대신 Store의 상태를 구독합니다.
    const { userProfile, isInitialized } = useAuthStore();

    useEffect(() => {
        // 1. 초기화가 안 끝났으면 아무것도 하지 않고 대기 (useEffect 종료)
        //    이 줄이 없으면 새로고침 시 바로 튕깁니다.
        if (!isInitialized) return;

        // 2. 초기화 완료 후 체크: 비로그인 상태
        if (!userProfile) {
            navigate('/login', { replace: true }); // 뒤로가기 방지 replace
            return;
        }

        // 3. 초기화 완료 후 체크: 권한 부족
        if (userProfile.role !== USER_ROLE.ADMIN) {
            alert("관리자 권한이 없습니다.");
            navigate('/', { replace: true });
        }
    }, [userProfile, isInitialized, navigate]);

    // ✅ 화면 렌더링 처리

    // Case 1: 아직 세션 확인 중 (새로고침 시 이 화면이 잠깐 보임)
    if (!isInitialized) {
        return (
            <div className="flex h-screen items-center justify-center">
                <div className="text-gray-500">관리자 권한 확인 중...</div>
                {/* 여기에 스피너 컴포넌트를 넣으면 더 좋습니다 */}
            </div>
        );
    }

    // Case 2: 로딩 끝났는데 권한이 없는 경우 (useEffect에서 이동시키겠지만, 찰나의 순간 UI 보호)
    if (!userProfile || userProfile.role !== USER_ROLE.ADMIN) {
        return null;
    }

    return <>{children}</>;
};
