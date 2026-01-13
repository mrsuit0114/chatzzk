import { Hono } from 'hono';
import { HonoEnv } from '../types';
import { createClient } from '@supabase/supabase-js';
import { VOD_ITEMS_PER_PAGE } from '@shared/constants/ui';
import { VodData, VodDataSchema } from '@shared/types/vod';

const app = new Hono<HonoEnv>();

app.get('/', async (c) => {
    const platformParam = c.req.query('platform')?.toUpperCase();
    const page = parseInt(c.req.query('page') || '1');
    const query = c.req.query('query') || '';
    const fromDate = c.req.query('from') || null;
    const toDate = c.req.query('to') || null;
    const channelId = c.req.query('channelId');
    const pageSize = VOD_ITEMS_PER_PAGE;

    if (!platformParam) {
        return c.json({ error: 'Platform is required' }, 400);
    }

    const supabase = createClient(c.env.SUPABASE_URL, c.env.SUPABASE_ANON_KEY);

    const { data, error } = await supabase
        .rpc('search_vods', {
            p_platform_code: platformParam,
            p_query: query,
            p_page: page,
            p_page_size: pageSize,
            p_from_date: fromDate,
            p_to_date: toDate,
            p_channel_id: channelId
        });

    if (error) {
        return c.json({ error: error.message }, 500);
    }

    const vods = data || [];
    const totalCount = vods.length > 0 ? Number(vods[0].total_count) : 0;

    const vodsData: VodData[] = vods.map((item: any) => {
        const rawData = {
            ...item,
            platform: platformParam
        }
        const vodData = VodDataSchema.parse(rawData);
        return vodData;
    });

    return c.json({
        data: vodsData,
        meta: {
            total: totalCount,
            page: page,
            pageSize: pageSize,
            totalPages: Math.ceil(totalCount / pageSize)
        }
    });
});

export default app;
