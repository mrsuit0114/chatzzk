import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { PLATFORM_LABELS } from "@/types";

export function GlobalSearchBar() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();

    const getInitialPlatform = () => {
        const urlParam = searchParams.get("platform");
        if (urlParam) return urlParam;

        const savedPlatform = localStorage.getItem("preferred-platform");
        return savedPlatform || "all";
    };

    const [keyword, setKeyword] = useState(searchParams.get("q") || "");
    const [platform, setPlatform] = useState(getInitialPlatform());
    const [isFocused, setIsFocused] = useState(false);

    useEffect(() => {
        const qParam = searchParams.get("q");
        setKeyword(qParam || "");

        const pParam = searchParams.get("platform");
        if (pParam) {
            setPlatform(pParam.toLowerCase());
        } else {
            setPlatform("all");
        }
    }, [searchParams]);

    const handlePlatformChange = (value: string) => {
        setPlatform(value);
        localStorage.setItem("preferred-platform", value);
    };

    const handleSearch = () => {
        if (!keyword.trim()) return;

        const params = new URLSearchParams();
        params.set("q", keyword);
        // "all"이 아닐 때만 파라미터 추가
        if (platform !== "all") {
            params.set("platform", platform);
        }

        navigate(`/search?${params.toString()}`);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter") handleSearch();
    };

    return (
        <div
            className={cn(
                "flex w-full max-w-xl items-center rounded-md border border-input bg-background overflow-hidden transition-colors",
                isFocused ? "ring-2 ring-ring ring-offset-2" : ""
            )}
        >
            <Select value={platform} onValueChange={handlePlatformChange}>
                <SelectTrigger
                    className="w-[110px] border-none shadow-none focus:ring-0 rounded-none bg-transparent h-10 gap-1 pl-3"
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setIsFocused(false)}
                >
                    {/* ✅ 2. 여기서 매핑 객체를 사용해 한글 이름 출력 */}
                    <SelectValue aria-label={platform}>
                        {PLATFORM_LABELS[platform] || "전체"}
                    </SelectValue>
                </SelectTrigger>
                <SelectContent>
                    {/* Value는 소문자 영어, 보여지는 텍스트는 한글 */}
                    <SelectItem value="all">전체</SelectItem>
                    <SelectItem value="chzzk">치지직</SelectItem>
                    <SelectItem value="youtube">유튜브</SelectItem>
                </SelectContent>
            </Select>

            <div className="h-5 w-[1px] bg-border mx-1" />

            <Input
                type="text"
                placeholder="채널명 또는 영상 제목 검색"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                className="flex-1 border-none shadow-none focus-visible:ring-0 h-10 rounded-none px-3"
            />

            <Button
                size="icon"
                variant="ghost"
                className="h-10 w-10 rounded-none hover:bg-transparent text-muted-foreground"
                onClick={handleSearch}
            >
                <Search className="h-4 w-4" />
            </Button>
        </div>
    );
}
