import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { VodData } from "@shared/types/vod";
import { PLATFORM_COLORS, PLATFORM_LABELS } from "@/constants";
import { cn } from "@/lib/utils";
import { formatDateKo, formatTime } from "@/utils/time-formatter";
import { Skeleton } from "@/components/ui/skeleton";


interface Props {
    data: VodData;
}

export function VodCard({ data }: Props) {
    const navigate = useNavigate();

    // 1. 카드 전체 클릭 -> 분석 페이지로 이동
    const handleCardClick = () => {
        navigate(`/${data.platform.toLowerCase()}/analysis/${data.videoNo}`);
    };

    // 2. 채널명 클릭 -> 채널 상세 페이지로 이동
    const handleChannelClick = (e: React.MouseEvent) => {
        e.stopPropagation(); // 🚨 핵심: 부모(카드) 클릭 이벤트가 발생하지 않도록 막음
        navigate(`/${data.platform.toLowerCase()}/channel/${data.channelId}`);
    };

    const badgeColor = PLATFORM_COLORS[data.platform] || "bg-gray-600";

    return (
        <Card
            className="group cursor-pointer hover:shadow-md hover:border-primary/50 transition-all duration-200 overflow-hidden flex flex-col bg-card"
            onClick={handleCardClick}
        >
            {/* 상단 바: 플랫폼 뱃지 + 재생시간 */}
            <div className="flex items-center justify-between px-3 pt-3 pb-0">
                <Badge className={cn("text-white border-none shadow-sm text-[10px] px-1.5 py-0.5", badgeColor)}>
                    {PLATFORM_LABELS[data.platform]}
                </Badge>
                <span className="text-[11px] text-muted-foreground font-mono">
                    {formatTime(data.duration * 1000)}
                </span>
            </div>

            {/* 제목 */}
            <CardHeader className="p-3 pb-2 pt-2">
                <h3 className="font-semibold text-sm leading-snug line-clamp-3 min-h-[3.75rem] group-hover:text-primary transition-colors">
                    {data.title}
                </h3>
            </CardHeader>

            {/* 채널명 + 날짜 */}
            <CardContent className="px-3 pb-3 pt-0 mt-auto">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <button
                        onClick={handleChannelClick}
                        className="hover:text-foreground hover:underline transition-colors font-medium truncate max-w-[120px]"
                    >
                        {data.channelName}
                    </button>
                    <span className="shrink-0 opacity-70">
                        {formatDateKo(data.publishDate)}
                    </span>
                </div>
            </CardContent>
        </Card>
    );
}

export function VodCardSkeleton() {
    return (
        <div className="border rounded-xl bg-card overflow-hidden flex flex-col">
            <div className="flex items-center justify-between px-3 pt-3 pb-0">
                <Skeleton className="h-4 w-12" />
                <Skeleton className="h-3 w-10" />
            </div>
            <div className="p-3 pt-2 space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-4/5" />
                <Skeleton className="h-4 w-3/5" />
            </div>
            <div className="flex justify-between px-3 pb-3 pt-1">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-3 w-16" />
            </div>
        </div>
    );
}
