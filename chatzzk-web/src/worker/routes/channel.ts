import { Hono } from 'hono';
import { createClient } from '@supabase/supabase-js';
import { HonoEnv } from '../types';
import { ChannelData, ChannelDataSchema, ChannelDetailSchema } from '@shared/types/channel';
import { SEARCH_ITEMS_PER_PAGE } from '@shared/constants/ui';

const app = new Hono<HonoEnv>();

app.get('/', async (c) => {
    // 1. 파라미터 파싱
    const platformParam = c.req.query('platform')?.toUpperCase() || 'ALL'; // 기본값 ALL
    const page = parseInt(c.req.query('page') || '1');
    const query = c.req.query('query') || '';
    const pageSize = SEARCH_ITEMS_PER_PAGE; // 한 페이지에 보여줄 카드 수

    const supabase = createClient(c.env.SUPABASE_URL, c.env.SUPABASE_ANON_KEY);

    // 2. RPC 호출
    const { data, error } = await supabase
        .rpc('search_channels', {
            p_platform_code: platformParam,
            p_query: query,
            p_page: page,
            p_page_size: pageSize
        });

    if (error) {
        return c.json({ error: error.message }, 500);
    }

    const channels = data || [];
    const totalCount = channels.length > 0 ? Number(channels[0].total_count) : 0;

    const channelsData: ChannelData[] = channels.map((item: any) => {
        return ChannelDataSchema.parse(item);
    });

    return c.json({
        data: channelsData,
        meta: {
            total: totalCount,
            page: page,
            pageSize: pageSize,
            totalPages: Math.ceil(totalCount / pageSize)
        }
    });
});

app.get('/:id', async (c) => {
    const channelId = c.req.param('id');
    const platformParam = c.req.query('platform')?.toUpperCase();

    if (!platformParam) {
        return c.json({ error: 'Platform query parameter is required' }, 400);
    }

    const supabase = createClient(c.env.SUPABASE_URL, c.env.SUPABASE_ANON_KEY);

    const { data, error } = await supabase
        .rpc('get_channel_detail', {
            p_platform_code: platformParam,      // 쿼리에서 온 값
            p_platform_channel_id: channelId     // 경로에서 온 값
        })
        .single();

    if (error) return c.json({ error: error.message }, 500);
    if (!data) return c.json({ error: 'Channel not found' }, 404);

    try {
        const channelDetail = ChannelDetailSchema.parse(data);
        return c.json({ data: channelDetail });
    } catch (e: any) {
        return c.json({ error: 'Data parsing error', details: e.message }, 500);
    }
});

export default app;
