import type { RawDashboardResponse } from "@shared/schemas/vod-analysis";

const SEGMENT_COUNT = 24; // 2시간 / 5분
const CLIP_COUNT = 240;   // 2시간 / 30초

function randFloat(min: number, max: number, dp = 3) {
    return parseFloat((Math.random() * (max - min) + min).toFixed(dp));
}

function makePeak(segStart: number, clipStep: number) {
    const offset = Math.floor(Math.random() * 10) * clipStep;
    return {
        peakTs: segStart + offset,
        peakVl: randFloat(0.3, 1.0),
        peakMmt: randFloat(-2.0, 2.0),
    };
}

const atmoPool = ["중립", "폭소", "감탄", "기대", "슬픔", "격려", "분노", "야유"] as const;

const segmentTexts = [
    "스트리머가 오프닝 인사를 하며 방송을 시작했습니다. 오늘의 게임 콘텐츠와 진행 방향을 소개했고 시청자들이 반갑게 입장했습니다.",
    "첫 번째 게임 라운드를 플레이했습니다. 초반에 무난한 출발을 보였으나 예상치 못한 상황에서 시청자 반응이 폭발적으로 증가했습니다.",
    "챗팅 이벤트를 진행하며 시청자와 소통했습니다. 다양한 주제로 자유롭게 대화를 나누었고 분위기가 한층 무르익었습니다.",
    "예상치 못한 상황이 발생해 스트리머가 당황하는 모습을 보였습니다. 시청자들의 응원과 웃음이 이어졌습니다.",
    "게임 플레이 중 결정적인 순간이 왔습니다. 높은 집중력을 보여주었고 시청자들의 응원이 폭발적으로 증가했습니다.",
    "잠깐의 휴식 시간을 갖고 시청자와 일상적인 대화를 나누었습니다. 편안한 분위기 속에서 다양한 이야기가 오갔습니다.",
    "신규 컨텐츠를 도입하며 방송에 새로운 활력을 불어넣었습니다. 시청자들의 기대감이 높아지는 구간이었습니다.",
    "화제의 영상 클립을 함께 시청하며 반응을 나누었습니다. 재미있는 장면에서 채팅이 빠르게 증가했습니다.",
    "팬들의 후원 메시지를 읽으며 감사 인사를 전했습니다. 감동적인 메시지에 스트리머와 시청자 모두 뭉클했습니다.",
    "게임의 어려운 구간을 도전했습니다. 여러 번 실패에도 포기하지 않는 모습에 시청자들의 격려가 이어졌습니다.",
    "드디어 어려운 구간을 돌파했습니다. 스트리머와 시청자가 함께 환호하며 최고조의 분위기를 만들었습니다.",
    "잠시 다른 주제로 넘어가 최근 화제에 대한 이야기를 나누었습니다. 다양한 의견이 채팅을 통해 오갔습니다.",
    "오늘 방송의 하이라이트 영상을 다시 보며 추억을 나누었습니다. 재미있는 순간들을 돌아보며 웃음이 넘쳤습니다.",
    "시청자 참여 게임을 진행했습니다. 운이 따라주지 않는 결과에도 유머 있게 마무리했습니다.",
    "게임 전략을 분석하며 다음 라운드를 준비했습니다. 분석적인 시각과 유머가 조화를 이루었습니다.",
    "도전 미션을 받아 수행했습니다. 예상보다 어려운 난이도에 고전했지만 끝까지 포기하지 않았습니다.",
    "방송 중반부 정리를 하며 진행 상황을 공유했습니다. 앞으로의 방향에 대해 시청자와 소통했습니다.",
    "특별 게스트가 등장해 방송이 더욱 활기를 띠었습니다. 두 사람의 케미가 시청자들에게 큰 재미를 선사했습니다.",
    "게스트와 함께 미니 게임을 즐겼습니다. 경쟁과 웃음이 어우러진 즐거운 시간이었습니다.",
    "게스트와의 대화가 깊어졌습니다. 진솔한 이야기들이 시청자들에게 감동과 공감을 주었습니다.",
    "게스트가 퇴장하고 마무리 게임을 진행했습니다. 게스트에 대한 아쉬움과 함께 다음을 기약했습니다.",
    "오늘의 하이라이트를 함께 돌아보는 시간을 가졌습니다. 여러 재미있는 순간들을 리뷰하며 웃음이 가득했습니다.",
    "시청자 질문 응답 시간을 가졌습니다. 다양한 질문에 솔직하고 재치 있는 답변을 전했습니다.",
    "방송 마무리를 하며 오늘의 감사 인사를 전했습니다. 다음 방송 예고와 함께 따뜻하게 마무리했습니다.",
];

