import { Hono } from 'hono';
import { HonoEnv } from '../types';

import { MyChannelSchema } from '@shared/types/channel';

const app = new Hono<HonoEnv>();

// GET /api/my/channel
app.get('/channel', async (c) => {
    // ✅ 미들웨어가 이미 생성하고 인증을 마친 클라이언트를 가져옴
    const supabase = c.get('supabase');

    // 필요하다면 유저 정보도 바로 가져올 수 있음
    // const user = c.get('user');

    // RPC 호출 (auth.uid()가 자동으로 인식됨)
    const { data, error } = await supabase
        .rpc('get_my_channel')
        .single();

    if (error) return c.json({ error: error.message }, 500);

    // 일반 유저라 채널이 없는 경우 등
    if (!data) return c.json({ error: 'Channel not found or permission denied' }, 404);

    try {
        const myChannel = MyChannelSchema.parse(data);
        return c.json({ data: myChannel });
    } catch (e: any) {
        return c.json({ error: 'Data parsing error', details: e.message }, 500);
    }
});

export default app;
