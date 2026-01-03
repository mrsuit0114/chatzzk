import { useState, useEffect } from "react";
import { Search, Calendar, RotateCcw } from "lucide-react"; // RotateCcw 아이콘 추가
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useUrlParams } from "@/lib/hooks";

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
        if (e.key === "Enter") {
            e.preventDefault();
            handleSearch();
        }
    };

    return (
        <div className="flex flex-col gap-4 p-4 border rounded-lg bg-card md:flex-row md:items-end shadow-sm">

            {/* 1. 검색어 입력 */}
            <div className="flex-1 space-y-2">
                <label className="text-sm font-medium text-muted-foreground">검색</label>
                <div className="relative">
                    <Input
                        placeholder={placeholder}
                        value={localQuery}
                        onChange={(e) => setLocalQuery(e.target.value)}
                        onKeyDown={handleKeyDown}
                        className="pl-9"
                    />
                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                </div>
            </div>

            {/* 2. 날짜 범위 선택 */}
            <div className="flex items-center gap-2">
                <div className="space-y-2">
                    <label className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                        <Calendar className="h-3.5 w-3.5" /> 시작일
                    </label>
                    <Input
                        type="date"
                        className="w-[140px]"
                        value={localFrom}
                        onChange={(e) => setLocalFrom(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />
                </div>
                <span className="pt-8 text-muted-foreground">~</span>
                <div className="space-y-2">
                    <label className="text-sm font-medium text-muted-foreground flex items-center gap-1">
                        <Calendar className="h-3.5 w-3.5" /> 종료일
                    </label>
                    <Input
                        type="date"
                        className="w-[140px]"
                        value={localTo}
                        onChange={(e) => setLocalTo(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />
                </div>
            </div>

            {/* 3. 액션 버튼 그룹 */}
            <div className="flex gap-2">
                {/* 조회 버튼 */}
                <Button onClick={handleSearch} className="min-w-[80px]">
                    조회
                </Button>

                {/* ✅ 초기화 버튼 */}
                <Button
                    variant="outline"
                    size="icon"
                    onClick={handleReset}
                    title="검색 조건 초기화"
                >
                    <RotateCcw className="h-4 w-4" />
                </Button>
            </div>
        </div>
    );
}
