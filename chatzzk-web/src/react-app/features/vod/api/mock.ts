import { VodCardUI } from "../types";


// 실제로는 API에서 받아올 데이터 형태입니다.
export const MOCK_VOD_DATA: VodCardUI[] = [
    {
        vodId: 101,
        channelId: 1,
        title: "침착맨의 휴식 방송 다시보기",
        thumbnailUrl: "https://placehold.co/600x400", // 임시 이미지
        channelName: "침착맨",
        platform: "chzzk",
        publishDate: "2024-01-01",
        duration: "3시간 10분",
    },
    {
        vodId: 102,
        channelId: 2,
        title: "배도라지 합방 하이라이트",
        channelName: "배도라지",
        platform: "youtube",
        publishDate: "2023-12-25",
        duration: "45분 20초",
    },
]
