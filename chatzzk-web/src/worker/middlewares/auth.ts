// src/worker/middlewares/auth.ts
import { createMiddleware } from 'hono/factory';
import { createClient } from '@supabase/supabase-js';
import { HonoEnv } from '../types';

// 미들웨어 생성
export const authMiddleware = createMiddleware<HonoEnv>(async (c, next) => {
    const authHeader = c.req.header('Authorization');

    if (!authHeader) {
        return c.json({ error: 'Authorization header is required' }, 401);
    }

    // 1. 토큰을 포함한 Supabase 클라이언트 생성
    const supabase = createClient(c.env.SUPABASE_URL, c.env.SUPABASE_ANON_KEY, {
        global: { headers: { Authorization: authHeader } },
    });

    // 2. 토큰 검증 (Supabase Auth 서버에 확인)
    const { data: { user }, error } = await supabase.auth.getUser();

    if (error || !user) {
        return c.json({ error: 'Invalid or expired token' }, 401);
    }

    // 3. 검증된 정보를 컨텍스트(c)에 저장 -> 다음 핸들러가 사용함
    c.set('user', user);
    c.set('supabase', supabase);

    await next();
});
