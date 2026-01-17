import { create } from 'zustand';
import { User, Session } from '@supabase/supabase-js';
import { UserProfile, UserProfileSchema } from '@shared/types/user';
import { supabase } from '@/lib/supabase';

interface AuthState {
    user: User | null;
    session: Session | null;
    userProfile: UserProfile | null;
    isInitialized: boolean; // 처음에 로그인 여부를 확인했는지 체크

    setSession: (session: Session | null) => void;
    fetchUserProfile: () => Promise<void>;
    clearSession: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
    user: null,
    session: null,
    userProfile: null,
    isInitialized: false, // 앱이 켜지고 아직 Supabase 확인 전임

    // 로그인 시 세션 저장
    setSession: async (session) => {
        // 1. 로그아웃 상태이거나 세션이 없는 경우
        if (!session) {
            set({
                session: null,
                user: null,
                userProfile: null,
                isInitialized: true, // 로그인 안 된 상태로 확정
            });
            return;
        }

        // 2. 로그인 상태: 일단 user 정보는 넣되, isInitialized는 아직 false로 유지!
        set({
            session,
            user: session.user,
            isInitialized: false,
        });

        // 3. 프로필 데이터 가져오기 (기존 fetchUserProfile 함수 재사용)
        await get().fetchUserProfile();

        // 4. 프로필까지 다 가져왔으니 이제 진짜 초기화 완료!
        set({ isInitialized: true });
    },

    fetchUserProfile: async () => {
        const { user } = get();
        if (!user) return;

        try {
            const { data, error } = await supabase
                .from('users') // users 테이블 조회
                .select('*')
                .eq('supabase_uid', user.id)
                .single();

            if (error) {
                // 데이터가 없을 때(회원가입 직후 등)는 에러가 날 수 있음. 심각한 에러 아님.
                return;
            }
            const profile = UserProfileSchema.parse(data);

            set({ userProfile: profile });
        } catch (err) {
            console.error(err);
        }
    },

    // 로그아웃 시 초기화
    clearSession: () =>
        set({
            session: null,
            user: null,
            userProfile: null, // ✅ 로그아웃 시 프로필도 삭제
            isInitialized: true,
        }),
}));
