
export const getAnalysisKey = (vodId: string) => {
    return `vods/${vodId}/analytics.json`;
}

export const getStreamLogKey = (vodId: string, logIndex: string) => {
    return `vods/${vodId}/stream_logs_${logIndex}.json`;
}
