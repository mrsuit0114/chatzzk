import { Hono } from 'hono';
import { HonoEnv } from '../types';
import { createClient } from '@supabase/supabase-js';
import { VOD_ITEMS_PER_PAGE } from '@shared/constants/ui';
import { VodData, VodDataSchema } from '@shared/types/vod';
import { createAuthClient } from '../utils/supabase';
import { VOD_PIPELINE_STATUS } from '@shared/constants/service_codes';

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

app.get('/analysis/:platform/:videoNo', async (c) => {
    const platform = c.req.param('platform');
    const videoNo = c.req.param('videoNo');

    // 1. Supabase 클라이언트 생성 (로그인 여부 확인용)
    const authHeader = c.req.header('Authorization');
    const supabase = createAuthClient(c.env, authHeader || '');


    try {
        // 2. VOD 메타데이터 조회 (3단 Join: Vods -> Channels -> Platforms)
        const { data: vod, error } = await supabase
            .from('vods')
            .select(`
                id,
                video_title,
                video_no,
                is_exposed,
                publish_date,
                pipeline_status,
                channels!inner (
                    user_id,
                    editor_id,
                    vod_exposure_delay_hours,
                    vod_detail_exposure_delay_hours,
                    platforms!inner (
                        platform_code
                    )
                )
            `)
            .eq('video_no', videoNo)
            // ✅ 중첩된 테이블 필터링 (플랫폼 코드가 일치하는지 확인)
            .eq('channels.platforms.platform_code', platform.toUpperCase())
            .single();

        console.log('VOD:', vod, 'VOD Fetch Error:', error);
        if (error || !vod) {
            return c.json({ error: 'VOD not found or access denied' }, 404);
        }

        // 4. [중요] 파이프라인 상태 체크 (파일 존재 여부 확인)
        // 소유자라도 분석이 안 끝났으면 파일 로드 시도 금지
        if (vod.pipeline_status !== VOD_PIPELINE_STATUS.COMPLETED) {
            return c.json({
                error: 'Analysis is still processing.',
                status: vod.pipeline_status
            }, 400); // 404보다는 400이나 422가 적절 (데이터는 있는데 파일이 없음)
        }

        // 3. 접근 권한 체크 (HighlightView/Page 접근 권한)
        const channel = vod.channels as any; // Join된 채널 정보

        // 사용자 정보 확인 (Optional - 비로그인 유저도 있을 수 있음)
        const { data: { user } } = await supabase.auth.getUser();

        let isOwnerOrEditor = false;
        if (user) {
            // 내부 User ID 조회
            const { data: internalUser } = await supabase
                .from('users')
                .select('id')
                .eq('supabase_uid', user.id)
                .single();

            if (internalUser) {
                isOwnerOrEditor = (internalUser.id === channel.user_id) || (internalUser.id === channel.editor_id);
            }
        }

        // 경로 규칙: vods/{vod_id}/analysis.json
        const objectKey = `vods/${vod.id}/analytics.json`;
        const object = await c.env.MY_BUCKET.get(objectKey);

        if (!object) {
            // DB에는 있는데 R2에 파일이 없는 경우 (분석 중이거나 오류)
            return c.json({ error: 'Analysis data not found in storage.' }, 404);
        }

        // JSON 파싱 후 반환
        const analysisData = await object.json();

        const publishDate = new Date(vod.publish_date);
        const detailDelay = channel.vod_detail_exposure_delay_hours || 0;

        // 상세 분석 공개 시점 = 방송일 + 지연 시간
        const insightReleaseTime = new Date(publishDate.getTime() + (detailDelay * 60 * 60 * 1000));

        // 잠금 조건: 소유자/편집자가 아니면서 && 아직 공개 시간이 안 됐을 때
        const isInsightLocked = !isOwnerOrEditor && (new Date() < insightReleaseTime);

        return c.json({
            ...(analysisData as object),
            _meta: {
                isInsightLocked,
                insightReleaseAt: insightReleaseTime.toISOString()
            }
        });

    } catch (e: any) {
        console.error(e);
        return c.json({ error: e.message }, 500);
    }
});

export default app;
