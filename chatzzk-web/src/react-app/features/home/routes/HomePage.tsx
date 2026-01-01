import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Tv, Youtube, MonitorPlay, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";

export function HomePage() {
    const navigate = useNavigate();

    // 플랫폼 바로가기 설정 (ID는 반드시 소문자)
    const platforms = [
        {
            id: "chzzk",
            label: "치지직",
            description: "네이버의 게임 스트리밍 플랫폼",
            icon: Tv,
            colorClass: "group-hover:text-green-500",
            borderClass: "group-hover:border-green-500",
            bgClass: "group-hover:bg-green-50/50",
        },
        {
            id: "youtube",
            label: "유튜브",
            description: "글로벌 비디오 플랫폼",
            icon: Youtube,
            colorClass: "group-hover:text-red-600",
            borderClass: "group-hover:border-red-600",
            bgClass: "group-hover:bg-red-50/50",
        },
        {
            id: "afreeca",
            label: "SOOP",
            description: "대한민국 대표 라이브 스트리밍",
            icon: MonitorPlay,
            colorClass: "group-hover:text-blue-600",
            borderClass: "group-hover:border-blue-600",
            bgClass: "group-hover:bg-blue-50/50",
        },
    ];

    return (
        <div className="container mx-auto flex flex-col items-center justify-center min-h-[calc(100vh-8rem)] py-12 space-y-16">

            {/* 1. Hero Section (서비스 소개) */}
            <div className="text-center space-y-6 max-w-2xl animate-in fade-in zoom-in duration-500">
                <div className="flex justify-center mb-4">
                    <div className="p-3 rounded-full bg-primary/10">
                        <BarChart3 className="w-10 h-10 text-primary" />
                    </div>
                </div>
                <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl">
                    Stream Analytics
                </h1>
                <p className="text-xl text-muted-foreground leading-relaxed">
                    인터넷 방송의 흐름을 데이터로 읽다.<br />
                    채팅 분위기, 화력, 하이라이트를 AI로 분석하여 제공합니다.
                </p>
            </div>

            {/* 2. Platform Navigation (바로가기 버튼) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl">
                {platforms.map((platform) => (
                    <Card
                        key={platform.id}
                        className={cn(
                            "group cursor-pointer transition-all duration-300 hover:shadow-lg border-2",
                            platform.borderClass,
                            platform.bgClass
                        )}
                        onClick={() => navigate(`/platform/${platform.id}`)} // 소문자 ID로 이동
                    >
                        <CardContent className="flex flex-col items-center justify-center p-8 text-center space-y-4">
                            {/* 아이콘 */}
                            <div
                                className={cn(
                                    "p-4 rounded-full bg-secondary transition-colors duration-300 group-hover:bg-background",
                                    platform.colorClass
                                )}
                            >
                                <platform.icon className="w-8 h-8" />
                            </div>

                            {/* 텍스트 정보 */}
                            <div className="space-y-2">
                                <h2 className="text-2xl font-bold group-hover:text-foreground transition-colors">
                                    {platform.label}
                                </h2>
                                <p className="text-sm text-muted-foreground group-hover:text-muted-foreground/80">
                                    {platform.description}
                                </p>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* 3. Footer / Additional Info (Optional) */}
            <div className="text-sm text-muted-foreground">
                분석을 원하는 플랫폼을 선택하여 시작하세요.
            </div>
        </div>
    );
}
