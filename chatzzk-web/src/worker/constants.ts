
export const getAnalysisKey = (vodId: string) => {
    return `vods-0203/${vodId}/analysis.json`;
}

export const getStreamLogKey = (vodId: string, logIndex: string) => {
    return `vods-0203/${vodId}/stream_logs_${logIndex}.json`;
}
