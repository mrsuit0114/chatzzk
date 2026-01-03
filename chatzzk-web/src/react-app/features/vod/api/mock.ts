import { VodCardUI } from "../types";


// 실제로는 API에서 받아올 데이터 형태입니다.
export const MOCK_VOD_DATA: VodCardUI[] = [
    {
        videoNo: "a1b2c3d4e5f6g7h8i9j0",
        platformChannelId: "4312fsadfasf3fasdfas",
        title: "침착맨의 휴식 방송 다시보기",
        channelName: "침착맨",
        thumbnailUrl: "https://placehold.co/600x400", // 임시 이미지
        publishDate: "2024-01-01",
        duration: "3시간 10분",
        platform: "chzzk",
    },
    {
        videoNo: "b2c3d4e5f6g7h8i9j0k1",
        platformChannelId: "asdfasf3fasdfas4312fsadf",
        title: "배도라지 합방 하이라이트",
        channelName: "배도라지",
        publishDate: "2023-12-25",
        duration: "45분 20초",
        platform: "youtube",
    },
]
