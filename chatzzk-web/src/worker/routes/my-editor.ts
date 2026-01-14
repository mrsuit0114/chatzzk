import { Hono } from 'hono';
import { z } from 'zod';
import { HonoEnv } from '../types';
import { createAdminClient } from '../utils/supabase';
import { AUTH_DOMAIN, BAN_DURATION, ID_REGEX, PASSWORD_MIN_LENGTH, USER_ROLE } from '@shared/constants/service_codes';

const app = new Hono<HonoEnv>();


/**
 * [Helper] 요청자가 소유한 채널 정보와 현재 편집자 ID 조회
 * - 일반 권한(createAuthClient)을 사용하여 RLS를 준수하며 조회함.
 * - 소유자가 아니면 데이터가 조회되지 않으므로 자연스럽게 차단됨.
 */
async function getOwnerChannel(c: any) {
    const supabase = c.get('supabase');
    const user = c.get('user'); // UUID

    // 1. UUID -> Owner의 Integer ID 변환
    const { data: userData, error: userError } = await supabase
        .from('users')
        .select('id')
        .eq('supabase_uid', user.id)
        .single();

    if (userError || !userData) throw new Error('Internal user profile not found');

    // 2. 채널 조회
    const { data: channel, error } = await supabase
        .from('channels')
        .select('id, editor_id') // editor_id는 Integer
        .eq('user_id', userData.id)
        .single();

    if (error || !channel) throw new Error('Channel not found');

    return channel;
}

/**
 * 1. GET /api/my/editor
 * 현재 편집자 계정 상태 조회
 */
app.get('/', async (c) => {
    try {
        const channel = await getOwnerChannel(c);

        // 연결된 편집자가 없음
        if (!channel.editor_id) return c.json({ data: null });

        // 1. Public User 테이블에서 UUID 찾기 (Admin 권한 필요)
        const adminSupabase = createAdminClient(c.env);
        const { data: publicEditor, error: publicError } = await adminSupabase
            .from('users')
            .select('supabase_uid')
            .eq('id', channel.editor_id) // Integer ID로 조회
            .single();

        if (publicError || !publicEditor || !publicEditor.supabase_uid) {
            // DB 정합성 깨짐 (채널에는 있는데 users 테이블에 없음)
            return c.json({ data: null });
        }

        // 2. Auth User 조회 (UUID 사용)
        const { data: { user: editorUser }, error: authError } = await adminSupabase.auth.admin.getUserById(publicEditor.supabase_uid);

        if (authError || !editorUser) return c.json({ data: null });

        const editorId = editorUser.email?.replace(`@${AUTH_DOMAIN}`, '') || '';
        const isBanned = editorUser.banned_until && new Date(editorUser.banned_until) > new Date();

        return c.json({
            data: {
                id: editorId,
                isActive: !isBanned,
            }
        });

    } catch (e: any) {
        return c.json({ error: e.message }, 500);
    }
});
/**
 * 2. POST /api/my/editor
 * 편집자 계정 생성 (최초 1회)
 */
app.post('/', async (c) => {
    const adminSupabase = createAdminClient(c.env);

    // ✅ 상수 정규식 활용
    const schema = z.object({
        id: z.string().regex(ID_REGEX, "아이디는 4~20자의 영문 소문자와 숫자만 가능합니다."),
        password: z.string().min(PASSWORD_MIN_LENGTH, `비밀번호는 최소 ${PASSWORD_MIN_LENGTH}자 이상이어야 합니다.`)
    });

    const body = await c.req.json().catch(() => null);
    const parsed = schema.safeParse(body);
    if (!parsed.success) return c.json({ error: parsed.error }, 400);

    const { id, password } = parsed.data;
    const email = `${id}@${AUTH_DOMAIN}`; // ✅ 상수 도메인

    try {
        const channel = await getOwnerChannel(c);

        // ✅ [1채널 1편집자 제약]
        // 이미 editor_id가 존재하면 추가 생성을 막음
        if (channel.editor_id) {
            return c.json({ error: '이미 편집자 계정이 존재합니다. 기존 계정을 수정하거나 관리하세요.' }, 409);
        }

        // 2. Auth 유저 생성 (Admin)
        const { data: newUser, error: createError } = await adminSupabase.auth.admin.createUser({
            email: email,
            password: password,
            email_confirm: true,
            user_metadata: { role: USER_ROLE.EDITOR }
        });

        if (createError) {
            // 이미 존재하는 아이디(이메일)인 경우 처리
            if (createError.message.includes('already has been registered')) {
                return c.json({ error: '이미 사용 중인 아이디입니다.' }, 409);
            }
            throw createError;
        }
        if (!newUser.user) throw new Error('Failed to create user');

        const newUuid = newUser.user.id;

        // 2. Public User ID 가져오기 (Trigger 지연 고려하여 Retry 로직 필요할 수 있음)
        // 여기서는 간단히 바로 조회하되, Trigger가 없다면 수동 insert가 필요할 수 있음.
        let newPublicId: number | null = null;

        // 최대 3초간 Public User 생성을 기다림 (Trigger 지연 대비)
        for (let i = 0; i < 6; i++) {
            const { data } = await adminSupabase.from('users').select('id').eq('supabase_uid', newUuid).single();
            if (data) {
                newPublicId = data.id;
                break;
            }
            await new Promise(res => setTimeout(res, 500)); // 0.5초 대기
        }

        if (!newPublicId) {
            // Trigger 실패 혹은 지연 -> 롤백(Auth 삭제) 후 에러
            await adminSupabase.auth.admin.deleteUser(newUuid);
            throw new Error('Public user profile creation failed (Trigger timeout).');
        }

        // 3. 채널 업데이트 (Integer ID 연결)
        const { error: updateError } = await adminSupabase
            .from('channels')
            .update({ editor_id: newPublicId }) // Integer ID 저장
            .eq('id', channel.id);

        if (updateError) {
            await adminSupabase.auth.admin.deleteUser(newUuid); // 롤백
            throw updateError;
        }

        return c.json({ success: true });

    } catch (e: any) {
        return c.json({ error: e.message }, 500);
    }
});
/**
 * 3. PUT /api/my/editor
 * 편집자 정보 수정 (ID/PW)
 */
