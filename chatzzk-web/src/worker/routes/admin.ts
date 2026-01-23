import { AUTH_DOMAIN, PasswordSchema, PlatformCodeSchema, USER_ROLE, UserIdSchema } from "@shared/constants/service_codes";
import { Hono } from "hono";
import { HonoEnv } from "../types";
import z from "zod";
import { createAdminClient } from "../utils/supabase";
import { ChannelMetadataUpdateSchema } from "@shared/types/channel";


const app = new Hono<HonoEnv>();


app.use('*', async (c, next) => {
    const user = c.get('user'); // authMiddleware에서 주입된 유저
    const supabase = c.get('supabase');

    // DB에서 실제 Role 확인 (JWT 변조 방지 및 실시간 권한 박탈 반영)
    const { data: userData, error } = await supabase
        .from('users')
        .select('role')
        .eq('supabase_uid', user.id)
        .single();

    if (error || !userData || userData.role !== USER_ROLE.ADMIN) {
        return c.json({ error: '관리자 권한이 없습니다.' }, 403);
    }

    await next();
});


async function waitForPublicUser(supabase: any, uuid: string, maxRetries = 5): Promise<number> {
    for (let i = 0; i < maxRetries; i++) {
        const { data } = await supabase
            .from('users')
            .select('id')
            .eq('supabase_uid', uuid)
            .single();

        if (data) return data.id;
        await new Promise(res => setTimeout(res, 500));
    }
    throw new Error("Public user creation timeout via Trigger");
}

app.post('/channels/provision', async (c) => {
    const adminSupabase = createAdminClient(c.env);

    // 1. 입력값 검증
    const provisionSchema = z.object({
        userId: UserIdSchema,
        password: PasswordSchema,
        platform: PlatformCodeSchema,
        channelId: z.string().min(1),
        channelName: z.string().min(1),
        // ✅ 공유 스키마를 사용하여 Camel -> Snake 자동 변환 및 기본값 적용
        metadata: ChannelMetadataUpdateSchema
    });

    const body = await c.req.json().catch(() => null);
    const parsed = provisionSchema.safeParse(body);
    if (!parsed.success) return c.json({ error: parsed.error }, 400);

    const { userId, password, platform, channelId, channelName, metadata } = parsed.data;
    const internalEmail = `${userId}@${AUTH_DOMAIN}`;
    let createdAuthUid: string | null = null;

    try {
        // ---------------------------------------------------------
        // Step 1: Auth User 생성
        // ---------------------------------------------------------
        const { data: authData, error: authError } = await adminSupabase.auth.admin.createUser({
            email: internalEmail,
            password,
            email_confirm: true,
            user_metadata: { user_name: userId }
        });

        if (authError) throw new Error(`User creation failed: ${authError.message}`);
        createdAuthUid = authData.user.id;

        const publicId = await waitForPublicUser(adminSupabase, createdAuthUid);

        const { error: updateError } = await adminSupabase
            .from('users')
            .update({ role: USER_ROLE.OWNER, user_name: userId })
            .eq('id', publicId);

        if (updateError) throw new Error(`User profile update failed: ${updateError.message}`);

        // ---------------------------------------------------------
        // Step 3: Platform ID 조회 (Hardcoding 제거)
        // ---------------------------------------------------------
        // 입력받은 platform 코드(CHZZK 등)로 DB에서 ID를 찾습니다.
        const { data: platformData, error: platformError } = await adminSupabase
            .from('platforms')
            .select('id')
            .eq('platform_code', platform)
            .single();

        if (platformError || !platformData) {
            throw new Error(`Invalid platform code: ${platform}. Database lookup failed.`);
        }

        // ---------------------------------------------------------
        // Step 4: Channel 생성
        // ---------------------------------------------------------
        const { data: channelData, error: channelError } = await adminSupabase
            .from('channels')
            .insert({
                platform_id: platformData.id,
                platform_channel_id: channelId,
                channel_name: channelName,
                user_id: publicId,
                is_collection_enabled: true
            })
            .select().single();

        if (channelError) {
            if (channelError.code === '23505') throw new Error('이미 등록된 채널입니다.');
            throw new Error(`Channel creation failed: ${channelError.message}`);
        }

        // ---------------------------------------------------------
        // Step 5: Channel Metadata 생성
        // ---------------------------------------------------------
        const { error: metaError } = await adminSupabase
            .from('channel_metadata')
            .insert({
                channel_id: channelData.id,
                attributes: metadata // JSONB
            });

        if (metaError) throw new Error(`Metadata creation failed: ${metaError.message}`);

        // ---------------------------------------------------------
        // Success
        // ---------------------------------------------------------
        return c.json({
            success: true,
            data: {
                user: { id: publicId, userName: userId, email: internalEmail },
                channel: channelData,
                metadata: metadata
            }
        }, 201);

    } catch (e: any) {
        // 🚨 롤백 로직 (Compensation Transaction)
        // Auth User 삭제 -> (Cascade) Public User 삭제 -> Channel 삭제 -> Metadata 삭제
        if (createdAuthUid) {
            console.warn(`[Rollback] Deleting user ${createdAuthUid} due to error: ${e.message}`);
            await adminSupabase.auth.admin.deleteUser(createdAuthUid);
        }

        return c.json({ error: e.message }, 500);
    }
});

