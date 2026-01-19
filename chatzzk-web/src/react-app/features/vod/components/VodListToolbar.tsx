import { useState, useEffect } from "react";
import { Search, Calendar, RotateCcw } from "lucide-react"; // RotateCcw 아이콘 추가
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useUrlParams } from "@/hooks/use-url-params";

interface Props {
    placeholder?: string;
}

export function VodListToolbar({ placeholder = "제목 또는 채널명 검색" }: Props) {
    const { query, fromDate, toDate, setParams } = useUrlParams();

    // 1. UI 표시용 임시 상태
    const [localQuery, setLocalQuery] = useState(query);
    const [localFrom, setLocalFrom] = useState(fromDate);
    const [localTo, setLocalTo] = useState(toDate);

    // URL이 외부에서 바뀌면 내부 상태 동기화
    useEffect(() => {
        setLocalQuery(query);
        setLocalFrom(fromDate);
        setLocalTo(toDate);
    }, [query, fromDate, toDate]);

    // 2. 검색 실행
    const handleSearch = () => {
        setParams({
            q: localQuery,
            from: localFrom,
            to: localTo,
            page: 1,
        });
    };

    // ✅ 3. 초기화 로직 (New)
    const handleReset = () => {
        // 내부 UI 상태 초기화
        setLocalQuery("");
        setLocalFrom("");
        setLocalTo("");

        // URL 파라미터 초기화 (빈 문자열을 보내면 훅 내부에서 delete 처리됨)
        setParams({
            q: "",
            from: "",
            to: "",
            page: 1,
        });
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.nativeEvent.isComposing) return;
        if (e.key === "Enter") {
            e.preventDefault();
            handleSearch();
        }
    };

    return (
        <div className="bg-card border rounded-lg p-4 shadow-sm space-y-4 lg:space-y-0 lg:flex lg:items-center lg:gap-4">

            {/* 1. 검색어 입력 (가변 너비) */}
            <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                    placeholder={placeholder}
                    value={localQuery}
                    onChange={(e) => setLocalQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="pl-9 bg-background"
                />
            </div>

            {/* 2. 구분선 (데스크탑 only) */}
            <div className="hidden lg:block w-px h-8 bg-border" />

            {/* 3. 날짜 및 버튼 그룹 */}
            <div className="flex flex-wrap items-center gap-2">
                <div className="flex items-center gap-2 bg-background border rounded-md px-3 py-2 text-sm">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <input
                        type="date"
                        className="bg-transparent outline-none w-[110px] text-foreground p-0 h-auto font-mono text-xs"
                        value={localFrom}
                        onChange={(e) => setLocalFrom(e.target.value)}
                    />
                    <span className="text-muted-foreground">~</span>
                    <input
                        type="date"
                        className="bg-transparent outline-none w-[110px] text-foreground p-0 h-auto font-mono text-xs"
                        value={localTo}
                        onChange={(e) => setLocalTo(e.target.value)}
                    />
                </div>

                <div className="flex items-center gap-2 ml-auto lg:ml-0">
                    <Button onClick={handleSearch} size="default">조회</Button>
                    <Button variant="outline" size="icon" onClick={handleReset} title="초기화">
                        <RotateCcw className="h-4 w-4" />
                    </Button>
                </div>
            </div>
        </div>
    );
}
