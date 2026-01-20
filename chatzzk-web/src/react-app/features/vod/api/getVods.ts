import { api } from "@/lib/api";
import dayjs from "dayjs";

// 파라미터 타입 정의
type GetVodsParams = {
    platform: string;
    page: number;
    query?: string;
    from?: string | null;
    to?: string | null;
    channelId?: string | null;
};

// 응답 데이터 타입 정의 (백엔드와 맞춤)
type VodResponse = {
    data: any[]; // 구체적인 타입(VodData)을 넣으면 더 좋습니다
    meta: {
        total: number;
        page: number;
        pageSize: number;
        totalPages: number;
    };
};

export const getVods = async ({ platform, page, query, from, to, channelId }: GetVodsParams): Promise<VodResponse> => {
    const fromDateUTC = from
        ? dayjs(from).startOf('day').toISOString()
        : undefined;
    const toDateUTC = to
        ? dayjs(to).endOf('day').toISOString()
        : undefined;

    const response = await api.get('/vods', {
        params: {
            platform,
            page,
            query,
            from: fromDateUTC,
            to: toDateUTC,
            channelId,
        },
    });
    return response.data;
};