app.post('/channels', async (c) => {
    const adminSupabase = createAdminClient(c.env);

    // 1. 요청 바디 검증 스키마 (CamelCase 입력)
    const bodySchema = z.object({
        platform: PlatformCodeSchema,
        channelId: z.string().min(1),
        channelName: z.string().min(1),

        // 매핑 옵션
        shouldLinkUser: z.boolean().default(false),
        targetUserName: z.string().optional(),

        // 메타데이터 (CamelCase -> SnakeCase 자동 변환 스키마 사용)
        metadata: ChannelMetadataUpdateSchema
    });

    const body = await c.req.json().catch(() => null);
    const parsed = bodySchema.safeParse(body);

    if (!parsed.success) {
        return c.json({ error: 'Invalid Input', details: parsed.error.format() }, 400);
    }

    const { platform, channelId, channelName, shouldLinkUser, targetUserName, metadata } = parsed.data;

    try {
        // 2. RPC 호출
        // metadata는 ChannelMetadataUpdateSchema 덕분에 이미 SnakeCase 객체로 변환되어 있음 ({ streamer_nicknames: ... })
        const { data, error } = await adminSupabase.rpc('add_new_channel_with_metadata', {
            p_platform_code: platform,
            p_platform_channel_id: channelId,
            p_channel_name: channelName,
            p_attributes: metadata, // JSONB로 저장될 객체
            p_target_user_name: shouldLinkUser ? targetUserName : null // 매핑 안 하면 null 전달
        });

        if (error) {
            // RPC 내부에서 RAISE EXCEPTION 한 메시지가 error.message로 옴
            if (error.message.includes('Channel already exists')) {
                return c.json({ error: '이미 등록된 채널입니다.' }, 409);
            }
            if (error.message.includes('User not found')) {
                return c.json({ error: '입력한 아이디의 유저를 찾을 수 없습니다.' }, 404);
            }
            throw error; // 그 외 에러는 500 처리
        }

        return c.json({ success: true, data });

    } catch (e: any) {
        console.error("Channel Add Error:", e);
        return c.json({ error: e.message || 'Internal Server Error' }, 500);
    }
});

// GET /api/admin/channels/detail?platform=CHZZK&channelId=...
app.get('/channels/detail', async (c) => {
    const { platform, channelId } = c.req.query();
    const adminSupabase = createAdminClient(c.env);

    // Join을 통해 user_name(소유자), platform_code, metadata 통째로 조회
    const { data, error } = await adminSupabase
        .from('channels')
        .select(`
            *,
            platform:platforms!inner(platform_code),
            owner:users!channels_user_id_fkey(user_name),
            channel_metadata(attributes)
        `)
        .eq('platform.platform_code', platform)
        .eq('platform_channel_id', channelId)
        .single();

    if (error || !data) return c.json({ error: 'Channel not found' }, 404);

    // 응답 전 CamelCase 변환 (선택 사항, 프론트에서 할 수도 있음)
    // 여기서는 Raw Data를 주고 프론트 Zod 스키마로 파싱하는 것을 추천
    return c.json({ data });
});

// 2. 일반 정보 및 메타데이터 수정 (안전한 작업)
// PUT /api/admin/channels/:id/general
app.put('/channels/:id/general', async (c) => {
    const id = c.req.param('id');
    const body = await c.req.json();
    const adminSupabase = createAdminClient(c.env);

    const schema = z.object({
        channelName: z.string().min(1),
        isCollectionEnabled: z.boolean(),
        // ✅ 추가: 이미 프론트 Zod에서 number로 변환되어 넘어옴
        vodExposureDelayHours: z.number().min(0),
        vodDetailExposureDelayHours: z.number().min(0),

        metadata: ChannelMetadataUpdateSchema
    });

    const parsed = schema.safeParse(body);
    if (!parsed.success) return c.json({ error: 'Invalid Input', details: parsed.error }, 400);

    const {
        channelName,
        isCollectionEnabled,
        vodExposureDelayHours,
        vodDetailExposureDelayHours,
        metadata
    } = parsed.data;

    // 2. Channel 테이블 업데이트 (일반 정보)
    const { error: chError } = await adminSupabase
        .from('channels')
        .update({
            channel_name: channelName,
            is_collection_enabled: isCollectionEnabled,
            // ✅ 추가: CamelCase -> SnakeCase 매핑
            vod_exposure_delay_hours: vodExposureDelayHours,
            vod_detail_exposure_delay_hours: vodDetailExposureDelayHours,
            updated_at: new Date().toISOString()
        })
        .eq('id', id);

    if (chError) return c.json({ error: chError.message }, 500);

    // 메타데이터 Update (Upsert)
    const { error: metaError } = await adminSupabase
        .from('channel_metadata')
        .upsert({
            channel_id: id,
            attributes: metadata // SnakeCase로 변환된 값
        }, { onConflict: 'channel_id' });

    if (metaError) return c.json({ error: metaError.message }, 500);

    return c.json({ success: true });
});

// 3. 소유권 이전 (위험 작업)
// POST /api/admin/channels/:id/transfer-ownership
app.post('/channels/:id/transfer-ownership', async (c) => {
    const id = c.req.param('id');
    const { targetUserName } = await c.req.json();
    const adminSupabase = createAdminClient(c.env);

    const { data, error } = await adminSupabase.rpc('transfer_channel_ownership', {
        p_channel_id: id,
        p_new_user_name: targetUserName
    });

    if (error) return c.json({ error: error.message }, 400); // 400 Bad Request (검증 실패 등)
    return c.json({ success: true, data });
});


export default app;
