import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { authMiddleware } from './middlewares/auth';
import { User } from '@supabase/supabase-js';

import vodRoute from './routes/vod';
import channelRoute from './routes/channel';

type Variables = {
    user: User;
}

const app = new Hono<{ Bindings: Env, Variables: Variables }>();

app.use("/api/*", cors());

app.route('/api/vods', vodRoute);

app.route('/api/channels', channelRoute);

app.use('/api/protected/*', authMiddleware);

app.get("/api/health", (c) => {
    return c.json({ status: 'ok' });
});

export default app;
