import { create } from 'zustand';
import { User, Session } from '@supabase/supabase-js';

interface AuthState {
    user: User | null;
    session: Session | null;
    isInitialized: boolean; // 처음에 로그인 여부를 확인했는지 체크
    setSession: (session: Session | null) => void;
    clearSession: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
    user: null,
    session: null,
    isInitialized: false, // 앱이 켜지고 아직 Supabase 확인 전임

    // 로그인 시 세션 저장
    setSession: (session) =>
        set({
            session,
            user: session?.user ?? null,
            isInitialized: true,
        }),

    // 로그아웃 시 초기화
    clearSession: () =>
        set({
            session: null,
            user: null,
            isInitialized: true,
        }),
}));
