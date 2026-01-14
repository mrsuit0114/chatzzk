import { useState, useEffect } from "react";
import { StreamLogData } from "../types";
import { mapRawStreamLogs } from "../utils";

export function useStreamLogs(chapterIndex: number) {
    const [logs, setLogs] = useState<StreamLogData[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        let isMounted = true;

        async function fetchLogs() {
            if (chapterIndex < 0) return;

            setIsLoading(true);
            try {
                // public 폴더 내의 파일 경로 가정
                const response = await fetch(`/data/stream_logs_${chapterIndex}.json`);
                if (!response.ok) {
                    throw new Error(`Failed to load logs for chapter ${chapterIndex}`);
                }
                const data = await response.json();
                const mappedLogs = mapRawStreamLogs(data);

                if (isMounted) {
                    setLogs(mappedLogs);
                    setError(null);
                }
            } catch (err) {
                if (isMounted) {
                    setError(err instanceof Error ? err : new Error("Unknown error"));
                    setLogs([]); // 에러 시 빈 배열
                }
            } finally {
                if (isMounted) setIsLoading(false);
            }
        }

        fetchLogs();

        return () => { isMounted = false; };
    }, [chapterIndex]);

    return { logs, isLoading, error };
}
