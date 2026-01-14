import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Eye, EyeOff, UserPlus, Save, Power, Ban, LockKeyhole, Loader2, Info } from "lucide-react";
import { toast } from "sonner";
import { DELAY_OPTIONS, ID_REGEX } from "@shared/constants/service_codes";
import { MyChannelData } from "@shared/types/channel";
import { useQueryClient, useMutation, useQuery } from "@tanstack/react-query";
import { updateChannelSettings, getEditorAccount, createEditorAccount, updateEditorAccount, toggleEditorStatus } from "../api/myChannel";

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

    // 편집자 정보 조회 Query
    const { data: editorAccount, isLoading: isLoadingEditor } = useQuery({
        queryKey: ['myEditor'],
        queryFn: getEditorAccount,
        enabled: isOwner, // Owner만 조회 가능
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
        if (!ID_REGEX.test(editId)) {
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
        if (!ID_REGEX.test(editId)) {
            toast.error("아이디 형식이 올바르지 않습니다.");
            return;
        }
        updateEditor();
    };

    return (
        <div className="space-y-6">
            {/* 1. 채널 설정 (Editor: Read Only, Owner: Edit) */}
            <Card>
                <CardHeader>
                    <div className="flex justify-between items-start">
                        <div>
                            <CardTitle>채널 운영 설정</CardTitle>
                            <CardDescription>데이터 수집 및 분석 결과의 공개 시점을 제어합니다.</CardDescription>
                        </div>
                        {!isOwner && (
                            <Badge variant="outline" className="text-orange-500 border-orange-200">
                                <Info className="h-3 w-3 mr-1" /> 읽기 전용
                            </Badge>
                        )}
                    </div>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* 데이터 수집 허용 */}
                    <div className="flex items-center justify-between">
                        <div className="space-y-0.5">
                            <Label className="text-base">데이터 수집 허용</Label>
                            <p className="text-xs text-muted-foreground">방송 시작 시 자동으로 채팅 및 데이터를 수집합니다.</p>
                        </div>
                        <Switch
                            checked={settings.isCollectionEnabled}
                            onCheckedChange={(v) => setSettings(prev => ({ ...prev, isCollectionEnabled: v }))}
                            disabled={!isOwner} // ✅ 권한 제어
                        />
                    </div>

                    <Separator />

                    {/* VOD 요약 공개 시점 */}
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="space-y-0.5">
                            <Label className="text-base">VOD 요약 공개 시점</Label>
                            <p className="text-xs text-muted-foreground">방송 종료 후 요약본을 일반 사용자에게 공개할 시점입니다.</p>
                        </div>
                        <Select
                            value={settings.vodExposureDelayHours}
                            onValueChange={(v) => setSettings(prev => ({ ...prev, vodExposureDelayHours: v }))}
                            disabled={!isOwner} // ✅ 권한 제어
                        >
                            <SelectTrigger className="w-[180px]">
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
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="space-y-0.5">
                            <Label className="text-base">상세 분석 데이터 공개 시점</Label>
                            <p className="text-xs text-muted-foreground">VOD 요약의 상세 분석 공개 시점입니다.</p>
                        </div>
                        <Select
                            value={settings.vodDetailExposureDelayHours}
                            onValueChange={(v) => setSettings(prev => ({ ...prev, vodDetailExposureDelayHours: v }))}
                            disabled={!isOwner} // ✅ 권한 제어
                        >
                            <SelectTrigger className="w-[180px]">
                                <SelectValue placeholder="선택하세요" />
                            </SelectTrigger>
                            <SelectContent>
                                {DELAY_OPTIONS.map(opt => (
                                    <SelectItem key={`detail-${opt.value}`} value={opt.value}>{opt.label}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>
                </CardContent>

                {/* 저장 버튼은 Owner만 노출 */}
                {isOwner && (
                    <CardFooter className="flex justify-end border-t p-6">
                        <Button onClick={() => saveSettings()} disabled={isSavingSettings}>
                            {isSavingSettings && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            설정 저장
                        </Button>
                    </CardFooter>
                )}
            </Card>

            {/* 2. 편집자 계정 관리 (Owner Only) - Editor에게는 은닉됨 */}
            {isOwner && (
                isLoadingEditor ? (
                    <div className="py-10 text-center text-muted-foreground">편집자 정보를 불러오는 중...</div>
                ) : (
                    <Card className={`transition-colors duration-300 ${editorAccount?.isActive
                        ? "border-green-200 dark:border-green-900/50"
                        : "border-border"
                        }`}>
                        {/* ... 기존 편집자 관리 UI 코드와 동일 (생략 없이 사용) ... */}
                        {/* 기존 코드의 내용을 그대로 유지하되, 필요 시 import 경로나 스타일만 위와 맞춥니다. */}
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <div className="space-y-1">
                                    <CardTitle>편집자 계정 관리</CardTitle>
                                    <CardDescription>
                                        내 채널의 비공개 데이터를 열람할 수 있는 편집자 계정입니다.
                                    </CardDescription>
                                </div>
                                {editorAccount && (
                                    <Badge variant={editorAccount.isActive ? "default" : "secondary"}
                                        className={editorAccount.isActive ? "bg-green-600 hover:bg-green-700" : ""}
                                    >
                                        {editorAccount.isActive ? "Active" : "Inactive"}
                                    </Badge>
                                )}
                            </div>
                        </CardHeader>

                        <CardContent>
                            {editorAccount ? (
                                <div className={`flex flex-col gap-4 p-5 border rounded-lg transition-all duration-300 ${editorAccount.isActive
                                    ? "bg-background border-green-100 dark:border-green-900/30"
                                    : "bg-muted/50 opacity-80"
                                    }`}>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div className="space-y-2">
                                            <Label>편집자 ID</Label>
                                            <div className="flex items-center gap-2">
                                                <Input
                                                    value={editId}
                                                    onChange={(e) => setEditId(e.target.value)}
                                                    disabled={!editorAccount.isActive}
                                                />
                                            </div>
                                        </div>

                                        <div className="space-y-2">
                                            <Label>비밀번호 변경</Label>
                                            <div className="relative">
                                                <Input
                                                    type={showEditorPw ? "text" : "password"}
                                                    value={editPw}
                                                    onChange={(e) => setEditPw(e.target.value)}
                                                    placeholder="변경할 때만 입력"
                                                    disabled={!editorAccount.isActive}
                                                    className="pr-10"
                                                />
                                                <Button
                                                    type="button"
                                                    variant="ghost"
                                                    size="sm"
                                                    className="absolute right-0 top-0 h-full px-3 py-2"
                                                    onClick={() => setShowEditorPw(!showEditorPw)}
                                                    disabled={!editorAccount.isActive}
                                                >
                                                    {showEditorPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                                </Button>
                                            </div>
                                        </div>
                                    </div>

                                    <Separator className="my-1" />

                                    <div className="flex justify-between items-center">
                                        <div className="text-sm text-muted-foreground flex items-center gap-2">
                                            {!editorAccount.isActive && <LockKeyhole className="h-4 w-4" />}
                                            <span>
                                                {editorAccount.isActive
                                                    ? "현재 정상적으로 활동 가능한 상태입니다."
                                                    : "계정이 정지되어 로그인이 불가능합니다."}
                                            </span>
                                        </div>

                                        <div className="flex gap-2">
                                            {editorAccount.isActive && (
                                                <Button variant="default" size="sm" onClick={handleUpdate} disabled={isUpdating}>
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
                                                className={!editorAccount.isActive ? "border-green-600 text-green-600 hover:bg-green-50" : ""}
                                            >
                                                {editorAccount.isActive ? (
                                                    <>
                                                        <Ban className="h-4 w-4 mr-2" />
                                                        계정 비활성화
                                                    </>
                                                ) : (
                                                    <>
                                                        <Power className="h-4 w-4 mr-2" />
                                                        계정 활성화
                                                    </>
                                                )}
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center py-10 text-center space-y-4 border-2 border-dashed rounded-lg bg-muted/20">
                                    {/* ... 생성 UI ... */}
                                    <div className="p-4 bg-background rounded-full shadow-sm">
                                        <UserPlus className="h-8 w-8 text-muted-foreground/50" />
                                    </div>
                                    <div className="space-y-4 w-full max-w-sm">
                                        <div className="space-y-1">
                                            <h3 className="font-semibold text-lg">편집자 계정 생성</h3>
                                            <p className="text-sm text-muted-foreground">
                                                계정을 생성하면 비공개 데이터를 공유할 수 있습니다.
                                            </p>
                                        </div>

                                        <div className="space-y-3 text-left">
                                            <div className="space-y-1">
                                                <Label>아이디</Label>
                                                <div className="flex items-center gap-2">
                                                    <Input value={editId} onChange={(e) => setEditId(e.target.value)} placeholder="user_id" />
                                                </div>
                                            </div>
                                            <div className="space-y-1">
                                                <Label>비밀번호</Label>
                                                <Input type="password" value={editPw} onChange={(e) => setEditPw(e.target.value)} placeholder="최소 8자 이상" />
                                            </div>
                                            <Button onClick={handleCreate} className="w-full" disabled={isCreating}>
                                                {isCreating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                                계정 생성하기
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                )
            )}
        </div>
    );
}
