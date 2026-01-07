/**
 * 시간순 정렬된 데이터에서 특정 타임스탬프가 포함된 세그먼트의 인덱스를 이진 탐색으로 찾습니다.
 * 구간: [startTime, endTime) (Start 포함, End 제외)
 */
export function findSegmentIndexBinary(
    data: { startTime: number; endTime: number }[],
    targetTime: number
): number {
    let left = 0;
    let right = data.length - 1;

    while (left <= right) {
        const mid = Math.floor((left + right) / 2);
        const segment = data[mid];

        // 1. 범위 안에 있는 경우 (Start <= T < End)
        if (targetTime >= segment.startTime && targetTime < segment.endTime) {
            return mid;
        }

        // 2. Target이 더 작은 경우 (왼쪽 탐색)
        if (targetTime < segment.startTime) {
            right = mid - 1;
        }
        // 3. Target이 더 큰 경우 (오른쪽 탐색)
        else {
            left = mid + 1;
        }
    }

    // 예외 처리: 영상의 정확한 마지막 종료 시간인 경우 마지막 세그먼트 반환
    // (보통 endTime은 포함하지 않으므로 마지막 1ms 때문에 놓칠 수 있음)
    if (data.length > 0 && targetTime === data[data.length - 1].endTime) {
        return data.length - 1;
    }

    return -1; // 찾지 못함
}


export const scaleMomentum = (value: number) => {
    // 1. Clip: -3보다 작으면 -3, 3보다 크면 3
    const clipped = Math.max(-3, Math.min(3, value));
    // 2. Scale: (-3 -> 0), (0 -> 0.5), (3 -> 1)
    return (clipped + 3) / 6;
};
