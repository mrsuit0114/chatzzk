import { api } from "@/lib/api";
import { Password, PlatformCode, UserId } from "@shared/constants/service_codes";
import { ChannelMetadata } from "@shared/types/channel";

// 요청 데이터 타입 정의 (백엔드와 스펙 일치)
export type ProvisionRequest = {
    userId: UserId;
    password: Password;
    platform: PlatformCode;
    channelId: string;
    channelName: string;
    // ✅ 내부 필드를 일일이 적지 않고 공통 타입을 재사용 (CamelCase)
    metadata: ChannelMetadata;
};

// 응답 데이터 타입 정의 (필요시 구체화)
export type ProvisionResponse = {
    success: boolean;
    data: {
        user: { id: number; email: string; userName: string };
        channel: { id: number; channel_name: string };
        metadata: any;
    };
};

/**
 * 채널 및 유저 통합 프로비저닝 API
 * POST /api/admin/channels/provision
 */
export const provisionChannel = async (params: ProvisionRequest): Promise<ProvisionResponse> => {
    // api 인스턴스(Axios)가 Interceptor를 통해 Authorization 헤더를 자동으로 붙여준다고 가정합니다.
    const { data } = await api.post<ProvisionResponse>('/admin/channels/provision', params);
    return data;
};
