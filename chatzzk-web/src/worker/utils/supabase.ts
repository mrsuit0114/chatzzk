import { createClient } from "@supabase/supabase-js";
import { HonoEnv } from "../types";

export const createAuthClient = (env: HonoEnv['Bindings'], token: string) => {
    return createClient(env.SUPABASE_URL, env.SUPABASE_ANON_KEY, {
        global: {
            headers: { Authorization: token },
        },
    });
};


/**
 * 2. [관리자용] Admin Client (Service Role)
 * - Service Role Key를 사용하여 모든 RLS를 무시하고 관리자 권한을 가짐.
 * - 유저 생성, 삭제, 비밀번호 강제 변경 등 특수 목적에만 사용해야 합니다.
 * - ⚠️ 절대 일반 라우트에서 남용하지 마십시오.
 */
export const createAdminClient = (env: HonoEnv['Bindings']) => {
    if (!env.SUPABASE_SERVICE_ROLE_KEY) {
        throw new Error("SUPABASE_SERVICE_ROLE_KEY is missing in environment variables.");
    }

    return createClient(env.SUPABASE_URL, env.SUPABASE_SERVICE_ROLE_KEY, {
        auth: {
            autoRefreshToken: false, // Admin 작업은 단발성이므로 세션 관리 불필요
            persistSession: false,
        },
    });
};
