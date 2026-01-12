import { Hono } from 'hono';
import { createClient } from '@supabase/supabase-js';
import { PLATFORM_ITEMS_PER_PAGE } from '@shared/constants/ui';
import { Variables } from 'hono/types';

const app = new Hono<{ Bindings: Env, Variables: Variables }>();

app.get('/', async (c) => {
    const platformParam = c.req.query('platform');
    const page = parseInt(c.req.query('page') || '1');
    const query = c.req.query('query') || '';
    const fromDate = c.req.query('from') || null;
    const toDate = c.req.query('to') || null;
    const pageSize = PLATFORM_ITEMS_PER_PAGE;

    if (!platformParam) {
        return c.json({ error: 'Platform is required' }, 400);
    }

    const supabase = createClient(c.env.SUPABASE_URL, c.env.SUPABASE_ANON_KEY);

    const { data, error } = await supabase
        .rpc('search_vods', {
            p_platform_code: platformParam.toUpperCase(),
            p_query: query,
            p_page: page,
            p_page_size: pageSize,
            p_from_date: fromDate,
            p_to_date: toDate
        });

    if (error) {
        return c.json({ error: error.message }, 500);
    }

    const vods = data || [];
    const totalCount = vods.length > 0 ? Number(vods[0].total_count) : 0;

    const formattedData = vods.map((item: any) => {
        return {
            videoNo: item.video_no,
            title: item.video_title,
            channelName: item.channel_name,
            publishDate: item.publish_date,
            platform: platformParam,
            duration: item.duration,
        };
    });

    return c.json({
        data: formattedData,
        meta: {
            total: totalCount,
            page: page,
            pageSize: pageSize,
            totalPages: Math.ceil(totalCount / pageSize)
        }
    });
});

export default app;