app.put('/', async (c) => {
    const adminSupabase = createAdminClient(c.env);

    const schema = z.object({
        id: z.string().regex(ID_REGEX).optional(),
        password: z.string().min(PASSWORD_MIN_LENGTH).optional()
    });

    const body = await c.req.json().catch(() => null);
    const parsed = schema.safeParse(body);
    if (!parsed.success) return c.json({ error: parsed.error }, 400);

    const { id: newId, password } = parsed.data;

    try {
        const channel = await getOwnerChannel(c);
        if (!channel.editor_id) return c.json({ error: 'Editor not found' }, 404);

        // Integer ID로 UUID 찾기
        const { data: publicEditor } = await adminSupabase
            .from('users')
            .select('supabase_uid, user_name')
            .eq('id', channel.editor_id)
            .single();

        if (!publicEditor?.supabase_uid) throw new Error('Public user not found');

        const isIdChanged = newId && newId !== publicEditor.user_name;

        // 2. ID 변경 요청이 있는 경우 중복 검사
        if (isIdChanged) {
            const { data: existingUser } = await adminSupabase
                .from('users')
                .select('id')
                .eq('user_name', newId)
                .single();

            if (existingUser) {
                return c.json({ error: '이미 사용 중인 아이디입니다.' }, 409);
            }
        }

        const updateData: any = {};
        if (password) updateData.password = password;
        if (isIdChanged) updateData.email = `${newId}@${AUTH_DOMAIN}`; // 변경된 경우에만 이메일 업데이트

        // 변경할 내용이 없으면 바로 리턴 (최적화)
        if (Object.keys(updateData).length === 0) {
            return c.json({ success: true });
        }

        const { error: authError } = await adminSupabase.auth.admin.updateUserById(
            publicEditor.supabase_uid,
            updateData
        );

        if (authError) throw authError;

        if (newId) {
            const { error: dbError } = await adminSupabase
                .from('users')
                .update({ user_name: newId })
                .eq('id', channel.editor_id);

            if (dbError) {
                // 매우 드문 경우지만, 여기서 에러나면 Auth는 바뀌었는데 DB는 안 바뀐 상태가 됨.
                // 로그를 남기거나, Auth를 롤백해야 함. (여기선 로그 처리)
                throw new Error('ID update partially failed. Please contact support.');
            }
        }

        return c.json({ success: true });

    } catch (e: any) {
        return c.json({ error: e.message }, 500);
    }
});

/**
 * 4. PATCH /api/my/editor/status
 * 계정 활성/비활성 토글 (Ban 처리)
 */
app.patch('/status', async (c) => {
    const adminSupabase = createAdminClient(c.env);
    const schema = z.object({ isActive: z.boolean() });
    const body = await c.req.json().catch(() => null);
    const parsed = schema.safeParse(body);
    if (!parsed.success) return c.json({ error: 'Invalid body' }, 400);

    try {
        const channel = await getOwnerChannel(c);
        if (!channel.editor_id) return c.json({ error: 'Editor not found' }, 404);

        const { data: publicEditor } = await adminSupabase
            .from('users')
            .select('supabase_uid')
            .eq('id', channel.editor_id)
            .single();

        if (!publicEditor?.supabase_uid) throw new Error('Public user not found');

        const banDuration = parsed.data.isActive ? 'none' : BAN_DURATION;

        const { error } = await adminSupabase.auth.admin.updateUserById(
            publicEditor.supabase_uid,
            { ban_duration: banDuration }
        );

        if (error) throw error;
        return c.json({ success: true });

    } catch (e: any) {
        return c.json({ error: e.message }, 500);
    }
});

export default app;
