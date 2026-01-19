import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Tv, BarChart3, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { PLATFORM_CODE } from "@shared/constants/service_codes";


export function HomePage() {
    const navigate = useNavigate();

    const chzzkPlatform = {
        id: PLATFORM_CODE.CHZZK.toLowerCase(),
        label: "CHZZK",
        subLabel: "치지직",
        description: "네이버의 인터넷 방송 스트리밍 플랫폼",
        icon: Tv,
        colorClass: "group-hover:text-[#00FFA3]",
        borderClass: "group-hover:border-[#00FFA3]",
        bgClass: "group-hover:bg-[#00FFA3]/5",
    };

    return (
        // min-h 계산식 수정: 헤더/푸터 높이에 따라 유동적이지만, 중앙 정렬을 위해 flex 사용
        <div className="container mx-auto flex flex-col items-center justify-center min-h-[calc(100vh-14rem)] py-12 space-y-12">

            {/* 1. Hero Section (서비스 소개) */}
            <div className="text-center space-y-4 max-w-2xl animate-in fade-in zoom-in duration-500 slide-in-from-bottom-4">
                <div className="flex justify-center mb-6">
                    <div className="p-4 rounded-full bg-primary/10 ring-1 ring-primary/20 shadow-lg shadow-primary/5">
                        <BarChart3 className="w-12 h-12 text-primary" />
                    </div>
                </div>
                <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl">
                    CHATZZK
                </h1>
                <p className="text-lg text-muted-foreground leading-relaxed max-w-lg mx-auto">
                    지난 방송, 보고싶은 부분만 시청하세요.<br />
                    AI가 분석한 방송의 흐름과 핵심 요약을 제공합니다.
                </p>
            </div>

            {/* 2. Main Action (단일 플랫폼 카드) */}
            <div className="w-full max-w-md animate-in fade-in slide-in-from-bottom-8 duration-700 delay-150">
                <Card
                    className={cn(
                        "group cursor-pointer relative overflow-hidden transition-all duration-300 hover:shadow-xl border-2",
                        chzzkPlatform.borderClass,
                        chzzkPlatform.bgClass
                    )}
                    onClick={() => navigate(`/${chzzkPlatform.id}`)}
                >
                    <CardContent className="flex items-center p-6 gap-6">
                        {/* 아이콘 영역 */}
                        <div
                            className={cn(
                                "p-4 rounded-2xl bg-secondary shrink-0 transition-colors duration-300 group-hover:bg-background shadow-sm",
                                chzzkPlatform.colorClass
                            )}
                        >
                            <chzzkPlatform.icon className="w-8 h-8" />
                        </div>

                        {/* 텍스트 정보 영역 */}
                        <div className="flex-1 text-left space-y-1">
                            <h2 className="text-xl font-bold flex items-center gap-2 group-hover:text-foreground transition-colors">
                                {chzzkPlatform.label}
                            </h2>
                            <p className="text-sm font-medium text-foreground/80">
                                {chzzkPlatform.subLabel}
                            </p>
                            <p className="text-xs text-muted-foreground line-clamp-1">
                                {chzzkPlatform.description}
                            </p>
                        </div>

                        {/* 화살표 아이콘 (이동 암시) */}
                        <div className="text-muted-foreground/30 group-hover:text-foreground group-hover:translate-x-1 transition-all">
                            <ChevronRight className="w-6 h-6" />
                        </div>
                    </CardContent>

                    {/* 배경 데코레이션 (선택 사항) */}
                    <div className="absolute -right-12 -top-12 w-24 h-24 bg-primary/5 rounded-full blur-2xl group-hover:bg-[#00FFA3]/10 transition-colors" />
                </Card>
            </div>
        </div>
    );
}
