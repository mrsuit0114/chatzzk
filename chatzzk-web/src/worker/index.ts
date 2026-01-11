import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { authMiddleware } from './middlewares/auth';
import { User } from '@supabase/supabase-js';


// Env 인터페이스는 worker-configuration.d.ts에 정의되어 있다고 가정합니다.
// (수정을 미루셨으므로 여기서는 빨간줄이 뜰 수 있지만, 일단 진행해봅니다.)
interface Env {
    SUPABASE_URL: string;
    SUPABASE_ANON_KEY: string;
    MY_BUCKET: R2Bucket;
}

type Variables = {
    user: User;
}

const app = new Hono<{ Bindings: Env, Variables: Variables }>();

app.use("/api/*", cors());

// 1. 공개 API
app.get("/api/health", (c) => {
    return c.json({ status: 'ok' });
});

// 2. 비공개 API 그룹
app.use('/api/protected/*', authMiddleware);

// 예시: 내 정보 가져오기 API
app.get('/api/protected/me', (c) => {
    const user = c.get('user');
    return c.json({
        message: '당신은 인증된 유저입니다!',
        user_id: user.id,
        email: user.email
    });
});

export default app;
