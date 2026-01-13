// src/worker/types.ts
import { User, SupabaseClient } from '@supabase/supabase-js';

// 1. 미들웨어를 통해 주입될 변수들
export type Variables = {
    user: User;                 // authMiddleware가 넣어줌
    supabase: SupabaseClient;   // authMiddleware가 넣어줌 (재사용)
};

// 2. Hono 앱 전체 설정 타입 (제네릭 단축용)
// Bindings에 전역 Env 인터페이스를 연결합니다.
export type HonoEnv = {
    Bindings: Env;       // worker-configuration.d.ts의 Env 사용
    Variables: Variables;
};
