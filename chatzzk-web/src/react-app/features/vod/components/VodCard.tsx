import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { VodData } from "@shared/types/vod";
import { PLATFORM_COLORS, PLATFORM_LABELS } from "@/constants";
import { cn } from "@/lib/utils";
import { formatDateKo, formatTime } from "@/utils/time-formatter";
import { Play } from "lucide-react";


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
            className="cursor-pointer hover:shadow-lg transition-all group overflow-hidden border-border/60 flex flex-col"
            onClick={handleCardClick}
        >
            {/* 썸네일 영역 */}
            <div className="relative h-28 bg-muted">
                <div className="flex items-center justify-center w-full h-full bg-gradient-to-br from-muted/40 to-muted/10 text-muted-foreground">
                    <Play className="w-10 h-10 opacity-60" />
                </div>

                {/* 좌측 상단: 플랫폼 배지 */}
                <Badge className={cn("absolute top-2 left-2 text-white border-none", badgeColor)}>
                    {PLATFORM_LABELS[data.platform]}
                </Badge>

                {/* 우측 하단: 영상 길이 */}
                <Badge className="absolute bottom-2 right-2 bg-black/80 text-white border-none pointer-events-none">
                    {formatTime(data.duration * 1000)}
                </Badge>
            </div>

            <CardHeader className="p-4 pb-2 space-y-1">
                <div className="flex justify-between items-start">
                    <span className="text-xs text-muted-foreground">{formatDateKo(data.publishDate)}</span>
                </div>
                <CardTitle className="text-base leading-tight line-clamp-2">
                    {data.title}
                </CardTitle>
            </CardHeader>

            <CardContent className="p-4 pt-0 mt-auto">
                {/* 채널명 (클릭 시 전파 중단) */}
                <button
                    onClick={handleChannelClick}
                    className="text-sm text-muted-foreground hover:text-primary hover:underline transition-colors text-left"
                >
                    {data.channelName}
                </button>
            </CardContent>
        </Card>
    );
}
