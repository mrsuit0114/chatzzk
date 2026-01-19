import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChannelData } from "../types";
import { Skeleton } from "@/components/ui/skeleton";
import { PLATFORM_LABELS, PLATFORM_COLORS } from "@/constants";
import { cn } from "@/lib/utils";
import { ChevronRight, User } from "lucide-react";

interface Props {
    data: ChannelData;
}

export function ChannelCard({ data }: Props) {
    const navigate = useNavigate();

    const handleClick = () => {
        navigate(`/${data.platform.toLowerCase()}/channel/${data.channelId}`);
    };

    // 플랫폼 관련 스타일/텍스트 매핑
    const platformLabel = PLATFORM_LABELS[data.platform] || data.platform;
    const badgeColor = PLATFORM_COLORS[data.platform] || "bg-gray-600";

    return (
        <Card
            className="group relative flex items-center p-4 gap-4 cursor-pointer hover:shadow-md hover:border-primary/50 transition-all border-border/60 bg-card"
            onClick={handleClick}
        >
            {/* 1. 프로필 이미지 대체 (그라디언트 아이콘) */}
            <div className="h-12 w-12 rounded-full shrink-0 flex items-center justify-center bg-gradient-to-br from-secondary to-secondary/50 border shadow-sm">
                <User className="h-6 w-6 text-muted-foreground/70" />
            </div>

            {/* 2. 텍스트 정보 (상하 배치로 변경하여 잘림 방지) */}
            <div className="flex-1 min-w-0 flex flex-col justify-center gap-1.5">

                {/* 상단: 채널명 */}
                <h3 className="font-bold text-base truncate leading-none group-hover:text-primary transition-colors">
                    {data.channelName}
                </h3>

                {/* 하단: 뱃지 + ID */}
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    {/* 뱃지: 크기 고정 (shrink-0) */}
                    <Badge className={cn("px-1.5 py-0 h-5 font-normal text-white border-none shrink-0", badgeColor)}>
                        {platformLabel}
                    </Badge>

                    {/* ID: 공간 부족 시 말줄임표 처리 */}
                    {data.channelId && (
                        <span className="truncate font-mono opacity-80" title={data.channelId}>
                            {data.channelId}
                        </span>
                    )}
                </div>
            </div>

            {/* 3. 이동 아이콘 */}
            <ChevronRight className="w-5 h-5 text-muted-foreground/30 group-hover:text-primary group-hover:translate-x-1 transition-all shrink-0" />
        </Card>
    );
}

// ✅ 스켈레톤 컴포넌트
export function ChannelCardSkeleton() {
    return (
        <Card className="flex items-center p-4 gap-4 border-border/60">
            {/* 아바타 스켈레톤 */}
            <Skeleton className="h-14 w-14 rounded-full shrink-0" />

            {/* 텍스트 스켈레톤 */}
            <div className="flex-1 space-y-2">
                <Skeleton className="h-5 w-1/2" />
                <div className="flex gap-2">
                    <Skeleton className="h-4 w-12" />
                    <Skeleton className="h-4 w-20" />
                </div>
            </div>
        </Card>
    );
}
