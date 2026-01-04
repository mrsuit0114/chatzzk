export const VIEW_TYPE = {
    HIGHLIGHT: "highlight",
    INSIGHT: "insight",
} as const;

export type ViewType = typeof VIEW_TYPE[keyof typeof VIEW_TYPE];

export interface Sentiment {
    label: string;
    score: number; // Float (0.0 ~ 100.0)
    color: string; // Tailwind class (e.g. "text-green-500")
}

export interface VodHeaderData {
    title: string;
    vodUrl: string;
    platform: "chzzk" | "youtube";
    platformChannelUrl: string;
    channelName: string;
    channelId: string;
    publishDate: string | Date;
    duration: string;
    avgScore: number;
    sentiments: Sentiment[];
}

export interface VodAnalysisHeaderProps {
    data: VodHeaderData;
    currentView: ViewType;
    onViewChange: (view: ViewType) => void;
    isInsightLocked?: boolean;
}
