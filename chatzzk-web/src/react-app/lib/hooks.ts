import { useSearchParams } from "react-router-dom";

export function useUrlParams() {
    const [searchParams, setSearchParams] = useSearchParams();

    // 읽기 (Read)
    const query = searchParams.get("q") || "";
    const platform = searchParams.get("platform") || "all";

    // [추가] 정렬 및 날짜 필터
    const sort = searchParams.get("sort") || "latest"; // 'latest' | 'oldest'
    const fromDate = searchParams.get("from") || "";
    const toDate = searchParams.get("to") || "";
    const page = parseInt(searchParams.get("page") || "1", 10);

    // 쓰기 (Write) - 기존 파라미터 유지하면서 업데이트
    const setParams = (newParams: Record<string, any>) => {
        const currentParams = new URLSearchParams(searchParams);

        Object.entries(newParams).forEach(([key, value]) => {
            if (value === undefined || value === null || value === "") {
                currentParams.delete(key);
            } else {
                currentParams.set(key, String(value));
            }
        });

        if (!newParams.page) {
            currentParams.set("page", "1");
        }

        setSearchParams(currentParams, { replace: true });
    };

    return {
        query,
        platform,
        sort,
        fromDate,
        toDate,
        page,
        setParams, // 통합된 업데이트 함수
    };
}
