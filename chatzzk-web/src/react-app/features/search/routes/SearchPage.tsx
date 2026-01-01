import { useSearchParams } from "react-router-dom";
import { Separator } from "@/components/ui/separator";

// 도메인 컴포넌트 & 데이터 import
import { VodCard } from "@/features/vod/components/VodCard";
import { MOCK_VOD_DATA } from "@/features/vod/api/mock";
import { ChannelCard } from "@/features/channel/components/ChannelCard";
import { MOCK_CHANNEL_DATA } from "@/features/channel/api/mock";

export function SearchPage() {
    const [searchParams] = useSearchParams();

    // 1. URL 파라미터 읽기
    const query = searchParams.get("q") || "";
    const platform = searchParams.get("platform") || "all";

    // 2. 필터링 로직 (나중엔 백엔드 API가 수행)

    // [채널 검색] 이름에 검색어 포함
    const channelResults = MOCK_CHANNEL_DATA.filter((channel) => {
        const matchPlatform = platform === "all" || channel.platform === platform;
        const matchQuery = channel.name.includes(query);
        return matchPlatform && matchQuery;
    });

    // [VOD 검색] 제목 OR 채널명에 검색어 포함
    const vodResults = MOCK_VOD_DATA.filter((vod) => {
        const matchPlatform = platform === "all" || vod.platform === platform;
        const matchQuery = vod.title.includes(query) || vod.channelName.includes(query);
        return matchPlatform && matchQuery;
    });

    // 검색어가 없을 때 처리
    if (!query) {
        return (
            <div className="container mx-auto py-20 text-center text-muted-foreground">
                검색어를 입력해주세요.
            </div>
        );
    }

    return (
        <div className="container mx-auto py-8 space-y-10">
            {/* 페이지 타이틀 */}
            <div>
                <h1 className="text-2xl font-bold">
                    "{query}" 검색 결과
                </h1>
                <p className="text-muted-foreground text-sm mt-1">
                    플랫폼: {platform === "all" ? "전체" : platform}
                </p>
            </div>

            {/* Section 1: 채널 검색 결과 */}
            <section className="space-y-4">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                    채널 <span className="text-sm font-normal text-muted-foreground">({channelResults.length})</span>
                </h2>
                {channelResults.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {channelResults.map((channel) => (
                            <ChannelCard key={channel.id} data={channel} />
                        ))}
                    </div>
                ) : (
                    <div className="py-8 text-center bg-secondary/10 rounded-lg text-muted-foreground text-sm">
                        검색된 채널이 없습니다.
                    </div>
                )}
            </section>

            <Separator />

            {/* Section 2: VOD 검색 결과 */}
            <section className="space-y-4">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                    동영상 <span className="text-sm font-normal text-muted-foreground">({vodResults.length})</span>
                </h2>
                {vodResults.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {vodResults.map((vod) => (
                            <VodCard key={vod.vodId} data={vod} />
                        ))}
                    </div>
                ) : (
                    <div className="py-12 text-center bg-secondary/10 rounded-lg text-muted-foreground text-sm">
                        검색된 동영상이 없습니다.
                    </div>
                )}
            </section>
        </div>
    );
}
