import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { HonoEnv } from './types';
import { authMiddleware } from './middlewares/auth';

import vodRoute from './routes/vod';
import channelRoute from './routes/channel';
import myRoute from './routes/my';
import myEditorRoute from './routes/my-editor';

const app = new Hono<HonoEnv>();

app.use("/api/*", cors({
    origin: '*', // 실제 운영 시 프론트엔드 도메인으로 제한 권장
    allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    // 클라이언트가 서버로 보낼 수 있는 헤더
    allowHeaders: ['Content-Type', 'Authorization', 'If-None-Match'],
    // 클라이언트(브라우저 JS)가 응답에서 읽을 수 있는 헤더
    exposeHeaders: ['ETag'],
    maxAge: 600,
}));

app.route('/api/vods', vodRoute);
app.route('/api/channels', channelRoute);

app.use('/api/my/*', authMiddleware);
app.route('/api/my', myRoute);
app.route('/api/my/editor', myEditorRoute);

app.get("/api/health", (c) => {
    return c.json({ status: 'ok' });
});

export default app;
