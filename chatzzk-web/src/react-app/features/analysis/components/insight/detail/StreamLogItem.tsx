import React from "react";
import { StreamLogData, StreamLogType } from "../../../types";
import { cn } from "@/lib/utils";
import { User, Mic, DollarSign, Crown } from "lucide-react";
import { formatTime } from "@/utils/time-formatter";

interface StreamLogItemProps {
    log: StreamLogData;
    style: React.CSSProperties; // 위치(transform) 정보
    measureRef: (node: Element | null) => void; // ✅ [추가] 높이 측정용 Ref
    index: number; // ✅ [추가] 리스트 내 인덱스 (측정 식별용)
}

export function StreamLogItem({ log, style, measureRef, index }: StreamLogItemProps) {
    const isASR = log.type === StreamLogType.ASR;
    const isDonation = log.type === StreamLogType.DONATION;
    const isSpecialUser = !!log.user; // 특수 권한 유저 (닉네임 존재)

    return (
        <div
            ref={measureRef} // ✅ [핵심] 실제 DOM 요소 측정 연결
            data-index={index} // ✅ [핵심] Virtualizer가 식별하기 위한 인덱스
            style={style}
            className={cn(
                "flex w-full px-4 py-1.5 absolute top-0 left-0", // absolute 위치 지정은 style과 함께 동작
                isASR ? "justify-start" : "justify-end"
            )}
        >
            <div className={cn(
                "max-w-[85%] rounded-lg p-3 text-sm relative group transition-all shadow-sm",
                // 1. ASR (좌측)
                isASR && "bg-white border border-slate-200 text-slate-700 rounded-tl-none",

                // 2. Donation (우측)
                isDonation && "bg-yellow-50 border border-yellow-200 text-yellow-900 rounded-tr-none",

                // 3. Chat (우측) - 일반 vs 특수 유저 구분
                !isASR && !isDonation && (
                    isSpecialUser
                        ? "bg-indigo-50 border-2 border-indigo-200 text-indigo-900 rounded-tr-none ring-1 ring-indigo-100" // ✅ 특수 유저 강조
                        : "bg-blue-50 border border-blue-100 text-blue-900 rounded-tr-none"
                )
            )}>
                {/* Header: Timestamp & User Info */}
                <div className="flex items-center gap-2 mb-1.5 opacity-80 text-xs">
                    <span className="font-mono text-[10px] text-muted-foreground">{formatTime(log.timestamp)}</span>

                    {/* ASR 아이콘 */}
                    {isASR && <Mic className="h-3 w-3" />}

                    {/* 유저 정보 (Chat & Donation) */}
                    {!isASR && log.user && (
                        <div className={cn(
                            "flex items-center gap-1 font-bold",
                            isSpecialUser ? "text-indigo-700" : "text-foreground/80"
                        )}>
                            {/* 특수 유저는 왕관 아이콘, 일반은 유저 아이콘 */}
                            {isSpecialUser ? <Crown className="h-3 w-3 fill-indigo-200" /> : <User className="h-3 w-3" />}
                            <span>{log.user}</span>
                        </div>
                    )}

                    {/* 후원 뱃지 */}
                    {isDonation && (
                        <span className="flex items-center text-yellow-700 font-bold bg-yellow-100/50 px-1.5 py-0.5 rounded-full text-[10px]">
                            <DollarSign className="h-2.5 w-2.5 mr-0.5" />
                            Donation
                        </span>
                    )}
                </div>

                {/* Content */}
                {/* ✅ break-words와 whitespace-pre-wrap으로 줄바꿈 처리 */}
                <p className="whitespace-pre-wrap break-words leading-relaxed text-[13px]">
                    {log.content}
                </p>
            </div>
        </div>
    );
}
