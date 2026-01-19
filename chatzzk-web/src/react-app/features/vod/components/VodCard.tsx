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
            className="group cursor-pointer hover:shadow-md hover:border-primary/50 transition-all duration-200 overflow-hidden flex flex-col h-full bg-card"
            onClick={handleCardClick}
        >
            <div className="relative h-20 bg-gradient-to-r from-emerald-500/10 to-emerald-500/5 border-b">

                <Badge className={cn("absolute top-2 left-2 text-white border-none shadow-sm", badgeColor)}>
                    {PLATFORM_LABELS[data.platform]}
                </Badge>

                <Badge className="absolute bottom-2 right-2 bg-black/80 text-white border-none pointer-events-none hover:bg-black/80">
                    {formatTime(data.duration * 1000)}
                </Badge>
            </div>

            {/* 2. 콘텐츠 영역 */}
            <CardHeader className="p-4 pb-2 space-y-2">
                <h3 className="font-semibold leading-snug line-clamp-2 min-h-[2.5rem] group-hover:text-primary transition-colors">
                    {data.title}
                </h3>
            </CardHeader>

            <CardContent className="p-4 pt-0 mt-auto">
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
        <div className="border rounded-xl bg-card overflow-hidden h-[160px] flex flex-col">
            <div className="h-14 bg-muted/40 animate-pulse" />
            <div className="p-4 space-y-3">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-5 w-1/2" />
                <div className="flex justify-between pt-2">
                    <Skeleton className="h-4 w-20" />
                    <Skeleton className="h-4 w-16" />
                </div>
            </div>
        </div>
    );
}
