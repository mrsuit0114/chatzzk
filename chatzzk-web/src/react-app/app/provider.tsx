import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            // 중요: 창을 다시 포커스했을 때 자동으로 재요청하는 기능 끄기 (원하면 켜도 됨)
            refetchOnWindowFocus: false,
            // 데이터가 '상했다'고 판단하는 시간 (기본 0초 -> 즉시 상함)
            // 여기서는 5분으로 설정하여 뒤로가기 시 재요청을 막습니다.
            staleTime: 1000 * 60 * 5,
        },
    },
});