const keywordPool = [
    ["게임", "클리어", "도전"],
    ["시청자", "소통", "채팅"],
    ["후원", "감사", "메시지"],
    ["유머", "웃음", "분위기"],
    ["전략", "분석", "집중"],
    ["이벤트", "참여", "경쟁"],
    ["게스트", "케미", "협력"],
    ["하이라이트", "리뷰", "순간"],
    ["격려", "응원", "끈기"],
    ["마무리", "예고", "다음"],
];

const clipVolumes = Array.from({ length: CLIP_COUNT }, (_, i) => {
    const base = Math.sin(i / 20) * 0.2 + 0.4;
    const noise = (Math.random() - 0.5) * 0.15;
    const spike = (i === 80 || i === 140 || i === 200) ? 0.35 : 0;
    return Math.min(1, Math.max(0, parseFloat((base + noise + spike).toFixed(3))));
});

const clipMomentums = clipVolumes.map((v, i) => {
    if (i === 0) return 0;
    return parseFloat((v - clipVolumes[i - 1]).toFixed(3));
});

const SEGMENT_STEP = 300000;  // 5분 ms
const CLIP_STEP = 30000;       // 30초 ms

const segmentVolumes = Array.from({ length: SEGMENT_COUNT }, (_, i) => {
    const sliceStart = i * 10;
    const slice = clipVolumes.slice(sliceStart, sliceStart + 10);
    return parseFloat((slice.reduce((a, b) => a + b, 0) / slice.length).toFixed(3));
});

const segmentMomentums = segmentVolumes.map((v, i) => {
    if (i === 0) return 0;
    return parseFloat((v - segmentVolumes[i - 1]).toFixed(3));
});

const segments = Array.from({ length: SEGMENT_COUNT }, (_, i) => {
    const startMs = i * SEGMENT_STEP;
    return {
        txt: segmentTexts[i % segmentTexts.length],
        kwd: keywordPool[i % keywordPool.length],
        atmo: atmoPool[i % atmoPool.length],
        volPeak: makePeak(startMs, CLIP_STEP),
        mmtPeak: makePeak(startMs, CLIP_STEP),
    };
});

const chapterTitles = [
    "오프닝 & 초반 게임 플레이",
    "시청자 소통 & 이벤트",
    "게스트 등장 & 협력 게임",
    "마무리 & 하이라이트 리뷰",
];

const chapters = chapterTitles.map((title, ci) => {
    const keyTopics = Array.from({ length: 4 }, (_, ti) => {
        const segIndex = ci * 6 + ti * 1;
        const totalMinutes = Math.floor((segIndex * SEGMENT_STEP) / 60000);
        const hh = String(Math.floor(totalMinutes / 60)).padStart(2, "0");
        const mm = String(totalMinutes % 60).padStart(2, "0");
        const topics = [
            "방송 시작 및 인사",
            "첫 번째 게임 시작",
            "채팅 이벤트 진행",
            "예상치 못한 상황 발생",
            "팬 후원 메시지 읽기",
            "어려운 구간 도전",
            "게스트 입장",
            "미니 게임 대결",
            "진솔한 이야기",
            "하이라이트 리뷰",
            "시청자 Q&A",
            "마무리 인사",
        ];
        return { timestamp: `${hh}:${mm}`, topic: topics[(ci * 4 + ti) % topics.length] };
    });
    return { title, keyTopics };
});

export const MOCK_ANALYSIS_DATA: RawDashboardResponse = {
    version: "1.0",
    metaInfo: {
        platform: "CHZZK",
        title: "【미리보기 모드】 테스트 방송 - Mock 데이터입니다",
        channelId: "mock_channel_01",
        channelName: "Mock 채널",
        videoNo: "mock_video_001",
        publishDate: "2025-01-15T14:00:00+09:00",
        duration: 7200,
        intervals: {
            chapterStep: 1800000,
            segmentStep: SEGMENT_STEP,
            clipStep: CLIP_STEP,
        },
    },
    stats: {
        clip: { volume: clipVolumes, momentum: clipMomentums },
        segment: { volume: segmentVolumes, momentum: segmentMomentums },
        atmosphereRatio: {
            "중립": 30.0,
            "폭소": 28.0,
            "감탄": 15.0,
            "기대": 12.0,
            "격려": 8.0,
            "슬픔": 4.0,
            "분노": 2.0,
            "야유": 1.0,
        },
    },
    segments,
    chapters,
};
