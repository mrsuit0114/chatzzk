import { PlatformCode, PLATFORM_CODE } from "@shared/constants/service_codes";

export function getBadgeClasses(platform: PlatformCode) {
    switch (platform.toUpperCase() as PlatformCode) {
        case PLATFORM_CODE.CHZZK:
            return "uppercase px-2 py-1 text-xs font-bold hover:bg-secondary transition-colors cursor-pointer text-green-600 border-green-200";
        default:
            return "uppercase px-2 py-1 text-xs font-bold hover:bg-secondary transition-colors cursor-pointer text-red-600 border-red-200";
    }
}
