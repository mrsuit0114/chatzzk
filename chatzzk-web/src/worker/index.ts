import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { HonoEnv } from './types';
import { authMiddleware } from './middlewares/auth';

import vodRoute from './routes/vod';
import channelRoute from './routes/channel';
import myRoute from './routes/my';
import myEditorRoute from './routes/my-editor';

const app = new Hono<HonoEnv>();

app.use("/api/*", cors());
app.route('/api/vods', vodRoute);
app.route('/api/channels', channelRoute);

app.use('/api/my/*', authMiddleware);
app.route('/api/my', myRoute);
app.route('/api/my/editor', myEditorRoute);

app.get("/api/health", (c) => {
    return c.json({ status: 'ok' });
});

export default app;
