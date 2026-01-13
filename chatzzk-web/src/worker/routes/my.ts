import { Hono } from 'hono';
import { HonoEnv } from '../types';

import { z } from 'zod';

import { MyChannelSchema } from '@shared/types/channel';
import { VOD_ITEMS_PER_PAGE } from '@shared/constants/ui';
import { MyVodDataSchema } from '@shared/types/vod';

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


// GET /api/my/vods
app.get('/vods', async (c) => {
    const supabase = c.get('supabase');

    // 파라미터 파싱
    const page = parseInt(c.req.query('page') || '1');
    const query = c.req.query('query') || '';
    const visibility = c.req.query('visibility') || null; // 필터링 (옵션)
    const pageSize = VOD_ITEMS_PER_PAGE;

    const { data, error } = await supabase
        .rpc('get_my_vods', {
            p_page: page,
            p_page_size: pageSize,
            p_query: query,
            p_visibility: visibility
        });

    if (error) return c.json({ error: error.message }, 500);

    const vods = data || [];
    const totalCount = vods.length > 0 ? Number(vods[0].total_count) : 0;

    try {
        const myVods = vods.map((item: any) => MyVodDataSchema.parse(item));

        return c.json({
            data: myVods,
            meta: {
                total: totalCount,
                page: page,
                pageSize: pageSize,
                totalPages: Math.ceil(totalCount / pageSize)
            }
        });
    } catch (e: any) {
        return c.json({ error: 'Data parsing error', details: e.message }, 500);
    }
});


app.patch('/vods/:videoNo/exposure', async (c) => {
    const supabase = c.get('supabase');
    const videoNo = c.req.param('videoNo');

    // ✅ Body Validation 수정: platform, channelId 추가
    const bodySchema = z.object({
        isExposed: z.boolean(),
        platform: z.string(),   // 추가
        channelId: z.string()   // 추가
    });

    const body = await c.req.json().catch(() => null);
    const parsed = bodySchema.safeParse(body);

    if (!parsed.success) {
        return c.json({ error: 'Invalid body', details: parsed.error }, 400);
    }

    const { isExposed, platform, channelId } = parsed.data;

    // ✅ RPC 호출 인자 추가
    const { data: success, error } = await supabase
        .rpc('update_vod_exposure', {
            p_video_no: videoNo,
            p_platform_code: platform,
            p_platform_channel_id: channelId,
            p_is_exposed: isExposed
        });

    if (error) return c.json({ error: error.message }, 500);

    if (!success) {
        return c.json({ error: 'Update failed. VOD not found or permission denied.' }, 403);
    }

    return c.json({ success: true });
});

export default app;
