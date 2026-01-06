import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Save, Info, RotateCcw, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { StringListInput } from "./StringListInput";
import { useAuthStore } from "@/stores/auth.store";
import { USER_ROLE } from "@/constants";


// 데이터 타입 정의
interface ChannelInfoData {
    streamerAliases: string[];
    fanAliases: string[];
    gender: "male" | "female";
    additionalInfo: string[];
}

// 초기 데이터 (Mock or Fetch result)
const INITIAL_DATA: ChannelInfoData = {
    streamerAliases: ["침착맨", "이말년", "쏘영이 아빠"],
    fanAliases: ["침수자", "한국인"],
    gender: "male",
    additionalInfo: ["삼국지 매니아", "전 웹툰 작가"],
};

export function MyChannelInfoTab() {
    const user = useAuthStore((state) => state.user);
    const isEditor = user?.role === USER_ROLE.EDITOR;

    // 1. 상태 관리
    const [originalData, setOriginalData] = useState<ChannelInfoData>(INITIAL_DATA);
    const [data, setData] = useState<ChannelInfoData>(INITIAL_DATA);

    // ✅ 다이얼로그 열림 상태 관리
    const [isResetDialogOpen, setIsResetDialogOpen] = useState(false);

    // 2. 변경 사항 감지 (Dirty Check)
    const isDirty = JSON.stringify(originalData) !== JSON.stringify(data);

    // 3. 핸들러
    const handleSave = () => {
        if (isEditor) return;

        // TODO: API Call to save 'data'
        console.log("Saving...", data);

        toast.promise(new Promise((resolve) => setTimeout(resolve, 1000)), {
            loading: '저장 중...',
            success: () => {
                setOriginalData(data);
                return '성공적으로 저장되었습니다.';
            },
            error: '저장 실패',
        });
    };

    // ✅ 초기화 버튼 클릭 시 (다이얼로그 오픈)
    const handleResetClick = () => {
        setIsResetDialogOpen(true);
    };

    // ✅ 다이얼로그에서 [확인] 클릭 시 실제 로직 수행
    const handleConfirmReset = () => {
        setData(originalData); // 원본으로 롤백
        toast.info("변경 사항이 초기화되었습니다.");
        setIsResetDialogOpen(false);
    };

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle>채널 분석 정보 수정</CardTitle>
                            <CardDescription>
                                AI가 방송 요약 및 하이라이트 분석 시 참고할 정보를 관리합니다.
                            </CardDescription>
                        </div>
                        {isEditor && (
                            <Badge variant="outline" className="text-orange-500 border-orange-200">
                                <Info className="h-3 w-3 mr-1" /> 읽기 전용 모드
                            </Badge>
                        )}
                    </div>
                </CardHeader>

                <CardContent className="space-y-8">
                    {/* 1. 스트리머 호칭 */}
                    <StringListInput
                        label="스트리머 호칭 (Aliases)"
                        description="방송에서 불리는 별명이나 호칭을 입력하세요. 클릭하여 수정할 수 있습니다."
                        items={data.streamerAliases}
                        onChange={(val) => setData(prev => ({ ...prev, streamerAliases: val }))}
                        disabled={isEditor}
                    />

                    {/* 2. 팬 호칭 */}
                    <StringListInput
                        label="팬 호칭 (Fan Aliases)"
                        description="시청자나 팬을 지칭하는 용어를 입력하세요."
                        items={data.fanAliases}
                        onChange={(val) => setData(prev => ({ ...prev, fanAliases: val }))}
                        disabled={isEditor}
                    />

                    {/* 3. 성별 (Enum) */}
                    <div className="space-y-3">
                        <div className="space-y-1">
                            <Label className="text-base">스트리머 성별</Label>
                        </div>
                        <RadioGroup
                            value={data.gender}
                            onValueChange={(val) => !isEditor && setData(prev => ({ ...prev, gender: val as "male" | "female" }))}
                            className="flex gap-6"
                            disabled={isEditor}
                        >
                            <div className="flex items-center space-x-2">
                                <RadioGroupItem value="male" id="male" />
                                <Label htmlFor="male">남성</Label>
                            </div>
                            <div className="flex items-center space-x-2">
                                <RadioGroupItem value="female" id="female" />
                                <Label htmlFor="female">여성</Label>
                            </div>
                        </RadioGroup>
                    </div>

                    {/* 4. 추가 정보 */}
                    <StringListInput
                        label="추가 배경 정보"
                        description="AI가 문맥을 이해하는 데 도움이 될만한 정보를 입력하세요."
                        items={data.additionalInfo}
                        onChange={(val) => setData(prev => ({ ...prev, additionalInfo: val }))}
                        disabled={isEditor}
                    />
                </CardContent>

                {/* 하단 액션 버튼 (편집자는 숨김) */}
                {!isEditor && (
                    <CardFooter className="flex justify-between border-t p-6 bg-muted/20">
                        {/* 되돌리기 버튼: 변경사항이 있을 때만 활성화 */}
                        <Button
                            variant="ghost"
                            onClick={handleResetClick} // ✅ 다이얼로그 오픈 함수 연결
                            disabled={!isDirty}
                            className="text-muted-foreground hover:text-destructive"
                        >
                            <RotateCcw className="mr-2 h-4 w-4" />
                            되돌리기
                        </Button>

                        {/* 저장 버튼 */}
                        <Button onClick={handleSave} disabled={!isDirty}>
                            <Save className="mr-2 h-4 w-4" />
                            변경사항 저장
                        </Button>
                    </CardFooter>
                )}
            </Card>

            {/* ✅ 변경 취소 확인 다이얼로그 */}
            <AlertDialog open={isResetDialogOpen} onOpenChange={setIsResetDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle className="flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-destructive" />
                            변경 사항 초기화
                        </AlertDialogTitle>
                        <AlertDialogDescription>
                            현재 수정 중인 모든 내용을 취소하고 마지막 저장 상태로 되돌리시겠습니까?
                            <br />
                            <span className="text-xs text-muted-foreground mt-1 block">
                                (이 작업은 되돌릴 수 없습니다)
                            </span>
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>취소</AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleConfirmReset}
                            className="bg-destructive hover:bg-destructive/90"
                        >
                            초기화
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
