import { formatTime } from "@/features/analysis/utils";

export const DetailChartTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
        const data = payload[0].payload;
        return (
            <div className="bg-white/65 border border-slate-200 p-2.5 rounded-lg shadow-md text-xs z-50">
                <p className="font-bold mb-1.5 text-slate-800">
                    {formatTime(data.startTime)}
                </p>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-slate-600">
                    <span>Volume:</span>
                    <span className="font-mono font-medium text-slate-900 text-right">
                        {data.volume.toFixed(2)}
                    </span>
                    <span>Momentum:</span>
                    <span className="font-mono font-medium text-slate-900 text-right">
                        {data.scaledMomentum.toFixed(2)}
                        <span className="ml-1 text-slate-800 font-normal">
                            ({data.originalMomentum.toFixed(2)})
                        </span>
                    </span>
                </div>
            </div>
        );
    }
    return null;
};
