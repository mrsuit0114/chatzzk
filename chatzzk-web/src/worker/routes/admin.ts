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

export default app;
