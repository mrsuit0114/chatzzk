import { addDays, isAfter, isBefore } from "date-fns"; // npm install date-fns
import { useAuthStore } from "@/stores/auth.store";
import { USER_ROLE } from "@/constants";


interface InsightAccessParams {
    publishDate: Date | string;    // VOD 게시일
    insightOpenDays: number;       // 채널 설정: 며칠 뒤 공개할지 (0이면 즉시 공개, -1이면 영구 비공개 등)
    channelOwnerId: string;        // 채널 소유자 ID
}

export function useInsightAccess({ publishDate, insightOpenDays, channelOwnerId }: InsightAccessParams) {
    const user = useAuthStore((state) => state.user);

    // 1. [권한 체크] 로그인한 유저가 소유자이거나 편집자인가?
    const isOwner = user?.id === channelOwnerId; // 실제로는 user.id와 ownerId 비교
    const isEditor = user?.role === USER_ROLE.EDITOR; // 또는 채널별 권한 체크 로직

    if (isOwner || isEditor) {
        return {
            isLocked: false,
            reason: "관리자 권한으로 접근 가능합니다."
        };
    }

    // 2. [설정 체크] 영구 비공개 설정인 경우 (-1 같은 특수값 약속)
    if (insightOpenDays < 0) {
        return {
            isLocked: true,
            reason: "채널 소유자가 분석 데이터를 비공개로 설정했습니다."
        };
    }

    // 3. [날짜 체크] 게시일로부터 설정된 날짜가 지났는가?
    const published = new Date(publishDate);
    const openDate = addDays(published, insightOpenDays); // 공개 예정일 계산
    const now = new Date();

    // 현재 시간이 공개 예정일보다 이전이면 잠금
    if (isBefore(now, openDate)) {
        // 남은 일수 계산 등을 추가로 리턴할 수도 있음
        return {
            isLocked: true,
            reason: `상세 분석은 방송일로부터 ${insightOpenDays}일 뒤에 공개됩니다. (${openDate.toLocaleDateString()} 공개 예정)`
        };
    }

    // 4. 모든 조건 통과
    return {
        isLocked: false,
        reason: null
    };
}
