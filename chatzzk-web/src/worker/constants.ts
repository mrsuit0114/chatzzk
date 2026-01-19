
export const getAnalysisKey = (vodId: string) => {
    return `vods/${vodId}/analysis.json`;
}

export const getStreamLogKey = (vodId: string, logIndex: string) => {
    return `vods/${vodId}/stream_logs_${logIndex}.json`;
}
