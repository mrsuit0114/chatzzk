import { supabase } from "@/lib/supabase";
import { useAuthStore } from "@/stores";
import { useEffect } from "react";


export function useAuthInit() {
    const { setSession, clearSession, isInitialized } = useAuthStore();

    useEffect(() => {
        const handleAuth = async (session: any) => {
            if (session) {
                // 스토어의 최신 상태 조회 (의존성 배열 문제 해결)
                const currentUser = useAuthStore.getState().user;

                // 중복 호출 방지
                if (currentUser?.id === session.user.id) {
                    return;
                }

                setSession(session);
            } else {
                clearSession();
            }
        };

        // 초기 세션 확인 및 구독 설정
        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            handleAuth(session);
        });

        return () => subscription.unsubscribe();
    }, []); // 마운트 시 1회 실행

    return { isInitialized };
}
