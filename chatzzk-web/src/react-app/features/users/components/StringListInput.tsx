import { useState, useRef, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { X, Check } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";


interface StringListInputProps {
    label: string;
    description?: string;
    items: string[];
    onChange: (items: string[]) => void;
    disabled?: boolean;
}

export function StringListInput({ label, description, items, onChange, disabled }: StringListInputProps) {
    const [inputValue, setInputValue] = useState("");
    const [editingIndex, setEditingIndex] = useState<number | null>(null);
    const [editValue, setEditValue] = useState("");

    const addInputRef = useRef<HTMLTextAreaElement>(null);
    const editInputRef = useRef<HTMLTextAreaElement>(null);

    // ✅ 공통: Textarea 높이 자동 조절 함수 (Grow -> Scroll)
    const autoResizeTextarea = (element: HTMLTextAreaElement | null) => {
        if (!element) return;

        // 1. 높이를 초기화하여 줄어들었을 때를 감지
        element.style.height = "auto";

        // 2. 스크롤 높이만큼 늘림 (단, CSS max-height에 의해 제한됨)
        element.style.height = `${element.scrollHeight}px`;
    };

    // [수정 모드] 진입 시 초기 높이 설정 및 포커스
    useEffect(() => {
        if (editingIndex !== null && editInputRef.current) {
            const textarea = editInputRef.current;
            textarea.focus();
            // 커서를 맨 끝으로
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
            autoResizeTextarea(textarea);
        }
    }, [editingIndex]);

    // [추가 모드] 입력 핸들러
    const handleAdd = () => {
        const newItem = inputValue.trim();
        if (!newItem) return;

        if (items.includes(newItem)) {
            toast.error("이미 존재하는 항목입니다.");
            return;
        }

        onChange([...items, newItem]);
        setInputValue("");

        // 입력창 높이 초기화
        if (addInputRef.current) {
            addInputRef.current.style.height = "auto";
        }
    };

    // 키보드 이벤트 (Enter: 추가/저장, Shift+Enter: 줄바꿈)
    const handleKeyDown = (
        e: React.KeyboardEvent<HTMLTextAreaElement>,
        action: () => void
    ) => {
        if (e.nativeEvent.isComposing) return;
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            action();
        }
        if (e.key === "Escape") {
            if (editingIndex !== null) cancelEdit();
        }
    };

    // --- 수정 관련 로직 ---

    const startEditing = (index: number) => {
        if (disabled) return;
        setEditingIndex(index);
        setEditValue(items[index]);
    };

    const saveEdit = () => {
        if (editingIndex === null) return;

        const trimmed = editValue.trim();
        if (!trimmed || trimmed === items[editingIndex]) {
            cancelEdit();
            return;
        }

        if (items.some((item, idx) => idx !== editingIndex && item === trimmed)) {
            toast.error("다른 항목과 중복됩니다.");
            return;
        }

        const newItems = [...items];
        newItems[editingIndex] = trimmed;
        onChange(newItems);
        setEditingIndex(null);
    };

    const cancelEdit = () => {
        setEditingIndex(null);
        setEditValue("");
    };

    const handleRemove = (indexToRemove: number) => {
        if (disabled) return;
        onChange(items.filter((_, i) => i !== indexToRemove));
    };

    return (
        <div className="space-y-3">
            <div className="space-y-1">
                <Label className="text-base">{label}</Label>
                <p className="text-sm text-muted-foreground">{description}</p>
            </div>

            {/* 1. 추가(Adding) 영역 */}
            {!disabled && (
                <div className="flex gap-2 items-start">
                    <textarea
                        ref={addInputRef}
                        value={inputValue}
                        onChange={(e) => {
                            setInputValue(e.target.value);
                            autoResizeTextarea(e.target);
                        }}
                        onKeyDown={(e) => handleKeyDown(e, handleAdd)}
                        placeholder="내용 입력 후 Enter"
                        rows={1}
                        className={cn(
                            "flex min-h-[40px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
                            "resize-none overflow-y-auto max-w-md", // 기본 가로 제한
                            "max-h-[150px]" // ✅ 일정 높이 이상 시 스크롤 발생
                        )}
                    />
                    <Button type="button" variant="secondary" onClick={handleAdd} disabled={!inputValue.trim()} className="mt-0.5">
                        추가
                    </Button>
                </div>
            )}

            {/* 2. 리스트 영역 */}
            <div className="flex flex-wrap gap-2 p-3 border rounded-md bg-secondary/10 max-h-[400px] overflow-y-auto items-start align-top">
                {items.length > 0 ? (
                    items.map((item, index) => {
                        // A. 수정 모드
                        if (editingIndex === index) {
                            return (
                                <div key={index} className="flex items-start gap-1 w-full animate-in fade-in zoom-in-95 duration-200">
                                    <textarea
                                        ref={editInputRef}
                                        value={editValue}
                                        onChange={(e) => {
                                            setEditValue(e.target.value);
                                            autoResizeTextarea(e.target);
                                        }}
                                        onKeyDown={(e) => handleKeyDown(e, saveEdit)}
                                        onBlur={cancelEdit}
                                        rows={1}
                                        className={cn(
                                            "flex-1 min-h-[2.5rem] w-full resize-none",
                                            "rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm",
                                            "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
                                            "overflow-y-auto max-h-[150px]" // ✅ 수정 시에도 일정 높이 이상 스크롤
                                        )}
                                    />

                                    {/* 버튼 그룹 (상단 고정) */}
                                    <div className="flex shrink-0 mt-0.5 gap-1">
                                        <Button
                                            type="button"
                                            size="icon" variant="ghost" className="h-8 w-8 hover:bg-green-100 dark:hover:bg-green-900/30 text-green-600"
                                            onMouseDown={(e) => e.preventDefault()} onClick={saveEdit}
                                        >
                                            <Check className="h-4 w-4" />
                                        </Button>
                                        <Button
                                            type="button"
                                            size="icon" variant="ghost" className="h-8 w-8 hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600"
                                            onMouseDown={(e) => e.preventDefault()} onClick={cancelEdit}
                                        >
                                            <X className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                            );
                        }

                        // B. 조회 모드 (Badge)
                        return (
                            <Badge
                                key={index}
                                variant="secondary"
                                className={cn(
                                    "px-3 py-1.5 text-sm bg-background border-input",
                                    "flex items-center gap-2 group max-w-full",
                                    "whitespace-pre-wrap break-all h-auto text-left leading-relaxed", // 줄바꿈 및 긴 텍스트 처리
                                    !disabled && "cursor-pointer hover:border-primary/50 transition-colors"
                                )}
                                onClick={() => !disabled && startEditing(index)}
                            >
                                <span>{item}</span>
                                {!disabled && (
                                    <div className="flex items-center shrink-0 ml-1">
                                        <div className="w-px h-3 bg-border mr-2" />
                                        <button
                                            type="button"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleRemove(index);
                                            }}
                                            className="text-muted-foreground hover:text-destructive focus:outline-none p-0.5 rounded-md hover:bg-muted"
                                        >
                                            <X className="h-3 w-3" />
                                        </button>
                                    </div>
                                )}
                            </Badge>
                        );
                    })
                ) : (
                    <span className="text-sm text-muted-foreground flex items-center px-2 py-1">
                        등록된 정보가 없습니다.
                    </span>
                )}
            </div>
        </div>
    );
}
