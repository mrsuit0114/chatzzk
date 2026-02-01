
export const getAnalysisKey = (vodId: string) => {
    return `vods-0202/${vodId}/analysis.json`;
}

export const getStreamLogKey = (vodId: string, logIndex: string) => {
    return `vods-0202/${vodId}/stream_logs_${logIndex}.json`;
}
