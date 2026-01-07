import { ATMOSPHERE } from "@/constants";

// 추후에 분위기에 따라 constants 정의한 값으로 사용해야함
export const getBadgeClasses = (attr: string) => {
    switch (attr) {
        case ATMOSPHERE.NEUTRAL: return "bg-gray-100 text-gray-700 border-gray-200";
        case ATMOSPHERE.HILARIOUS: return "bg-yellow-100 text-yellow-700 border-yellow-200";
        case ATMOSPHERE.SADNESS: return "bg-blue-100 text-blue-700 border-blue-200";
        case ATMOSPHERE.ANGER: return "bg-red-100 text-red-700 border-red-200";
        case ATMOSPHERE.BOOING: return "bg-gray-100 text-gray-700 border-gray-200";
        case ATMOSPHERE.ADMIRATION: return "bg-green-100 text-green-700 border-green-200";
        case ATMOSPHERE.ANTICIPATION: return "bg-purple-100 text-purple-700 border-purple-200";
        case ATMOSPHERE.ENCOURAGEMENT: return "bg-orange-100 text-orange-700 border-orange-200";
        default: return "bg-secondary text-secondary-foreground border-transparent";
    }
};

export const getBarColor = (attr: string) => {
    switch (attr) {
        case ATMOSPHERE.NEUTRAL: return "#9CA3AF"; // Gray
        case ATMOSPHERE.HILARIOUS: return "#FBBF24"; // Yellow
        case ATMOSPHERE.SADNESS: return "#3B82F6"; // Blue
        case ATMOSPHERE.ANGER: return "#EF4444"; // Red
        case ATMOSPHERE.BOOING: return "#6B7280"; // Gray
        case ATMOSPHERE.ADMIRATION: return "#10B981"; // Green
        case ATMOSPHERE.ANTICIPATION: return "#8B5CF6"; // Purple
        case ATMOSPHERE.ENCOURAGEMENT: return "#F97316"; // Orange
        default: return "#da8946ff"; // Default Gray
    }
}

export const getAtmosphereColor = (attr: string) => {
    switch (attr) {
        case ATMOSPHERE.NEUTRAL: return "text-gray-600";
        case ATMOSPHERE.HILARIOUS: return "text-yellow-600";
        case ATMOSPHERE.SADNESS: return "text-blue-600";
        case ATMOSPHERE.ANGER: return "text-red-600";
        case ATMOSPHERE.BOOING: return "text-gray-600";
        case ATMOSPHERE.ADMIRATION: return "text-green-600";
        case ATMOSPHERE.ANTICIPATION: return "text-purple-600";
        case ATMOSPHERE.ENCOURAGEMENT: return "text-orange-600";
        default: return "text-muted-foreground";
    }
}
