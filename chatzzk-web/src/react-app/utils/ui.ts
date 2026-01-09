import { PLATFORM_CODE, PlatformCode } from "@/constants";

export function getBadgeClasses(platform: PlatformCode) {
    switch (platform) {
        case PLATFORM_CODE.CHZZK:
            return "uppercase px-2 py-1 text-xs font-bold hover:bg-secondary transition-colors cursor-pointer text-green-600 border-green-200";
        default:
            return "uppercase px-2 py-1 text-xs font-bold hover:bg-secondary transition-colors cursor-pointer text-red-600 border-red-200";
    }
}
