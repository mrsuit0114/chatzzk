import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator"; // 구분선 추가
import { PLATFORM_COLORS, PLATFORM_LABELS } from "@/constants";
import { cn } from "@/lib/utils";
import { formatPlatformChannelUrl } from "@/utils/platform";
import { formatDateTimeKo } from "@/utils/time-formatter";
import { USER_ROLE } from "@shared/constants/service_codes";
import { MyChannelData } from "@shared/types/channel";
import { UserProfile } from "@shared/types/user";
import { ExternalLink, UserCog, ShieldCheck, Clock, ShieldAlert, LinkIcon, Activity } from "lucide-react";

interface Props {
    user: UserProfile;              // 로그인한 유저 정보 (Store)
    channel?: MyChannelData;    // 관리 중인 채널 정보 (API)
}

export function MyProfile({ user, channel }: Props) {
    const isEditor = user.role === USER_ROLE.EDITOR;

    // 채널 데이터 포맷팅
    const lastCrawledText = channel
        ? formatDateTimeKo(channel.lastVodCrawledAt) || "수집 기록 없음"
        : "-";

    const platformUrl = channel
        ? formatPlatformChannelUrl(channel.platform, channel.channelId)
        : "#";

    return (
        <Card className="flex flex-col lg:flex-row bg-card border shadow-sm overflow-hidden">
            {/* 1. 좌측: 사용자(관리자) 신원 영역 */}
            <div className="flex flex-col items-center justify-center p-8 bg-secondary/5 min-w-[240px] border-b lg:border-b-0 lg:border-r border-border gap-4">
                <Avatar className="h-24 w-24 border-4 border-background shadow-md">
                    <AvatarFallback className="text-3xl font-bold bg-primary/10 text-primary">
                        {user.userName.slice(0, 2).toUpperCase()}
                    </AvatarFallback>
                </Avatar>

                <div className="text-center space-y-2">
                    <div className="flex justify-center">
                        {isEditor ? (
                            <Badge variant="secondary" className="text-orange-600 bg-orange-50 border-orange-200 gap-1.5 px-3 py-1">
                                <UserCog className="h-3.5 w-3.5" /> 편집자
                            </Badge>
                        ) : (
                            <Badge variant="secondary" className="text-green-600 bg-green-50 border-green-200 gap-1.5 px-3 py-1">
                                <ShieldCheck className="h-3.5 w-3.5" /> 소유자
                            </Badge>
                        )}
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-foreground">{user.userName}</h2>
                    </div>
                </div>
            </div>

            {/* 2. 우측: 채널 상태 대시보드 */}
            <div className="flex-1 p-6 md:p-8 space-y-6">
                {channel ? (
                    <>
                        {/* 채널 헤더 */}
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="space-y-2">
                                <div className="flex items-center gap-2">
                                    <Badge variant="outline" className={cn(PLATFORM_COLORS[channel.platform], "text-white border-transparent")}>
                                        {PLATFORM_LABELS[channel.platform]}
                                    </Badge>

                                    {/* 수집 상태 배지 추가 */}
                                    {channel.isCollectionEnabled ? (
                                        <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50 gap-1">
                                            <Activity className="h-3 w-3" /> 수집 중
                                        </Badge>
                                    ) : (
                                        <Badge variant="outline" className="text-muted-foreground bg-muted gap-1">
                                            수집 일시 중지
                                        </Badge>
                                    )}
                                </div>
                                <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
                                    {channel.channelName}
                                </h1>
                            </div>

                            <Button variant="outline" size="sm" asChild className="gap-2 shrink-0">
                                <a href={platformUrl} target="_blank" rel="noopener noreferrer">
                                    채널 방문하기 <ExternalLink className="h-3.5 w-3.5" />
                                </a>
                            </Button>
                        </div>

                        <Separator />

                        {/* 데이터 정책/상태 그리드 (ChannelProfile과 동일 구성) */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                    </>
                ) : (
                    // 로딩 중이거나 데이터가 없을 때
                    <div className="h-full flex flex-col items-center justify-center text-muted-foreground gap-3 min-h-[200px]">
                        <div className="p-4 bg-secondary/20 rounded-full">
                            <LinkIcon className="h-8 w-8 opacity-30" />
                        </div>
                        <p>연결된 채널 정보를 불러오는 중입니다...</p>
                    </div>
                )}
            </div>
        </Card>
    );
}

// 내부용 정보 카드 (ChannelProfile과 동일)
function StatusCard({ icon, label, value, description }: { icon: React.ReactNode, label: string, value: string, description?: string }) {
    return (
        <div className="flex flex-col p-4 rounded-lg bg-secondary/20 border border-border/50 hover:bg-secondary/30 transition-colors space-y-1.5">
            <div className="flex items-center gap-2 text-xs text-muted-foreground font-medium uppercase tracking-wider">
                {icon}
                <span>{label}</span>
            </div>
            <div className="text-base font-bold text-foreground truncate">
                {value}
            </div>
            {description && (
                <div className="text-[11px] text-muted-foreground/80 truncate leading-tight" title={description}>
                    {description}
                </div>
            )}
        </div>
    );
}
