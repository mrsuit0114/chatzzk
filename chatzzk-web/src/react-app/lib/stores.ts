import { AuthUser } from "@/types";
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

interface AuthState {
    user: AuthUser | null;
    isAuthenticated: boolean;
    login: (userInfo: AuthUser) => void;
    logout: () => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            user: null,
            isAuthenticated: false,

            // 로그인 액션 (Mock: 실제로는 API 통신 후 토큰 저장)
            login: (userInfo: AuthUser) => {
                set({
                    user: userInfo,
                    isAuthenticated: true
                });
            },

            // 로그아웃 액션
            logout: () => {
                set({ user: null, isAuthenticated: false });
            },
        }),
        {
            name: "auth-storage", // 로컬 스토리지 키 이름
            storage: createJSONStorage(() => localStorage),
        }
    )
);
