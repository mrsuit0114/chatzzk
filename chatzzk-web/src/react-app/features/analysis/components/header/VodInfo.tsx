// src/features/vod/components/header/VodInfo.tsx

import { Link } from "react-router-dom";
import { ExternalLink, Calendar, Clock } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { VodHeaderData } from "../../types";
import { getBadgeClasses } from "@/utils/ui";
import { PLATFORM_LABELS } from "@/constants";
import { formatDateKo, formatTime } from "@/utils/time-formatter";


interface VodInfoProps {
    data: VodHeaderData;
}

export function VodInfo({ data }: VodInfoProps) {
    return (
        <div className="flex items-center gap-4 min-w-0 flex-1 ps-4">
            {/* 1. Platform Badge (Link to Platform Channel) */}
            <a
                href={data.platformChannelUrl}
                target="_blank"
                rel="noreferrer"
                className="flex-shrink-0"
            >
                <Badge variant="outline" className={getBadgeClasses(data.platform)}>
                    {PLATFORM_LABELS[data.platform.toUpperCase()]}
                </Badge>
            </a>

            <Separator orientation="vertical" className="h-6" />

            {/* 2. Title & Meta Info Wrapper */}
            <div className="flex flex-col min-w-0">
                {/* Title (Link to VOD) with Tooltip */}
                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <a
                                href={data.vodUrl}
                                target="_blank"
                                rel="noreferrer"
                                className="text-lg font-bold hover:underline decoration-primary underline-offset-4 truncate flex items-center gap-1"
                            >
                                {data.title}
                                <ExternalLink className="h-3 w-3 opacity-50 inline-block align-top" />
                            </a>
                        </TooltipTrigger>
                        <TooltipContent side="bottom" align="start">
                            <p className="max-w-md break-keep">{data.title}</p>
                        </TooltipContent>
                    </Tooltip>
                </TooltipProvider>

                {/* Meta Info Row */}
                <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                    {/* Channel Name (Internal Link) */}
                    <Link
                        to={`/${data.platform}/channel/${data.channelId}`}
                        className="font-medium hover:text-foreground transition-colors"
                    >
                        {data.channelName}
                    </Link>

                    <span>•</span>

                    {/* Date */}
                    <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span>{formatDateKo(data.publishDate)}</span>
                    </div>

                    <span>•</span>

                    {/* Duration */}
                    <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        <span>{formatTime(data.duration * 1000)}</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
