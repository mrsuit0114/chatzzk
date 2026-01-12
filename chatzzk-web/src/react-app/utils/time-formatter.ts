import { format } from "date-fns";
import { ko } from "date-fns/locale";

export const formatVideoTime = (ms: number): string => {
    const totalSeconds = Math.floor(ms / 1000);
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    // 1시간 이상이면 1:05, 미만이면 0:05 형태로 출력
    return h > 0
        ? `${h}:${String(m).padStart(2, '0')}`
        : `0:${String(m).padStart(2, '0')}`;
};

export const formatTime = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = totalSeconds % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
};

export const formatInterval = (ms: number) => {
    const minutes = Math.floor(ms / 60000);
    return `${minutes}min`;
};

export const formatDateKo = (dateStr: string) => {
    const date = new Date(dateStr);
    return format(date, "yyyy.MM.dd", { locale: ko });
}
