import { api } from "@/lib/api";
import { ChannelDetailData } from "@shared/types/channel";

type ChannelDetailResponse = {
    data: ChannelDetailData;
};

/**
 * 채널 상세 정보를 조회합니다.
 * @param channelId - 플랫폼 채널 ID
 * @param platform - 플랫폼 코드 (ex: chzzk, youtube)
 */
export const getChannelDetail = async (channelId: string, platform: string): Promise<ChannelDetailResponse> => {
    // ✅ 변경: URL은 ID까지만, Platform은 params로 전달
    // 결과 요청 URL: /channels/abcd123?platform=CHZZK
    const response = await api.get<ChannelDetailResponse>(`/channels/${channelId}`, {
        params: {
            platform: platform.toUpperCase() // 대문자 변환 안전장치
        }
    });

    return response.data;
};
