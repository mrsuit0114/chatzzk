
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { AuthUser, PLATFORM_COLORS, PLATFORM_LABELS, USER_ROLE } from "@/types";
import { ExternalLink, UserCog, ShieldCheck } from "lucide-react";

interface Props {
    user: AuthUser;
}

export function MyProfile({ user }: Props) {
    const isEditor = user.role === USER_ROLE.EDITOR;

    return (
        <div className="flex flex-col md:flex-row items-center gap-6 px-4 py-2">
            {/* 1. 프로필 이미지 */}
            <Avatar className="h-24 w-24 border-2 border-border shadow-sm">
                <AvatarImage src="" /> {/* 실제라면 user.profileImage */}
                <AvatarFallback className="text-2xl font-bold bg-muted">
                    {user.id.slice(0, 2)}
                </AvatarFallback>
            </Avatar>

            {/* 2. 정보 영역 */}
            <div className="text-center md:text-left space-y-2">
                {/* 역할 배지 */}
                {isEditor ? (
                    <Badge variant="secondary" className="text-orange-600 bg-orange-50 border-orange-200 gap-1">
                        <UserCog className="h-3 w-3" /> 편집자
                    </Badge>
                ) : (
                    <Badge variant="secondary" className="text-green-600 bg-green-50 border-green-200 gap-1">
                        <ShieldCheck className="h-3 w-3" /> 채널 소유자
                    </Badge>
                )}
                <div className="flex flex-col md:flex-row items-center gap-2">
                    <h1 className="text-2xl font-bold">{user.id}</h1>

                </div>

                {/* ID 및 담당 채널 정보 */}
                <div className="text-muted-foreground space-y-1">
                    {/* 플랫폼 배지 */}
                    <Badge variant="outline" className={cn(PLATFORM_COLORS[user.platform], "text-xs py-0 h-5")}>
                        {PLATFORM_LABELS[user.platform]}
                    </Badge>

                    <div className="flex items-center gap-2 justify-center md:justify-start text-sm">
                        <span>
                            {isEditor ? "담당 채널:" : "운영 채널:"}
                        </span>

                        {/* 채널 링크 (클릭 시 새 탭 이동) */}
                        <a
                            href={user.platformChannelUrl || "#"}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-medium text-foreground hover:underline flex items-center gap-1 group"
                        >
                            {user.channelName}
                            <ExternalLink className="h-3 w-3 opacity-50 group-hover:opacity-100 transition-opacity" />
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
}
