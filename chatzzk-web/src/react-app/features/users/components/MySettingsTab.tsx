import { useState } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge"; // ✅ Badge 추가
import { Eye, EyeOff, UserPlus, Save, Power, Ban, LockKeyhole } from "lucide-react"; // ✅ 아이콘 변경
import { toast } from "sonner";

export function MySettingsTab() {
    const [allowCollection, setAllowCollection] = useState(true);
    const [isChannelPublic, setIsChannelPublic] = useState(true);
    const [analysisVisibility, setAnalysisVisibility] = useState("1d");

    // 편집자 계정 상태 (isActive 필드 추가)
    // null: 계정 자체가 생성되지 않음
    // isActive: false -> 계정은 있지만 비활성화됨 (Soft Delete)
    const [editorAccount, setEditorAccount] = useState<{ id: string; pw: string; isActive: boolean } | null>({
        id: "editor_chzzk",
        pw: "password1234",
        isActive: true, // 기본값: 활성
    });

    const [editId, setEditId] = useState(editorAccount?.id || "");
    const [editPw, setEditPw] = useState(editorAccount?.pw || "");
    const [showEditorPw, setShowEditorPw] = useState(false);

    // --- 핸들러 ---

    const handleSaveSettings = () => {
        toast.promise(new Promise((resolve) => setTimeout(resolve, 1000)), {
            loading: '설정을 저장하는 중...',
            success: '설정이 성공적으로 저장되었습니다.',
            error: '저장에 실패했습니다.',
        });
    };

    // 편집자 정보 수정
    const handleSaveEditor = () => {
        if (!editorAccount) return;
        if (!editId || !editPw) {
            toast.error("아이디와 비밀번호를 모두 입력해주세요.");
            return;
        }
        setEditorAccount({ ...editorAccount, id: editId, pw: editPw });
        toast.success("편집자 계정 정보가 업데이트되었습니다.");
    };

    // ✅ [변경] 계정 상태 토글 (활성 <-> 비활성)
    const handleToggleActive = () => {
        if (!editorAccount) return;

        const nextState = !editorAccount.isActive;
        setEditorAccount({ ...editorAccount, isActive: nextState });

        if (nextState) {
            toast.success("편집자 계정이 다시 활성화되었습니다.", {
                description: "이제 편집자가 로그인할 수 있습니다."
            });
        } else {
            toast.warning("편집자 계정이 비활성화되었습니다.", {
                description: "편집자의 로그인이 차단됩니다. (데이터는 유지됨)"
            });
        }
    };

    // 편집자 계정 최초 생성
    const handleCreateEditor = () => {
        const newAccount = { id: "new_editor", pw: "123456", isActive: true };
        setEditorAccount(newAccount);
        setEditId(newAccount.id);
        setEditPw(newAccount.pw);
        toast.success("새 편집자 계정이 생성되었습니다.", {
            description: "초기 비밀번호를 변경해주세요."
        });
    };

    return (
        <div className="space-y-6">

            {/* 1. 일반 설정 카드 */}
            <Card>
                <CardHeader>
                    <CardTitle>채널 설정</CardTitle>
                    <CardDescription>데이터 수집 및 분석 정보 공개 범위를 설정합니다.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="flex items-center justify-between">
                        <div className="space-y-0.5"><Label className="text-base">데이터 수집 허용</Label></div>
                        <Switch checked={allowCollection} onCheckedChange={setAllowCollection} />
                    </div>
                    <Separator />
                    <div className="flex items-center justify-between">
                        <div className="space-y-0.5"><Label className="text-base">채널 공개</Label></div>
                        <Switch checked={isChannelPublic} onCheckedChange={setIsChannelPublic} />
                    </div>
                    <Separator />

                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div className="space-y-0.5">
                            <Label className="text-base">상세 분석 데이터 공개 시점</Label>
                            <p className="text-sm text-muted-foreground">방송 종료 후 언제부터 상세 데이터를 공개할지 설정합니다.</p>
                        </div>
                        <Select value={analysisVisibility} onValueChange={setAnalysisVisibility}>
                            <SelectTrigger className="w-[180px]">
                                <SelectValue placeholder="선택하세요" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="immediate">즉시</SelectItem>
                                <SelectItem value="6h">방송 종료 6시간 후</SelectItem>
                                <SelectItem value="1d">방송 종료 1일 후</SelectItem>
                                <SelectItem value="2d">방송 종료 2일 후</SelectItem>
                                <SelectItem value="3d">방송 종료 3일 후</SelectItem>
                                <SelectItem value="7d">방송 종료 7일 후</SelectItem>
                                <SelectItem value="never">공개 안 함 (나만 보기)</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </CardContent>
                <CardFooter className="flex justify-end border-t p-6">
                    <Button onClick={handleSaveSettings}>설정 저장</Button>
                </CardFooter>
            </Card>

            {/* 2. 편집자 관리 카드 */}
            <Card className={`transition-colors duration-300 ${editorAccount?.isActive
                ? "border-green-200 dark:border-green-900/50" // 활성 시 초록 테두리
                : "border-border"
                }`}>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <CardTitle>편집자 계정 관리</CardTitle>
                            <CardDescription>
                                비공개 데이터를 열람할 수 있는 편집자 계정을 관리합니다.
                            </CardDescription>
                        </div>
                        {/* ✅ 상태 배지 표시 */}
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
                        <div className={`flex flex-col gap-4 p-5 border rounded-lg transition-all duration-300 ${
                            // ✅ 비활성 시 배경색 변경 및 흐리게 처리
                            editorAccount.isActive
                                ? "bg-background border-green-100 dark:border-green-900/30"
                                : "bg-muted/50 opacity-80"
                            }`}>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label className={!editorAccount.isActive ? "text-muted-foreground" : ""}>편집자 ID</Label>
                                    <Input
                                        value={editId}
                                        onChange={(e) => setEditId(e.target.value)}
                                        // ✅ 비활성 상태면 수정 불가 (UX 선택사항)
                                        disabled={!editorAccount.isActive}
                                        className="bg-background"
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label className={!editorAccount.isActive ? "text-muted-foreground" : ""}>비밀번호</Label>
                                    <div className="relative">
                                        <Input
                                            type={showEditorPw ? "text" : "password"}
                                            value={editPw}
                                            onChange={(e) => setEditPw(e.target.value)}
                                            disabled={!editorAccount.isActive}
                                            className="bg-background pr-10"
                                        />
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="sm"
                                            disabled={!editorAccount.isActive}
                                            className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                                            onClick={() => setShowEditorPw(!showEditorPw)}
                                        >
                                            {showEditorPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                        </Button>
                                    </div>
                                </div>
                            </div>

                            <Separator className="my-1" />

                            <div className="flex justify-between items-center">
                                {/* 상태 설명 텍스트 */}
                                <div className="text-sm text-muted-foreground flex items-center gap-2">
                                    {!editorAccount.isActive && <LockKeyhole className="h-4 w-4" />}
                                    <span>
                                        {editorAccount.isActive
                                            ? "현재 편집자가 정상적으로 활동할 수 있습니다."
                                            : "편집자 계정이 정지되어 로그인이 불가능합니다."}
                                    </span>
                                </div>

                                <div className="flex gap-2">
                                    {/* 정보 수정 저장 버튼 (활성 상태일 때만 노출) */}
                                    {editorAccount.isActive && (
                                        <Button variant="default" size="sm" onClick={handleSaveEditor}>
                                            <Save className="h-4 w-4 mr-2" />
                                            정보 수정
                                        </Button>
                                    )}

                                    {/* ✅ 비활성화/활성화 토글 버튼 */}
                                    <Button
                                        variant={editorAccount.isActive ? "destructive" : "outline"}
                                        size="sm"
                                        onClick={handleToggleActive}
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
                        // 계정이 아예 없는 경우 (Create UI)
                        <div className="flex flex-col items-center justify-center py-10 text-center space-y-4 border-2 border-dashed rounded-lg bg-muted/20">
                            <div className="p-4 bg-background rounded-full shadow-sm">
                                <UserPlus className="h-8 w-8 text-muted-foreground/50" />
                            </div>
                            <div className="space-y-1">
                                <h3 className="font-semibold text-lg">편집자 계정이 없습니다</h3>
                                <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                                    편집자 계정을 생성하면 내 채널의 비공개 데이터를 안전하게 공유할 수 있습니다.
                                </p>
                            </div>
                            <Button onClick={handleCreateEditor} className="mt-2">
                                편집자 계정 생성하기
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
