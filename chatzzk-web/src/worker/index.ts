import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { sentry } from '@hono/sentry';
import { HonoEnv } from './types';
import { authMiddleware } from './middlewares/auth';

import vodRoute from './routes/vod';
import channelRoute from './routes/channel';
import myRoute from './routes/my';
import myEditorRoute from './routes/my-editor';
import adminRoute from './routes/admin';

const app = new Hono<HonoEnv>();

app.use("*", (c, next) => {
    return sentry({
        dsn: c.env.SENTRY_DSN,

        sendDefaultPii: false,
        beforeSend(event) {
            // 요청(request) 바디나 헤더에서 쿠키, 인증 토큰 제거
            if (event.request && event.request.headers) {
                delete event.request.headers["Authorization"];
                delete event.request.headers["Cookie"];
            }
            return event;
        }
    })(c, next);
});

app.use("/api/*", async (c, next) => {
    const allowOrigin = c.env.ALLOWED_ORIGIN; // 환경변수 (배열 또는 문자열)
    const requestOrigin = c.req.header('Origin');
    const requestReferer = c.req.header('Referer'); // 주의: HTTP 표준 스펠링은 'Referer' (R이 하나 빠짐)

    // 1. 검증 로직 함수화
    const isAllowedDomain = (domain: string) => {
        if (Array.isArray(allowOrigin)) {
            // dev 환경: 배열(["https://...", "http://..."])
            return allowOrigin.some(allowed => domain.startsWith(allowed));
        } else {
            // production 환경: 문자열("https://...")
            return domain.startsWith(allowOrigin);
        }
    };

    // 2. [단계별 검증]
    // Case A: Origin 헤더가 있는 경우 (주로 CORS 요청, POST 요청 등)
    if (requestOrigin) {
        if (!isAllowedDomain(requestOrigin)) {
            return c.json({ error: 'Access Denied: Invalid Origin' }, 403);
        }
    }
    // Case B: Origin은 없지만 Referer가 있는 경우 (Same-Origin GET 요청 등 - 현재 선생님 로그 상황)
    else if (requestReferer) {
        if (!isAllowedDomain(requestReferer)) {
            return c.json({ error: 'Access Denied: Invalid Referer' }, 403);
        }
    }
    // Case C: Origin도 없고 Referer도 없는 경우 (Curl, Python 스크립트 등)
    else {
        return c.json({
            error: 'Access Denied: Missing Origin/Referer. (브라우저로 접속해주세요)'
        }, 403);
    }

    // CORS 미들웨어 동적 생성
    const corsMiddleware = cors({
        origin: allowOrigin, // 변수 값 적용 ('*' 또는 'https://...')
        allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allowHeaders: ['Content-Type', 'Authorization', 'If-None-Match'],
        exposeHeaders: ['ETag'],
        maxAge: 600,
    });

    return corsMiddleware(c, next);
});

app.onError((err, c) => {
    const sentryInstance = c.get('sentry');

    if (sentryInstance) {
        // (선택사항) 환경 태그 명시적 설정 (wrangler.json의 vars 값 활용)
        // sentry가 자동으로 감지하기도 하지만, 확실하게 설정하려면 아래 줄 추가
        if (c.env.SENTRY_ENVIRONMENT) {
            sentryInstance.setTag('environment', c.env.SENTRY_ENVIRONMENT);
        }

        // 에러 전송
        sentryInstance.captureException(err);
    }

    // Cloudflare 로그에도 남김 (디버깅용)
    console.error('SERVER ERROR:', err);

    // 사용자에게는 500 에러 반환
    return c.json({ error: 'Internal Server Error' }, 500);
});

app.route('/api/vods', vodRoute);
app.route('/api/channels', channelRoute);

app.use('/api/my/*', authMiddleware);
app.route('/api/my', myRoute);
app.route('/api/my/editor', myEditorRoute);

app.use('/api/admin/*', authMiddleware);
app.route('/api/admin', adminRoute);

app.get("/api/health", (c) => {
    return c.json({ status: 'ok' });
});

app.get('*', async (c) => {
    // 1. 요청한 URL이 API가 아닌지 한 번 더 확인 (안전장치)
    // (위에서 이미 API 라우트들이 처리했겠지만 확실하게)
    if (c.req.path.startsWith('/api')) {
        return c.json({ error: 'Not Found' }, 404);
    }

    // 2. index.html 파일을 가져옵니다.
    // c.env.ASSETS는 Cloudflare가 정적 파일(dist 폴더)을 관리하는 객체입니다.
    // 사용자가 '/chzzk'를 요청했어도, 우리는 억지로 '/index.html' 내용을 줍니다.
    return await c.env.ASSETS.fetch(new URL('/index.html', c.req.url));
});

export default app;
