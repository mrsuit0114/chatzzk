import { useEffect, useState } from "react";
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
import { Save, Info, RotateCcw, AlertTriangle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { StringListInput } from "./StringListInput";
import { MyChannelData } from "@shared/types/channel";
import { useQueryClient, useMutation } from "@tanstack/react-query";
import { updateChannelMetadata } from "../api/myChannel";

interface Props {
    channel: MyChannelData; // 백엔드에서 받아온 실제 데이터
    isOwner: boolean;       // 권한 체크
}

export function MyChannelInfoTab({ channel, isOwner }: Props) {
    const queryClient = useQueryClient();

    // 1. 폼 상태 관리 (Props 데이터를 초기값으로 사용)
    const [formData, setFormData] = useState({
        streamerNicknames: channel.streamerNicknames,
        fanNicknames: channel.fanNicknames,
        streamerSex: channel.streamerSex || "", // null일 경우 빈 문자열 처리
        additionalInfo: channel.additionalInfo,
    });

    // 다이얼로그 상태
    const [isResetDialogOpen, setIsResetDialogOpen] = useState(false);

    // 2. Props가 변경되면(예: 리패칭 후) 폼 데이터도 동기화
    useEffect(() => {
        setFormData({
            streamerNicknames: channel.streamerNicknames,
            fanNicknames: channel.fanNicknames,
            streamerSex: channel.streamerSex || "",
            additionalInfo: channel.additionalInfo,
        });
    }, [channel]);

    // 3. 변경 사항 감지 (Dirty Check)
    // 배열 순서나 내용이 다르면 Dirty로 간주
    const isDirty = JSON.stringify(formData) !== JSON.stringify({
        streamerNicknames: channel.streamerNicknames,
        fanNicknames: channel.fanNicknames,
        streamerSex: channel.streamerSex || "",
        additionalInfo: channel.additionalInfo,
    });

    // 4. 저장 Mutation
    const { mutate: saveMetadata, isPending } = useMutation({
        mutationFn: updateChannelMetadata,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['myChannel'] }); // 데이터 갱신
            toast.success("채널 정보가 저장되었습니다.");
        },
        onError: () => {
            toast.error("저장에 실패했습니다. 잠시 후 다시 시도해주세요.");
        }
    });

    // 핸들러: 저장
    const handleSave = () => {
        if (!isOwner) return;
        saveMetadata(formData);
    };

    // 핸들러: 되돌리기 (다이얼로그 오픈)
    const handleResetClick = () => {
        setIsResetDialogOpen(true);
    };

    // 핸들러: 초기화 확정
    const handleConfirmReset = () => {
        setFormData({
            streamerNicknames: channel.streamerNicknames,
            fanNicknames: channel.fanNicknames,
            streamerSex: channel.streamerSex || "",
            additionalInfo: channel.additionalInfo,
        });
        setIsResetDialogOpen(false);
        toast.info("변경 사항이 초기화되었습니다.");
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
                        {!isOwner && (
                            <Badge variant="outline" className="text-orange-500 border-orange-200">
                                <Info className="h-3 w-3 mr-1" /> 읽기 전용 모드 (편집자)
                            </Badge>
                        )}
                    </div>
                </CardHeader>

                <CardContent className="space-y-8">
                    {/* 1. 스트리머 호칭 */}
                    <StringListInput
                        label="스트리머 호칭 (Aliases)"
                        description="방송에서 시청자로부터 불리는 별명이나 호칭을 입력하세요."
                        items={formData.streamerNicknames}
                        onChange={(val) => setFormData(prev => ({ ...prev, streamerNicknames: val }))}
                        disabled={!isOwner}
                    />

                    {/* 2. 팬 호칭 */}
                    <StringListInput
                        label="팬 호칭 (Fan Aliases)"
                        description="시청자나 팬을 지칭하는 용어(팬덤 명)를 입력하세요."
                        items={formData.fanNicknames}
                        onChange={(val) => setFormData(prev => ({ ...prev, fanNicknames: val }))}
                        disabled={!isOwner}
                    />

                    {/* 3. 성별 (한글 값 사용) */}
                    <div className="space-y-3">
                        <div className="space-y-1">
                            <Label className="text-base">스트리머 성별</Label>
                        </div>
                        <RadioGroup
                            value={formData.streamerSex}
                            onValueChange={(val) => isOwner && setFormData(prev => ({ ...prev, streamerSex: val }))}
                            className="flex gap-6 pt-1"
                            disabled={!isOwner}
                        >
                            <div className="flex items-center space-x-2">
                                <RadioGroupItem value="남성" id="male" />
                                <Label htmlFor="male" className="cursor-pointer">남성</Label>
                            </div>
                            <div className="flex items-center space-x-2">
                                <RadioGroupItem value="여성" id="female" />
                                <Label htmlFor="female" className="cursor-pointer">여성</Label>
                            </div>
                        </RadioGroup>
                    </div>

                    {/* 4. 추가 정보 */}
                    <StringListInput
                        label="추가 배경 정보"
                        description="모든 방송에서 공통적으로 언급되는 정보나 스트리머에 대한 배경 지식을 입력하세요. (ex. 방송 주요 컨텐츠, 주변 인물 관계, rp, 컨셉, 팬덤 캐릭터 표현 등)"
                        items={formData.additionalInfo}
                        onChange={(val) => setFormData(prev => ({ ...prev, additionalInfo: val }))}
                        disabled={!isOwner}
                    />
                </CardContent>

                {/* 하단 액션 버튼 (소유자만 표시) */}
                {isOwner && (
                    <CardFooter className="flex justify-between border-t p-6 bg-muted/20">
                        {/* 되돌리기 버튼 */}
                        <Button
                            variant="ghost"
                            onClick={handleResetClick}
                            disabled={!isDirty || isPending}
                            className="text-muted-foreground hover:text-destructive"
                        >
                            <RotateCcw className="mr-2 h-4 w-4" />
                            되돌리기
                        </Button>

                        {/* 저장 버튼 */}
                        <Button onClick={handleSave} disabled={!isDirty || isPending}>
                            {isPending ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                                <Save className="mr-2 h-4 w-4" />
                            )}
                            변경사항 저장
                        </Button>
                    </CardFooter>
                )}
            </Card>

            {/* 변경 취소 확인 다이얼로그 */}
            <AlertDialog open={isResetDialogOpen} onOpenChange={setIsResetDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle className="flex items-center gap-2">
                            <AlertTriangle className="h-5 w-5 text-destructive" />
                            변경 사항 초기화
                        </AlertDialogTitle>
                        <AlertDialogDescription>
                            현재 수정 중인 모든 내용을 취소하고 마지막 저장 상태로 되돌리시겠습니까?
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
