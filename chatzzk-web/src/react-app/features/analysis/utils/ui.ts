import { ATMOSPHERE, Atmosphere } from "@/constants";

// 추후에 분위기에 따라 constants 정의한 값으로 사용해야함
export const getBadgeClasses = (attr: Atmosphere) => {
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

export const getBarColor = (attr: Atmosphere) => {
    switch (attr) {
        case ATMOSPHERE.NEUTRAL: return "bg-gray-500/70 hover:bg-gray-600/80";
        case ATMOSPHERE.HILARIOUS: return "bg-yellow-500/70 hover:bg-yellow-600/80";
        case ATMOSPHERE.SADNESS: return "bg-blue-500/70 hover:bg-blue-600/80";
        case ATMOSPHERE.ANGER: return "bg-red-500/70 hover:bg-red-600/80";
        case ATMOSPHERE.BOOING: return "bg-gray-500/70 hover:bg-gray-600/80";
        case ATMOSPHERE.ADMIRATION: return "bg-green-500/70 hover:bg-green-600/80";
        case ATMOSPHERE.ANTICIPATION: return "bg-purple-500/70 hover:bg-purple-600/80";
        case ATMOSPHERE.ENCOURAGEMENT: return "bg-orange-500/70 hover:bg-orange-600/80";
        default: return "bg-secondary/70 hover:bg-secondary/80";
    }
}

export const getAtmosphereColor = (attr: Atmosphere) => {
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
