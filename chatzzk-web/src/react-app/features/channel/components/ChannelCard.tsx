import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { ChannelCardUI } from "../types";

interface Props {
    data: ChannelCardUI;
}

export function ChannelCard({ data }: Props) {
    const navigate = useNavigate();

    const handleClick = () => {
        navigate(`/channel/${data.id}`);
    };

    return (
        <Card
            className="flex items-center p-4 gap-4 cursor-pointer hover:bg-accent/50 transition-colors border-border/60"
            onClick={handleClick}
        >
            {/* 프로필 이미지 (Avatar) */}
            <Avatar className="h-14 w-14 border">
                <AvatarImage src={data.profileUrl} alt={data.name} />
                <AvatarFallback>{data.name.slice(0, 2)}</AvatarFallback>
            </Avatar>

            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-bold text-lg truncate">{data.name}</h3>
                    <Badge variant="outline" className="text-xs h-5 px-1.5">
                        {data.platform}
                    </Badge>
                </div>
                {data.description && (
                    <p className="text-sm text-muted-foreground line-clamp-1">
                        {data.description}
                    </p>
                )}
            </div>
        </Card>
    );
}
