// src/features/vod/components/header/ViewSwitcher.tsx

import { Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import { ViewType, VIEW_TYPE } from "../types";


interface ViewSwitcherProps {
    currentView: ViewType;
    onChange: (view: ViewType) => void;
    isInsightLocked?: boolean;
}

export function ViewSwitcher({ currentView, onChange, isInsightLocked }: ViewSwitcherProps) {

    // ✅ 토글 핸들러: 현재 상태를 확인하고 반대로 뒤집습니다.
    const handleToggle = () => {
        if (currentView === VIEW_TYPE.HIGHLIGHT) {
            // Highlight -> Insight 시도
            if (isInsightLocked) {
                // 잠겨있으면 차단 (부모 페이지에서 toast를 띄우겠지만 여기서도 방어)
                return;
            }
            onChange(VIEW_TYPE.INSIGHT);
        } else {
            // Insight -> Highlight
            onChange(VIEW_TYPE.HIGHLIGHT);
        }
    };

    // 잠김 상태에서의 커서 스타일 처리
    const isLockedAndHighlight = currentView === VIEW_TYPE.HIGHLIGHT && isInsightLocked;

    return (
        <div
            // ✅ 컨테이너 전체에 클릭 이벤트 부여
            onClick={handleToggle}
            className={cn(
                "relative flex items-center p-1 bg-muted rounded-lg border h-9 transition-colors select-none",
                // 잠겨있지 않거나, 이미 Insight 뷰라면 포인터 커서 / 잠겨있고 Highlight 뷰라면 금지 커서
                !isLockedAndHighlight ? "cursor-pointer hover:bg-muted/80" : "cursor-not-allowed opacity-80"
            )}
            role="button" // 접근성을 위해 버튼 역할 명시
            tabIndex={0}  // 키보드 탭 접근 가능하게 설정
            onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    handleToggle();
                }
            }}
        >
            {/* Highlight Label (Visual Only) */}
            <div
                className={cn(
                    "relative z-10 px-3 py-1 text-xs font-semibold transition-all duration-200 rounded-md flex items-center gap-2 h-full justify-center min-w-[80px]",
                    currentView === VIEW_TYPE.HIGHLIGHT
                        ? "bg-background text-foreground shadow-sm"
                        : "text-muted-foreground"
                )}
            >
                Highlight
            </div>

            {/* Insight Label (Visual Only) */}
            <div
                className={cn(
                    "relative z-10 px-3 py-1 text-xs font-semibold transition-all duration-200 rounded-md flex items-center gap-2 h-full justify-center min-w-[80px]",
                    currentView === VIEW_TYPE.INSIGHT
                        ? "bg-background text-primary shadow-sm"
                        : "text-muted-foreground"
                )}
            >
                {/* 잠겨있을 때 자물쇠 아이콘 표시 */}
                {isInsightLocked && <Lock className="h-3 w-3" />}
                Insight
            </div>
        </div>
    );
}
