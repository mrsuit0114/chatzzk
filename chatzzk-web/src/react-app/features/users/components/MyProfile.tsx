import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PLATFORM_COLORS, PLATFORM_LABELS } from "@/constants";
import { StatusCard } from "@/features/channel/components/ChannelProfile";
import { cn } from "@/lib/utils";
import { formatPlatformChannelUrl } from "@/utils/platform";
import { formatDateTimeKo } from "@/utils/time-formatter";
import { DELAY_OPTIONS, USER_ROLE } from "@shared/constants/service_codes";
import { MyChannelData } from "@shared/types/channel";
import { UserProfile } from "@shared/types/user";
import { ExternalLink, UserCog, ShieldCheck, Clock, ShieldAlert, AlertCircle, CheckCircle2, XCircle } from "lucide-react";

interface Props {
    user: UserProfile;              // 로그인한 유저 정보 (Store)
    channel: MyChannelData;    // 관리 중인 채널 정보 (API)
}

export function MyProfile({ user, channel }: Props) {
    return (
        <Card className="flex flex-col lg:flex-row bg-card border shadow-sm overflow-hidden">

            {/* 1. 좌측: 사용자 정보 (배경색으로 구분) */}
            <UserCard user={user} />

            {/* 2. 우측: 채널 대시보드 */}
            <div className="flex-1 p-6 md:p-8 space-y-6">
                {channel ? (
                    <MyProfileChannelInfo channel={channel} />
                ) : (
                    // 데이터 없음 (로딩 후)
                    <div className="h-full flex flex-col items-center justify-center text-muted-foreground gap-3 py-12">
                        <AlertCircle className="h-8 w-8 opacity-20" />
                        <p>연결된 채널 정보가 없습니다.</p>
                    </div>
                )}
            </div>
        </Card>
    );
}

function UserCard({ user }: { user: UserProfile }) {
    const isEditor = user.role === USER_ROLE.EDITOR;

    return (<div className="flex flex-col items-center justify-center p-8 bg-muted/30 min-w-[200px] border-b lg:border-b-0 lg:border-r gap-5">
        <Avatar className="h-24 w-24 border-4 border-background shadow-sm">
            <AvatarFallback className="text-2xl font-bold bg-primary/10 text-primary">
                {user.userName.slice(0, 2).toUpperCase()}
            </AvatarFallback>
        </Avatar>

        <div className="text-center space-y-2">
            <div className="flex justify-center">
                {isEditor ? (
                    <Badge variant="secondary" className="text-orange-600 bg-orange-50 border-orange-200 gap-1.5 px-2.5 py-0.5 shadow-none">
                        <UserCog className="h-3.5 w-3.5" /> 편집자
                    </Badge>
                ) : (
                    <Badge variant="secondary" className="text-green-600 bg-green-50 border-green-200 gap-1.5 px-2.5 py-0.5 shadow-none">
                        <ShieldCheck className="h-3.5 w-3.5" /> 채널 소유자
                    </Badge>
                )}
            </div>
            <h2 className="text-xl font-bold text-foreground">{user.userName}</h2>
        </div>
    </div>
    );
}

function MyProfileChannelInfo({ channel }: { channel: MyChannelData }) {
    const lastCrawledText = formatDateTimeKo(channel.lastVodCrawledAt) || "수집된 기록 없음";
    const getDelayLabel = (val: number) => DELAY_OPTIONS.find(o => o.value === String(val))?.label || "즉시 공개";
    const PlatformChannelUrl = formatPlatformChannelUrl(channel.platform, channel.channelId);

    return (<>
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


        {/* 상태 카드 그리드 */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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
    </>
    );
}
