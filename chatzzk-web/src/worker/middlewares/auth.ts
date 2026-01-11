// src/worker/middlewares/auth.ts
import { createMiddleware } from 'hono/factory';
import { createClient, User } from '@supabase/supabase-js';

type Env = {
    SUPABASE_URL: string;
    SUPABASE_ANON_KEY: string;
};

type Variables = {
    user: User; // "user라는 칸에는 Supabase User 객체가 들어갈 거야"
};

// 미들웨어 생성
export const authMiddleware = createMiddleware<{ Bindings: Env, Variables: Variables }>(async (c, next) => {
    const authHeader = c.req.header('Authorization');

    if (!authHeader) {
        return c.json({ error: '인증 토큰이 없습니다.' }, 401);
    }
    // 2. "Bearer 토큰값" 형태에서 토큰만 분리
    const token = authHeader.replace('Bearer ', '');

    // 3. Supabase 클라이언트 생성 (요청 들어올 때마다 가볍게 생성)
    const supabase = createClient(c.env.SUPABASE_URL, c.env.SUPABASE_ANON_KEY);

    // 4. Supabase에게 "이 토큰 진짜야?" 물어보기
    const { data: { user }, error } = await supabase.auth.getUser(token);

    if (error || !user) {
        return c.json({ error: '유효하지 않은 토큰입니다.' }, 401);
    }

    // 5. 검증 통과!
    // 나중에 API 로직에서 "누가 요청했는지" 알 수 있게 user 정보를 context에 심어줌
    c.set('user', user);

    await next(); // 다음 로직으로 이동
});
