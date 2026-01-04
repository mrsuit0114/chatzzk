// features/vod/components/highlight/mock.ts
import type { SegmentSummaryData } from "./types";

export const MOCK_SEGMENTS: SegmentSummaryData[] = [
    {
        id: "seg-1",
        chapterId: "ch-1",
        startTime: 300000, // 00:02:05
        endTime: 600000,
        atmosphere: "Funny",
        summary: "침착맨이 삼국지 유비의 귀 큰 특징을 설명하며 역대급 비유를 시전하는 장면.침착맨이 삼국지 유비의 귀 큰 특징을 설명하며 역대급 비유를 시전하는 장면.침착맨이 삼국지 유비의 귀 큰 특징을 설명하며 역대급 비유를 시전하는 장면.침착맨이 삼국지 유비의 귀 큰 특징을 설명하며 역대급 비유를 시전하는 장면.침착맨이 삼국지 유비의 귀 큰 특징을 설명하며 역대급 비유를 시전하는 장면. 시청자들이 채팅창에서 폭발적인 반응을 보임.",
        keywords: ["유비", "귀큰놈", "폭소"],
        momentum: 15.2,
        volume: 1200,
        score: 9.5,
        volPeak: { timestamp: 360000, volume: 0.58, momentum: 2.12 },
        mmtPeak: { timestamp: 390000, volume: 0.33, momentum: 2.81 },
    },
    {
        id: "seg-2",
        chapterId: "ch-1",
        startTime: 4500000, // 00:07:30
        endTime: 4800000,
        atmosphere: "Tension",
        summary: "조조가 등장하며 분위기가 반전되는 순간. 배경음악과 함께 긴장감이 고조됨.",
        keywords: ["조조", "등장", "긴장감"],
        momentum: 8.5,
        volume: 800,
        score: 8.2,
        volPeak: { timestamp: 4620000, volume: 0.72, momentum: -1.12 },
        mmtPeak: { timestamp: 4650000, volume: 0.31, momentum: 3.34 },
    },
];
