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
import { Save, Info, RotateCcw, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { StringListInput } from "./StringListInput";
import { ChannelMetadata, MyChannelData } from "@shared/types/channel";
import { useQueryClient, useMutation } from "@tanstack/react-query";
import { updateChannelMetadata } from "../api/myChannel";
import { cn } from "@/lib/utils";

interface Props {
    channel: MyChannelData; // 백엔드에서 받아온 실제 데이터
    isOwner: boolean;       // 권한 체크
}

export function MyChannelInfoTab({ channel, isOwner }: Props) {
    const queryClient = useQueryClient();

    // 1. 폼 상태 관리 (Props 데이터를 초기값으로 사용)
    const [formData, setFormData] = useState<ChannelMetadata>(channel.channelMetadata);

    const [isResetDialogOpen, setIsResetDialogOpen] = useState(false);

    // 2. Props 동기화: 리패칭 등으로 데이터가 갱신되면 폼 상태도 업데이트
    useEffect(() => {
        setFormData(channel.channelMetadata);
    }, [channel]);

    // 3. 변경 사항 감지 (Dirty Check)
    const isDirty = JSON.stringify(formData) !== JSON.stringify(channel.channelMetadata);

    // 4. 저장 Mutation
    const { mutate: saveMetadata, isPending } = useMutation({
        mutationFn: updateChannelMetadata,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['myChannel'] });
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

    // 핸들러: 초기화 확정
    const handleConfirmReset = () => {
        setFormData(channel.channelMetadata);
        setIsResetDialogOpen(false);
        toast.info("변경 사항이 초기화되었습니다.");
    };

    return (
        <div className="space-y-6 pb-8">
            <Card className="border-border/60 shadow-sm">
                <CardHeader className="pb-4 border-b bg-muted/10">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="space-y-1">
                            <CardTitle className="text-xl">채널 분석 정보 관리</CardTitle>
                            <CardDescription className="max-w-2xl leading-relaxed">
                                AI가 방송 내용을 분석하고 요약할 때 사용하는 핵심 메타데이터입니다.
                            </CardDescription>
                        </div>
                        {!isOwner && (
                            <Badge variant="outline" className="h-8 px-3 text-orange-600 bg-orange-50 border-orange-200 gap-2">
                                <Info className="h-3.5 w-3.5" />
                                <span>읽기 전용 (편집자)</span>
                            </Badge>
                        )}
                    </div>
                </CardHeader>

                <CardContent className="space-y-10 py-8">
                    {/* 1. 스트리머 호칭 */}
                    <StringListInput
                        label="스트리머 호칭"
                        description="시청자로부터 불리는 호칭을 입력하세요. (반드시 입력할 것을 권장합니다.)"
                        items={formData.streamerNicknames}
                        onChange={(val) => setFormData(prev => ({ ...prev, streamerNicknames: val }))}
                        disabled={!isOwner}
                    />

                    {/* 2. 팬 호칭 */}
                    <StringListInput
                        label="팬 호칭"
                        description="스트리머가 시청자나 팬을 지칭하는 호칭을 입력하세요. (없는 경우 비워두세요.)"
                        items={formData.fanNicknames}
                        onChange={(val) => setFormData(prev => ({ ...prev, fanNicknames: val }))}
                        disabled={!isOwner}
                    />

                    {/* 3. 성별 */}
                    <div className="space-y-3">
                        <Label className="text-base font-semibold">스트리머 성별</Label>
                        <Card className="p-4 border bg-muted/20 w-fit">
                            <RadioGroup
                                value={formData.streamerSex}
                                onValueChange={(val) => isOwner && setFormData(prev => ({ ...prev, streamerSex: val as any }))}
                                className="flex gap-8"
                                disabled={!isOwner}
                            >
                                <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="남성" id="male" />
                                    <Label htmlFor="male" className={cn("cursor-pointer font-medium", !isOwner && "cursor-not-allowed opacity-70")}>남성</Label>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <RadioGroupItem value="여성" id="female" />
                                    <Label htmlFor="female" className={cn("cursor-pointer font-medium", !isOwner && "cursor-not-allowed opacity-70")}>여성</Label>
                                </div>
                            </RadioGroup>
                        </Card>
                    </div>

                    {/* 4. 추가 정보 */}
                    <StringListInput
                        label="배경 지식 및 컨셉 - 가장 범용적인 정보를 우선하여 3개 이하 권장"
                        description="자신의 대부분 방송에서 언급되어 AI가 참고할 맥락 정보를 입력하세요. ex) 주요 컨텐츠, 주변 인물 관계, RP, 스트리머 경력 등"
                        items={formData.additionalInfo}
                        onChange={(val) => setFormData(prev => ({ ...prev, additionalInfo: val }))}
                        disabled={!isOwner}
                    />
                </CardContent>

                {isOwner && (
                    <CardFooter className={cn(
                        "flex justify-between border-t p-6 transition-colors duration-300 sticky bottom-0 z-10",
                        isDirty ? "bg-primary/5 border-primary/20" : "bg-background"
                    )}>
                        <Button
                            variant="ghost"
                            onClick={() => setIsResetDialogOpen(true)}
                            disabled={!isDirty || isPending}
                            className="text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                        >
                            <RotateCcw className="mr-2 h-4 w-4" />
                            초기화
                        </Button>

                        <Button
                            onClick={handleSave}
                            disabled={!isDirty || isPending}
                            className={cn(isDirty && "animate-pulse-subtle shadow-md")}
                        >
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

            <AlertDialog open={isResetDialogOpen} onOpenChange={setIsResetDialogOpen}>
                <AlertDialogContent>
                    <AlertDialogHeader>
                        <AlertDialogTitle>변경 사항 초기화</AlertDialogTitle>
                        <AlertDialogDescription>
                            수정 중인 모든 내용을 취소하고 마지막 저장 상태로 되돌리시겠습니까?<br />
                            이 작업은 되돌릴 수 없습니다.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel>취소</AlertDialogCancel>
                        <AlertDialogAction onClick={handleConfirmReset} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                            초기화
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}
