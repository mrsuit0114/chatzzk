import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone";
import relativeTime from "dayjs/plugin/relativeTime";
import "dayjs/locale/ko"; // 한국어 데이터 로드

// 1. 전역 설정 (딱 한 번만 수행됨)
dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.extend(relativeTime);

// 2. 기본 로케일 설정
dayjs.locale("ko");

// 3. (선택) 기본 타임존을 한국으로 고정하고 싶다면
// dayjs.tz.setDefault("Asia/Seoul");

export default dayjs;
