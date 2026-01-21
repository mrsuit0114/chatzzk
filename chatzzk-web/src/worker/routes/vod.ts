import { Hono } from 'hono';
import { HonoEnv } from '../types';
import { createClient } from '@supabase/supabase-js';
import { VOD_ITEMS_PER_PAGE } from '@shared/constants/ui';
import { VodData, VodDataSchema } from '@shared/types/vod';
import { createAuthClient } from '../utils/supabase';
import { VOD_PIPELINE_STATUS } from '@shared/constants/service_codes';
import { getAnalysisKey, getStreamLogKey } from '../constants';

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

        const publishDate = new Date(vod.publish_date);
        const detailDelay = channel.vod_detail_exposure_delay_hours || 0;
        const insightReleaseTime = new Date(publishDate.getTime() + (detailDelay * 60 * 60 * 1000));
        const isInsightLocked = !isOwnerOrEditor && (new Date() < insightReleaseTime);

        // 5. R2 객체 가져오기 (헤더만 먼저 읽거나, get은 비용이 저렴하므로 바로 호출)
        const objectKey = getAnalysisKey(vod.id);
        const object = await c.env.MY_BUCKET.get(objectKey);

        if (!object) {
            return c.json({ error: 'Analysis data not found in storage.' }, 404);
        }

        // ✅ [Cache Strategy: Smart ETag]
        // analysis.json 파일 자체는 안 바뀌지만, _meta(잠금여부)는 시간에 따라 바뀝니다.
        // 따라서 파일의 ETag와 잠금 상태를 조합하여 고유 값을 만듭니다.
        // 잠금 상태가 바뀌면 ETag가 달라져서 프론트엔드가 새로 데이터를 받게 됩니다.
        const rawEtag = object.httpEtag.replace(/^"|"$/g, '');
        const compositeEtag = `"${rawEtag}"`;

        // 2. Client Side ETag 가져오기 및 정규화 (Weak ETag 처리)
        const ifNoneMatch = c.req.header('If-None-Match');

        // ✅ [Fix] 'W/' 접두사가 있으면 제거하여 비교
        let clientEtag = ifNoneMatch;
        if (clientEtag && clientEtag.startsWith('W/')) {
            clientEtag = clientEtag.slice(2); // 앞의 2글자(W/) 제거
        }


        if (clientEtag === compositeEtag) {
            // 304 응답을 줄 때도 바뀐 헤더(잠금 상태)는 실어 보냅니다.
            // 브라우저는 304를 받으면 Body는 캐시를 쓰고, Header는 서버가 준 것으로 업데이트합니다.
            const headers = new Headers();
            headers.set('ETag', compositeEtag);
            headers.set('Cache-Control', 'private, no-cache'); // 항상 검증 요청
            headers.set('X-Insight-Locked', isInsightLocked.toString()); // ✨ 바뀐 상태 전달
            headers.set('X-Insight-Release-At', insightReleaseTime.toISOString());
            headers.set('Access-Control-Expose-Headers', 'X-Insight-Locked, X-Insight-Release-At, ETag');

            return new Response(null, {
                status: 304,
                headers
            });
        }

        const headers = new Headers();
        object.writeHttpMetadata(headers as any);
        headers.set('ETag', compositeEtag);
        headers.set('Cache-Control', 'private, no-cache');
        headers.set('X-Insight-Locked', isInsightLocked.toString());
        headers.set('X-Insight-Release-At', insightReleaseTime.toISOString());
        headers.set('Access-Control-Expose-Headers', 'X-Insight-Locked, X-Insight-Release-At, ETag');

        return new Response(object.body, {
            headers,
            status: 200
        });

    } catch (e: any) {
        console.error(e);
        return c.json({ error: e.message }, 500);
    }
});

app.get('/logs/:platform/:videoNo/:index', async (c) => {
    const platform = c.req.param('platform');
    const videoNo = c.req.param('videoNo');
    const logIndex = c.req.param('index'); // Chapter Index (0, 1, 2...)

    const authHeader = c.req.header('Authorization');
    const supabase = createAuthClient(c.env, authHeader || '');
    const { data: { user } } = await supabase.auth.getUser();

    try {
        // 1. VOD 및 설정 조회 (분석 API와 동일한 로직 + Detail Delay 컬럼)
        const { data: vod, error } = await supabase
            .from('vods')
            .select(`
                id,
                video_no,
                publish_date,
                pipeline_status,
                is_exposed,
                channels!inner (
                    user_id,
                    editor_id,
                    vod_exposure_delay_hours,
                    vod_detail_exposure_delay_hours,
                    platforms!inner ( platform_code )
                )
            `)
            .eq('video_no', videoNo)
            .eq('channels.platforms.platform_code', platform.toUpperCase())
            .single();

        if (error || !vod) return c.json({ error: 'VOD not found' }, 404);
        if (vod.pipeline_status !== VOD_PIPELINE_STATUS.COMPLETED) return c.json({ error: 'Not ready' }, 400);

        // 2. 권한 체크 (소유자/편집자 확인)
        const channel = vod.channels as any;
        let isOwnerOrEditor = false;

        if (user) {
            const { data: internalUser } = await supabase
                .from('users')
                .select('id')
                .eq('supabase_uid', user.id)
                .single();
            if (internalUser) {
                isOwnerOrEditor = (internalUser.id === channel.user_id) ||
                    (internalUser.id === channel.editor_id);
            }
        }

        // 3. [핵심] 일반 유저는 상세 공개 시간(Detail Delay) 체크 필수
        if (!isOwnerOrEditor) {
            // 기본 공개 조건 체크
            if (!vod.is_exposed) {
                return c.json({ error: 'Access denied' }, 403);
            }

            // 시간 계산
            const publishDate = new Date(vod.publish_date);
            const detailDelay = channel.vod_detail_exposure_delay_hours || 0;
            const insightReleaseTime = new Date(publishDate.getTime() + (detailDelay * 60 * 60 * 1000));

            // 상세 공개 시간이 안 지났으면 로그 접근 불가
            if (new Date() < insightReleaseTime) {
                return c.json({
                    error: 'Detail logs are restricted.',
                    releaseAt: insightReleaseTime.toISOString()
                }, 403);
            }
        }

        const objectKey = getStreamLogKey(vod.id, logIndex);
        const object = await c.env.MY_BUCKET.get(objectKey);

        if (!object) {
            return c.json({ error: 'Log file not found' }, 404);
        }

        // ✅ [Cache Strategy: Aggressive Immutable]
        // 로그 파일은 절대 내용이 변하지 않으므로 가장 강력한 캐시 적용
        const etag = object.httpEtag;
        const ifNoneMatch = c.req.header('If-None-Match');

        if (ifNoneMatch && ifNoneMatch === etag) {
            return new Response(null, {
                status: 304,
                headers: {
                    'ETag': etag,
                    // public: CDN 캐시 가능
                    // max-age=31536000: 1년 유지
                    // immutable: 만료 전엔 서버 요청조차 하지 마라 (새로고침 시에도 캐시 사용)
                    'Cache-Control': 'public, max-age=31536000, immutable',
                }
            });
        }

        // 캐시 헤더 설정 및 응답
        const headers = new Headers();
        object.writeHttpMetadata(headers);
        headers.set('ETag', etag);
        headers.set('Cache-Control', 'public, max-age=31536000, immutable');

        return new Response(object.body, {
            headers,
        });

    } catch (e: any) {
        return c.json({ error: e.message }, 500);
    }
});

export default app;
