import { Hono } from 'hono';
import { HonoEnv } from '../types';

import { z } from 'zod';

import { ChannelMetadataUpdateSchema, MyChannelSchema } from '@shared/types/channel';
import { VOD_ITEMS_PER_PAGE } from '@shared/constants/ui';
import { MyVodDataSchema } from '@shared/types/vod';

const app = new Hono<HonoEnv>();

// GET /api/my/channel
app.get('/channel', async (c) => {
    // ✅ 미들웨어가 이미 생성하고 인증을 마친 클라이언트를 가져옴
    const supabase = c.get('supabase');

    const { data, error } = await supabase.rpc('get_my_channel').single();

    if (error || !data) return c.json({ error: 'Channel Not Found' }, 404);

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

    const fromDate = c.req.query('fromDate') || null;
    const toDate = c.req.query('toDate') || null;

    const pageSize = VOD_ITEMS_PER_PAGE;

    const { data, error } = await supabase
        .rpc('get_my_vods', {
            p_page: page,
            p_page_size: pageSize,
            p_query: query,
            p_visibility: visibility,
            p_from_date: fromDate,
            p_to_date: toDate
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

app.put('/channel/metadata', async (c) => {
    const supabase = c.get('supabase');
    const body = await c.req.json().catch(() => ({}));

    const result = ChannelMetadataUpdateSchema.safeParse(body);

    if (!result.success) {
        return c.json({ error: 'Invalid body', details: result.error }, 400);
    }

    // 3. RPC 호출 (JSONB 통째로 전달)
    const { data: success, error } = await supabase.rpc('update_channel_metadata', {
        p_attributes: result.data // 변환된 데이터를 통째로 전달
    });

    if (error || !success) return c.json({ error: 'Update failed' }, 500);

    return c.json({ success: true });
});

app.patch('/channel', async (c) => {
    const supabase = c.get('supabase');
    const user = c.get('user');

    const schema = z.object({
        isCollectionEnabled: z.boolean().optional(),
        vodDetailExposureDelayHours: z.number().min(0).optional(),
        vodExposureDelayHours: z.number().min(0).optional(),
    });

    const body = await c.req.json().catch(() => null);
    const parsed = schema.safeParse(body);
    if (!parsed.success) return c.json({ error: parsed.error }, 400);

    // DB 컬럼명으로 매핑 (camelCase -> snake_case)
    const updates: any = {};
    if (parsed.data.isCollectionEnabled !== undefined) updates.is_collection_enabled = parsed.data.isCollectionEnabled;
    if (parsed.data.vodDetailExposureDelayHours !== undefined) updates.vod_detail_exposure_delay_hours = parsed.data.vodDetailExposureDelayHours;
    if (parsed.data.vodExposureDelayHours !== undefined) updates.vod_exposure_delay_hours = parsed.data.vodExposureDelayHours;

    if (Object.keys(updates).length === 0) return c.json({ success: true });

    try {
        // ✅ [수정] 1. UUID로 내부 유저 ID(Integer) 찾기
        const { data: userData, error: userError } = await supabase
            .from('users')
            .select('id')
            .eq('supabase_uid', user.id)
            .single();

        if (userError || !userData) {
            return c.json({ error: 'User not found' }, 404);
        }

        // ✅ [수정] 2. 찾은 Integer ID로 업데이트 수행
        const { error } = await supabase
            .from('channels')
            .update(updates)
            .eq('user_id', userData.id); // UUID 대신 Integer 사용

        if (error) return c.json({ error: error.message }, 500);

        return c.json({ success: true });
    } catch (e: any) {
        return c.json({ error: e.message }, 500);
    }
});

export default app;
