import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Eye, EyeOff, UserPlus, Save, Power, Ban, LockKeyhole, Loader2, Info, UserCog, Lock } from "lucide-react";
import { toast } from "sonner";
import { DELAY_OPTIONS, UserIdSchema } from "@shared/constants/service_codes";
import { MyChannelData } from "@shared/types/channel";
import { useQueryClient, useMutation, useQuery } from "@tanstack/react-query";
import { updateChannelSettings, getEditorAccount, createEditorAccount, updateEditorAccount, toggleEditorStatus } from "../api/myChannel";
import { cn } from "@/lib/utils";

interface Props {
    channel: MyChannelData;
    isOwner: boolean;
}

export function MySettingsTab({ channel, isOwner }: Props) {
    const queryClient = useQueryClient();

    // ----------------------------------------------------------------
    // 1. 채널 설정 상태 (Props 초기값 사용)
    // ----------------------------------------------------------------
    const [settings, setSettings] = useState({
        isCollectionEnabled: channel.isCollectionEnabled,
        vodExposureDelayHours: channel.vodExposureDelayHours.toString(),       // 요약 공개 시점
        vodDetailExposureDelayHours: channel.vodDetailExposureDelayHours.toString(), // 상세 분석 공개 시점
    });

    // 변경사항 저장 Mutation
    const { mutate: saveSettings, isPending: isSavingSettings } = useMutation({
        mutationFn: async () => {
            await updateChannelSettings({
                isCollectionEnabled: settings.isCollectionEnabled,
                vodExposureDelayHours: parseInt(settings.vodExposureDelayHours),
                vodDetailExposureDelayHours: parseInt(settings.vodDetailExposureDelayHours),
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['myChannel'] });
            toast.success("채널 설정이 저장되었습니다.");
        },
        onError: () => toast.error("설정 저장에 실패했습니다.")
    });

    // ----------------------------------------------------------------
    // 2. 편집자 계정 관리
    // ----------------------------------------------------------------
    const [isEditorRevealed, setIsEditorRevealed] = useState(false);

    // ✅ API 호출 최적화: Owner이면서 + 블러가 해제되었을 때만 fetch
    const { data: editorAccount, isLoading: isLoadingEditor } = useQuery({
        queryKey: ['myEditor'],
        queryFn: getEditorAccount,
        enabled: isOwner && isEditorRevealed,
    });

    // 입력 폼 상태
    const [editId, setEditId] = useState("");
    const [editPw, setEditPw] = useState("");
    const [showEditorPw, setShowEditorPw] = useState(false);

    // 편집자 데이터 로드 시 입력창 초기화
    useEffect(() => {
        if (editorAccount) {
            setEditId(editorAccount.id);
            setEditPw(""); // 비밀번호는 보안상 비워둠
        } else {
            setEditId("");
            setEditPw("");
        }
    }, [editorAccount]);

    // [Mutation] 편집자 생성
    const { mutate: createEditor, isPending: isCreating } = useMutation({
        mutationFn: () => createEditorAccount(editId, editPw),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['myEditor'] });
            toast.success("편집자 계정이 생성되었습니다.");
        },
        onError: (err: any) => toast.error(err.message || "계정 생성 실패")
    });

    // [Mutation] 편집자 정보 수정
    const { mutate: updateEditor, isPending: isUpdating } = useMutation({
        mutationFn: () => updateEditorAccount({ id: editId, password: editPw || undefined }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['myEditor'] });
            toast.success("계정 정보가 수정되었습니다.");
            setEditPw(""); // 수정 후 비번창 초기화
        },
        onError: (err: any) => toast.error(err.message || "수정 실패")
    });

    // [Mutation] 상태 토글 (Ban/Unban)
    const { mutate: toggleStatus, isPending: isToggling } = useMutation({
        mutationFn: () => toggleEditorStatus(!editorAccount!.isActive),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['myEditor'] });
            const msg = !editorAccount!.isActive ? "활성화되었습니다." : "비활성화되었습니다.";
            toast.success(`계정이 ${msg}`);
        },
        onError: () => toast.error("상태 변경 실패")
    });


    // 핸들러: 생성 요청
    const handleCreate = () => {
        if (!UserIdSchema.safeParse(editId).success) {
            toast.error("아이디는 4~20자의 영문 소문자와 숫자만 가능합니다.");
            return;
        }
        if (editPw.length < 8) {
            toast.error("비밀번호는 최소 8자 이상이어야 합니다.");
            return;
        }
        createEditor();
    };

    // 핸들러: 수정 요청
    const handleUpdate = () => {
        if (!UserIdSchema.safeParse(editId).success) {
            toast.error("아이디 형식이 올바르지 않습니다.");
            return;
        }
        updateEditor();
    };

    return (
        <div className="space-y-8 pb-8">
            {/* 1. 채널 운영 설정 */}
            <Card className="border-border/60 shadow-sm">
                <CardHeader>
                    <div className="flex justify-between items-start">
                        <div className="space-y-1">
                            <CardTitle>채널 운영 설정</CardTitle>
                            <CardDescription>데이터 수집 활성화 여부 및 분석 결과의 공개 시점을 제어합니다. 플랫폼에 게시된 시점을 기준으로 합니다.</CardDescription>
                        </div>
                        {!isOwner && (
                            <Badge variant="outline" className="text-orange-600 bg-orange-50 border-orange-200 gap-1.5 h-7">
                                <Info className="h-3 w-3" /> 읽기 전용
                            </Badge>
                        )}
                    </div>
                </CardHeader>
                <CardContent className="space-y-8">
                    {/* 데이터 수집 허용 */}
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <Label className="text-base font-medium">데이터 수집 활성화</Label>
                            <p className="text-sm text-muted-foreground">채팅 및 방송 데이터를 수집하고 분석 및 요약을 생성합니다.</p>
                        </div>
                        <Switch
                            checked={settings.isCollectionEnabled}
                            onCheckedChange={(v) => setSettings(prev => ({ ...prev, isCollectionEnabled: v }))}
                            disabled={!isOwner}
                        />
                    </div>

                    <Separator />

                    <div className="grid gap-6 md:grid-cols-2">
                        {/* VOD 요약 공개 시점 */}
                        <div className="space-y-3">
                            <div className="space-y-1">
                                <Label className="text-base font-medium">방송 요약 공개 시점</Label>
                                <p className="text-xs text-muted-foreground">일반 사용자에게 노출되기까지의 대기 시간입니다.</p>
                            </div>
                            <Select
                                value={settings.vodExposureDelayHours}
                                onValueChange={(v) => setSettings(prev => ({ ...prev, vodExposureDelayHours: v }))}
                                disabled={!isOwner}
                            >
                                <SelectTrigger className="w-full">
                                    <SelectValue placeholder="선택하세요" />
                                </SelectTrigger>
                                <SelectContent>
                                    {DELAY_OPTIONS.map(opt => (
                                        <SelectItem key={`summary-${opt.value}`} value={opt.value}>{opt.label}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>

                        {/* 상세 분석 공개 시점 */}
                        <div className="space-y-3">
                            <div className="space-y-1">
                                <Label className="text-base font-medium">상세 분석 공개 시점</Label>
                                <p className="text-xs text-muted-foreground">일반 사용자에게 상세 분석이 허용되기까지의 시간입니다.</p>
                            </div>
                            <Select
                                value={settings.vodDetailExposureDelayHours}
                                onValueChange={(v) => setSettings(prev => ({ ...prev, vodDetailExposureDelayHours: v }))}
                                disabled={!isOwner}
                            >
                                <SelectTrigger className="w-full">
                                    <SelectValue placeholder="선택하세요" />
                                </SelectTrigger>
                                <SelectContent>
                                    {DELAY_OPTIONS.map(opt => (
                                        <SelectItem key={`detail-${opt.value}`} value={opt.value}>{opt.label}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                </CardContent>

                {isOwner && (
                    <CardFooter className="flex justify-end border-t p-6 bg-muted/20">
                        <Button onClick={() => saveSettings()} disabled={isSavingSettings} className="min-w-[100px]">
                            {isSavingSettings ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                            설정 저장
                        </Button>
                    </CardFooter>
                )}
            </Card>

            {/* 2. 편집자 계정 관리 (Owner Only) */}
            {isOwner && (
                <div className="relative rounded-xl border border-border shadow-sm overflow-hidden bg-card transition-all h-auto">

                    {/* ✅ [Overlay] 블러 처리된 커버 (미조회 상태) */}
                    {!isEditorRevealed && (
                        <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-background/60 backdrop-blur-md gap-5 transition-all duration-500">
                            <div className="p-4 bg-muted/80 rounded-full ring-1 ring-border shadow-sm">
                                <Lock className="h-8 w-8 text-muted-foreground" />
                            </div>
                            <div className="text-center space-y-1.5">
                                <h3 className="font-semibold text-lg">편집자 계정 관리</h3>
                            </div>
                            <Button onClick={() => setIsEditorRevealed(true)} className="gap-2">
                                <UserCog className="h-4 w-4" />
                                관리 메뉴 열기
                            </Button>
                        </div>
                    )}

                    {/* ✅ [Content] 실제 내용 (Reveal 전에는 블러 처리된 Dummy 처럼 보임) */}
                    <div className={cn(
                        "p-6 space-y-6 transition-all duration-500",
                        !isEditorRevealed && "opacity-50 blur-sm pointer-events-none min-h-[300px]"
                    )}>
                        {/* 헤더 영역 */}
                        <div className="flex items-center justify-between">
                            <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                    <UserCog className="h-5 w-5 text-primary" />
                                    <h3 className="font-semibold text-xl leading-none tracking-tight">편집자 계정 관리</h3>
                                </div>
                                <p className="text-sm text-muted-foreground">
                                    내 채널의 비공개 데이터를 열람할 수 있는 부계정입니다.
                                </p>
                            </div>
                            {/* 배지 (데이터 로드 후에만 표시) */}
                            {editorAccount && (
                                <Badge
                                    variant={editorAccount.isActive ? "default" : "secondary"}
                                    className={editorAccount.isActive ? "bg-green-600" : ""}
                                >
                                    {editorAccount.isActive ? "Active" : "Inactive"}
                                </Badge>
                            )}
                        </div>

                        <Separator />

                        {/* 로딩 및 데이터 표시 영역 */}
                        {isEditorRevealed && isLoadingEditor ? (
                            <div className="py-20 text-center text-muted-foreground bg-muted/10 rounded-xl border border-dashed animate-pulse">
                                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-3 opacity-50" />
                                <p>계정 정보를 안전하게 불러오는 중...</p>
                            </div>
                        ) : (
                            // 데이터가 있거나(수정) 없을 때(생성)
                            <>
                                {editorAccount ? (
                                    // A. 수정 모드
                                    <div className={cn(
                                        "flex flex-col gap-6 p-6 border rounded-xl bg-card transition-all",
                                        editorAccount.isActive ? "border-green-200 bg-green-50/5" : "bg-muted/30 border-dashed"
                                    )}>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            <div className="space-y-2">
                                                <Label>편집자 ID</Label>
                                                <Input
                                                    value={editId}
                                                    onChange={(e) => setEditId(e.target.value)}
                                                    disabled={!editorAccount.isActive}
                                                    className="bg-background"
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <Label>비밀번호 변경</Label>
                                                <div className="relative">
                                                    <Input
                                                        type={showEditorPw ? "text" : "password"}
                                                        value={editPw}
                                                        onChange={(e) => setEditPw(e.target.value)}
                                                        placeholder={editorAccount.isActive ? "변경 시에만 입력" : "비활성 상태"}
                                                        disabled={!editorAccount.isActive}
                                                        className="pr-10 bg-background"
                                                    />
                                                    <Button
                                                        type="button" variant="ghost" size="sm"
                                                        className="absolute right-0 top-0 h-full px-3"
                                                        onClick={() => setShowEditorPw(!showEditorPw)}
                                                        disabled={!editorAccount.isActive}
                                                    >
                                                        {showEditorPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                                    </Button>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex flex-col sm:flex-row justify-between items-center gap-4 pt-2 border-t mt-2">
                                            <div className="text-xs text-muted-foreground flex items-center gap-1.5 bg-background border px-3 py-1.5 rounded-full">
                                                {!editorAccount.isActive ? <LockKeyhole className="h-3.5 w-3.5" /> : <Info className="h-3.5 w-3.5" />}
                                                <span>
                                                    {editorAccount.isActive
                                                        ? "현재 정상적으로 활동 가능한 상태입니다."
                                                        : "계정이 정지되어 로그인이 불가능합니다."}
                                                </span>
                                            </div>
                                            <div className="flex gap-2 w-full sm:w-auto">
                                                {editorAccount.isActive && (
                                                    <Button variant="default" size="sm" onClick={handleUpdate} disabled={isUpdating} className="flex-1 sm:flex-none">
                                                        {isUpdating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                                        <Save className="h-4 w-4 mr-2" />
                                                        정보 수정
                                                    </Button>
                                                )}
                                                <Button
                                                    variant={editorAccount.isActive ? "destructive" : "outline"}
                                                    size="sm"
                                                    onClick={() => toggleStatus()}
                                                    disabled={isToggling}
                                                    className={cn("flex-1 sm:flex-none", !editorAccount.isActive && "border-green-600 text-green-600 hover:bg-green-50")}
                                                >
                                                    {editorAccount.isActive ? (
                                                        <> <Ban className="h-4 w-4 mr-2" /> 계정 비활성화 </>
                                                    ) : (
                                                        <> <Power className="h-4 w-4 mr-2" /> 계정 활성화 </>
                                                    )}
                                                </Button>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    // B. 생성 모드 (데이터 없을 때)
                                    // 블러 상태일 때도 이 레이아웃이 뒷배경으로 깔려있음 (단, 내용은 비어있음)
                                    <div className="flex flex-col items-center justify-center py-10 text-center space-y-5 border-2 border-dashed rounded-xl bg-muted/5">
                                        <div className="p-4 bg-background rounded-full shadow-sm ring-1 ring-border">
                                            <UserPlus className="h-8 w-8 text-primary/60" />
                                        </div>
                                        <div className="space-y-1">
                                            <h3 className="font-semibold text-lg">편집자 계정 생성</h3>
                                            <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                                                편집자 계정은 비공개 데이터 열람 권한이 부여됩니다.
                                            </p>
                                        </div>
                                        <div className="w-full max-w-sm bg-card p-6 rounded-lg border shadow-sm space-y-4 text-left">
                                            <div className="space-y-2">
                                                <Label>아이디</Label>
                                                <Input value={editId} onChange={(e) => setEditId(e.target.value)} placeholder="알파벳 소문자와 숫자의 조합 4자 이상" />
                                            </div>
                                            <div className="space-y-2">
                                                <Label>비밀번호</Label>
                                                <Input type="password" value={editPw} onChange={(e) => setEditPw(e.target.value)} placeholder="최소 8자 이상" />
                                            </div>
                                            <Button onClick={handleCreate} className="w-full" disabled={isCreating}>
                                                {isCreating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                                계정 생성하기
                                            </Button>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
