
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PLATFORM_COLORS, PLATFORM_LABELS } from "@/constants";
import { cn } from "@/lib/utils";
import { formatPlatformChannelUrl } from "@/utils/platform";
import { formatDateTimeKo } from "@/utils/time-formatter";
import { DELAY_OPTIONS } from "@shared/constants/service_codes";
import { ChannelDetailData } from "@shared/types/channel";
import { ExternalLink, Clock, ShieldAlert, CheckCircle2, User, XCircle } from "lucide-react";



interface Props {
    channel: ChannelDetailData;
}

export function ChannelProfile({ channel }: Props) {
    // 날짜 포맷팅 (YYYY-MM-DD HH:mm)
    const lastCrawledText = formatDateTimeKo(channel.lastVodCrawledAt) || "수집된 기록 없음";
    const PlatformChannelUrl = formatPlatformChannelUrl(channel.platform, channel.channelId);

    const getDelayLabel = (value: number) =>
        DELAY_OPTIONS.find(opt => opt.value === String(value))?.label || "즉시 공개";

    return (
        <Card className="flex flex-col md:flex-row items-start gap-6 p-6 bg-gradient-to-br from-card to-secondary/10 border shadow-sm">
            {/* 1. 프로필 이미지 (Fallback: User Icon) */}
            <div className="flex-shrink-0">
                <Avatar className="h-20 w-20 md:h-24 md:w-24 border-4 border-background shadow-md bg-muted">
                    <AvatarFallback className="bg-secondary/50 text-secondary-foreground">
                        {/* 텍스트 대신 아이콘 사용으로 깔끔하게 */}
                        <User className="h-10 w-10 opacity-50" />
                    </AvatarFallback>
                </Avatar>
            </div>

            {/* 2. 정보 영역 */}
            <div className="flex-1 w-full space-y-5">
                {/* 헤더 */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <div className="space-y-2">
                        <div className="flex items-center gap-2 flex-wrap">
                            <Badge className={cn("text-white border-none", PLATFORM_COLORS[channel.platform])}>
                                {PLATFORM_LABELS[channel.platform]}
                            </Badge>

                            {/* 수집 상태 뱃지 개선 */}
                            {channel.isCollectionEnabled ? (
                                <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 gap-1 pr-2">
                                    <CheckCircle2 className="h-3 w-3" /> 수집 중
                                </Badge>
                            ) : (
                                <Badge variant="outline" className="border-red-200 bg-red-50 text-red-700 gap-1 pr-2">
                                    <XCircle className="h-3 w-3" /> 수집 중지
                                </Badge>
                            )}
                        </div>
                        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
                            {channel.channelName}
                        </h1>
                    </div>

                    <Button variant="outline" size="sm" asChild className="gap-2 shrink-0">
                        <a href={PlatformChannelUrl} target="_blank" rel="noopener noreferrer">
                            채널 바로가기 <ExternalLink className="h-3 w-3" />
                        </a>
                    </Button>
                </div>

                {/* 통계 카드 그리드 */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <StatusCard
                        icon={<Clock className="h-4 w-4 text-blue-500" />}
                        label="최근 수집"
                        value={lastCrawledText}
                        subtext="게시된 지 30분이 지난 VOD 만 수집됩니다"
                    />
                    <StatusCard
                        icon={<ShieldAlert className="h-4 w-4 text-amber-500" />}
                        label="방송 요약 공개 여부"
                        value={getDelayLabel(channel.vodExposureDelayHours)}
                        subtext="플랫폼 vod 게시 시간 기준"
                    />
                    <StatusCard
                        icon={<ShieldAlert className="h-4 w-4 text-rose-500" />}
                        label="상세 분석 공개 여부"
                        value={getDelayLabel(channel.vodDetailExposureDelayHours)}
                        subtext="플랫폼 vod 게시 시간 기준"
                    />
                </div>
            </div>
        </Card>
    );
}

// 작은 정보 카드
export function StatusCard({ icon, label, value, subtext }: { icon: React.ReactNode, label: string, value: string, subtext?: string }) {
    return (
        <div className="flex flex-col p-3 rounded-lg bg-background/60 border shadow-sm space-y-1 hover:bg-background transition-colors">
            <div className="flex items-center gap-2 text-xs text-muted-foreground font-medium">
                {icon}
                <span>{label}</span>
            </div>
            <div className="text-sm font-semibold text-foreground truncate" title={value}>
                {value}
            </div>
            {subtext && (
                <div className="text-[10px] text-muted-foreground/70 truncate">
                    {subtext}
                </div>
            )}
        </div>
    );
}

// ✅ 스켈레톤 컴포넌트
export function ChannelProfileSkeleton() {
    return (
        <Card className="flex flex-col md:flex-row items-start gap-6 p-6 border">
            <Skeleton className="h-20 w-20 md:h-24 md:w-24 rounded-full shrink-0" />
            <div className="flex-1 w-full space-y-5">
                <div className="space-y-2">
                    <div className="flex gap-2">
                        <Skeleton className="h-5 w-16" />
                        <Skeleton className="h-5 w-20" />
                    </div>
                    <Skeleton className="h-8 w-1/2" />
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <Skeleton className="h-16 rounded-lg" />
                    <Skeleton className="h-16 rounded-lg" />
                    <Skeleton className="h-16 rounded-lg" />
                </div>
            </div>
        </Card>
    );
}
