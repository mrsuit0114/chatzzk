
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PLATFORM_COLORS, PLATFORM_LABELS } from "@/constants";
import { cn } from "@/lib/utils";
import { formatPlatformChannelUrl } from "@/utils/platform";
import { formatDateTimeKo } from "@/utils/time-formatter";
import { ChannelDetailData } from "@shared/types/channel";
import { ExternalLink, Clock, ShieldAlert } from "lucide-react";



interface Props {
    channel: ChannelDetailData;
}

export function ChannelProfile({ channel }: Props) {
    // 날짜 포맷팅 (YYYY-MM-DD HH:mm)
    const lastCrawledText = formatDateTimeKo(channel.lastVodCrawledAt) || "수집된 기록 없음";

    const PlatformChannelUrl = formatPlatformChannelUrl(channel.platform, channel.channelId);

    return (
        <Card className="flex flex-col md:flex-row items-start gap-6 p-6 bg-card border shadow-sm">
            {/* 1. 프로필 이미지 (이미지 URL이 없으므로 Fallback 사용) */}
            <div className="flex-shrink-0">
                <Avatar className="h-20 w-20 md:h-24 md:w-24 border-2 border-border shadow-sm">
                    {/* 추후 썸네일 필드가 다시 추가되면 AvatarImage 사용 */}
                    <AvatarFallback className="text-xl font-bold bg-secondary text-secondary-foreground">
                        {channel.channelName.slice(0, 2)}
                    </AvatarFallback>
                </Avatar>
            </div>

            {/* 2. 메인 정보 및 통계 */}
            <div className="flex-1 w-full space-y-4">
                {/* 헤더: 뱃지, 이름, 외부 링크 */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                    <div className="space-y-1">
                        <div className="flex items-center gap-2">
                            <Badge variant="secondary" className={cn(PLATFORM_COLORS[channel.platform], "text-white hover:bg-opacity-90 transition-colors")}>
                                {PLATFORM_LABELS[channel.platform]}
                            </Badge>
                            {/* 수집 활성화 여부 표시 */}
                            {channel.isCollectionEnabled ? (
                                <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50">
                                    수집 중
                                </Badge>
                            ) : (
                                <Badge variant="outline" className="text-muted-foreground bg-muted">
                                    수집 중지
                                </Badge>
                            )}
                        </div>
                        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">{channel.channelName}</h1>
                    </div>

                    <Button variant="outline" size="sm" asChild className="gap-2">
                        <a href={PlatformChannelUrl} target="_blank" rel="noopener noreferrer">
                            채널 바로가기 <ExternalLink className="h-3 w-3" />
                        </a>
                    </Button>
                </div>

                {/* 데이터 정책 정보 그리드 (스키마 반영) */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                    <StatusCard
                        icon={<Clock className="h-4 w-4 text-blue-500" />}
                        label="최근 수집 시각"
                        value={lastCrawledText}
                        description="게시된 지 30분이 지난 VOD만 수집됩니다."
                    />
                    <StatusCard
                        icon={<ShieldAlert className="h-4 w-4 text-amber-500" />}
                        label="VOD 노출 지연"
                        value={`${channel.vodExposureDelayHours}시간 후 공개`}
                        description="VOD 게시 후 공개까지의 지연 시간입니다."
                    />
                    <StatusCard
                        icon={<ShieldAlert className="h-4 w-4 text-rose-500" />}
                        label="상세 분석 지연"
                        value={`${channel.vodDetailExposureDelayHours}시간 후 공개`}
                        description="VOD 게시 후 상세 분석 정보 공개까지의 지연 시간입니다."
                    />
                </div>
            </div>
        </Card>
    );
}

// 내부용 작은 정보 카드 컴포넌트
function StatusCard({ icon, label, value, description }: { icon: React.ReactNode, label: string, value: string, description?: string }) {
    return (
        <div className="flex flex-col p-3 rounded-lg bg-secondary/30 border border-border/50 space-y-1">
            <div className="flex items-center gap-2 text-xs text-muted-foreground font-medium">
                {icon}
                <span>{label}</span>
            </div>
            <div className="text-sm font-semibold text-foreground">
                {value}
            </div>
            {description && (
                <div className="text-[10px] text-muted-foreground/80 truncate" title={description}>
                    {description}
                </div>
            )}
        </div>
    );
}
