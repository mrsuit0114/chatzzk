// dto - db와 백엔드와의 경계
import { z } from 'zod';
import { UserRoleSchema } from "@shared/constants/service_codes";


export const UserProfileSchema = z.object({
    // 입력(Input): DB에서 들어오는 snake_case 데이터
    id: z.number(),
    supabase_uid: z.string(),
    user_name: z.string(),
    role: UserRoleSchema,
    created_at: z.string(),
}).transform((data) => ({
    // 출력(Output): 앱에서 사용할 camelCase 데이터로 변환 (Mapping)
    id: data.id,
    supabaseUid: data.supabase_uid,
    userName: data.user_name,
    role: data.role,
    createdAt: data.created_at,
}));

export type UserProfile = z.infer<typeof UserProfileSchema>;
