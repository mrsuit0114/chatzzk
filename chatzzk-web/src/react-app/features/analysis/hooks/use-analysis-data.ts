import { useState, useEffect, useMemo } from "react";
import { RawDashboardResponse } from "../types";
import { mapRawDataToViewData } from "../utils";


export function useAnalysisData() {
    const [rawData, setRawData] = useState<RawDashboardResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    // 1. 데이터 Fetching
    useEffect(() => {
        let isMounted = true;

        async function loadData() {
            try {
                setIsLoading(true);
                const response = await fetch("/data/analytics.json");

                if (!response.ok) {
                    throw new Error("Failed to load data");
                }

                const json = await response.json();

                if (isMounted) {
                    setRawData(json);
                    setError(null);
                }
            } catch (err) {
                if (isMounted) {
                    console.error(err);
                    setError(err instanceof Error ? err : new Error("Unknown error"));
                }
            } finally {
                if (isMounted) {
                    setIsLoading(false);
                }
            }
        }

        loadData();

        return () => { isMounted = false; };
    }, []);

    // 2. 데이터 매핑 (rawData -> viewData)
    const viewData = useMemo(() => {
        if (!rawData) return null;
        return mapRawDataToViewData(rawData);
    }, [rawData]);

    return {
        viewData,
        isLoading,
        error
    };
}
