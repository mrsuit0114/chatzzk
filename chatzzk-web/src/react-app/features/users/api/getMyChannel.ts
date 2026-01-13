import { api } from "@/lib/api";
import { MyChannelData } from "@shared/types/channel";

type MyChannelResponse = {
    data: MyChannelData;
};

export const getMyChannel = async (): Promise<MyChannelResponse> => {
    // axios interceptor가 자동으로 Authorization 헤더를 붙여준다고 가정합니다.
    // (로그인 상태이므로 토큰이 있을 것임)
    const response = await api.get<MyChannelResponse>('/my/channel');
    return response.data;
};
