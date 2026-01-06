
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { ChannelUI } from "../types";
import { PLATFORM_COLORS, PLATFORM_LABELS } from "@/constants";
import { cn } from "@/lib/utils";



interface Props {
    channel: ChannelUI;
}

export function ChannelProfile({ channel }: Props) {
    return (
        <Card className="flex flex-col md:flex-row items-center gap-6 p-8 bg-secondary/10 border-none shadow-sm">
            {/* 1. 프로필 이미지 (Avatar) */}
            <Avatar className="h-24 w-24 md:h-32 md:w-32 border-4 border-background shadow-md">
                <AvatarImage src={channel.profileUrl} alt={channel.name} />
                <AvatarFallback className="text-2xl">{channel.name.slice(0, 2)}</AvatarFallback>
            </Avatar>

            {/* 2. 텍스트 정보 */}
            <div className="flex flex-col items-center md:items-start text-center md:text-left space-y-2">
                <Badge variant="secondary" className={cn(PLATFORM_COLORS[channel.platform], "text-white font-normal")}>
                    {PLATFORM_LABELS[channel.platform]}
                </Badge>
                <div className="flex items-center gap-2">
                    <h1 className="text-3xl font-bold tracking-tight">{channel.name}</h1>
                </div>

                <p className="text-muted-foreground max-w-2xl leading-relaxed">
                    {channel.description || "채널 설명이 없습니다."}
                </p>

                {/* 통계 정보 (나중에 추가 가능) */}
                {/* <div className="flex gap-4 text-sm font-medium pt-2">
                    <span>구독자 250만명</span>
                    <span className="text-muted-foreground">•</span>
                    <span>동영상 1,200개</span>
                </div> */}
            </div>
        </Card>
    );
}
