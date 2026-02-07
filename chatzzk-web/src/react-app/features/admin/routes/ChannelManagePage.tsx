import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Search, AlertTriangle, UserCheck, Loader2, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage, FormDescription } from "@/components/ui/form";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";

import { DELAY_OPTIONS, PLATFORM_CODE, PlatformCodeSchema } from "@shared/constants/service_codes";
import { StringListInput } from "@/features/users/components/StringListInput";
import { getChannelDetail, AdminChannelDetail, updateChannelGeneral, transferOwnership } from "../api/channel";

const ChannelMetadataFormShape = z.object({
    streamerNicknames: z.array(z.string()).default([]),
    streamerSex: z.enum(["남성", "여성"]).default("남성"),
    fanNicknames: z.array(z.string()).default([]),
    additionalInfo: z.array(z.string()).default([]),
});

const searchSchema = z.object({
    platform: PlatformCodeSchema,
    channelId: z.string().min(1, "채널 ID를 입력하세요."),
});

// --- 수정 폼 스키마 ---
const editSchema = z.object({
    channelName: z.string().min(1, "채널명을 입력하세요."),
    isCollectionEnabled: z.boolean(),
    vodExposureDelayHours: z.coerce.number().min(0),
    vodDetailExposureDelayHours: z.coerce.number().min(0),
    metadata: ChannelMetadataFormShape, // 순수 CamelCase 스키마 (Shared)
});

type EditFormValues = z.infer<typeof editSchema>;

export function ChannelManagePage() {
    const [searchParams, setSearchParams] = useState<{ platform: string, channelId: string } | null>(null);

    // 1. 검색 폼
    const searchForm = useForm<z.infer<typeof searchSchema>>({
        resolver: zodResolver(searchSchema),
        defaultValues: { platform: PLATFORM_CODE.CHZZK, channelId: "" }
    });

    // 2. 데이터 조회
    const { data: channelData, isLoading, refetch, isError } = useQuery({
        queryKey: ['adminChannel', searchParams],
        queryFn: () => getChannelDetail(searchParams!),
        enabled: !!searchParams,
        retry: false
    });

    const onSearch = (values: z.infer<typeof searchSchema>) => {
        setSearchParams(values);
    };

    return (
        <div className="max-w-6xl mx-auto space-y-8 pb-20">
            <div className="space-y-2">
                <h1 className="text-3xl font-bold tracking-tight">채널 관리 및 수정</h1>
                <p className="text-muted-foreground">특정 채널을 식별하여 정보를 수정하거나 소유권을 이전합니다.</p>
            </div>

            {/* 검색 섹션 */}
            <Card className="bg-muted/30 border-dashed">
                <CardContent className="pt-6">
                    <Form {...searchForm}>
                        <form onSubmit={searchForm.handleSubmit(onSearch)} className="flex flex-col md:flex-row gap-4 items-end">
                            <FormField
                                control={searchForm.control}
                                name="platform"
                                render={({ field }) => (
                                    <FormItem className="w-full md:w-[200px]">
                                        <FormLabel>플랫폼</FormLabel>
                                        <Select onValueChange={field.onChange} value={field.value}>
                                            <FormControl><SelectTrigger><SelectValue /></SelectTrigger></FormControl>
                                            <SelectContent>
                                                <SelectItem value={PLATFORM_CODE.CHZZK}>치지직</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={searchForm.control}
                                name="channelId"
                                render={({ field }) => (
                                    <FormItem className="flex-1 w-full">
                                        <FormLabel>채널 고유 ID (Platform Channel ID)</FormLabel>
                                        <FormControl><Input placeholder="URL 해시값 또는 ID 입력..." {...field} /></FormControl>
                                    </FormItem>
                                )}
                            />
                            <Button type="submit" size="lg" disabled={isLoading}>
                                {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Search className="mr-2 h-4 w-4" />}
                                조회
                            </Button>
                        </form>
                    </Form>
                </CardContent>
            </Card>

            {/* 결과 없음 또는 에러 */}
            {isError && (
                <Alert variant="destructive">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>해당하는 채널을 찾을 수 없습니다. 플랫폼과 ID를 확인해주세요.</AlertDescription>
                </Alert>
            )}

            {/* 검색 결과 및 수정 영역 */}
            {channelData && (
                <div className="grid gap-8 lg:grid-cols-[2fr_1fr] animate-in fade-in slide-in-from-bottom-4">

                    {/* 왼쪽: 일반 정보 및 메타데이터 수정 */}
                    <div className="space-y-6">
                        <EditForm channel={channelData} onSuccess={refetch} />
                    </div>

                    {/* 오른쪽: 소유권 관리 (Danger Zone) */}
                    <div className="space-y-6">
                        <OwnershipManager channel={channelData} onSuccess={refetch} />
                    </div>
                </div>
            )}
        </div>
    );
}

// ------------------------------------------------------------------
// 하위 컴포넌트 1: 일반 수정 폼 (General + Metadata)
// ------------------------------------------------------------------
function EditForm({ channel, onSuccess }: { channel: AdminChannelDetail, onSuccess: () => void }) {
    // 초기값 매핑: DB(Snake/Raw) -> Form(Camel)
    const form = useForm({
        resolver: zodResolver(editSchema),
        defaultValues: {
            channelName: channel.channel_name,
            isCollectionEnabled: channel.is_collection_enabled,
            vodExposureDelayHours: String(channel.vod_exposure_delay_hours),
            vodDetailExposureDelayHours: String(channel.vod_detail_exposure_delay_hours),
            metadata: {
                // channel_metadata가 null일 경우 대비
                streamerNicknames: channel.channel_metadata?.attributes.streamerNicknames || [],
                streamerSex: (channel.channel_metadata?.attributes.streamerSex as any) || "남성",
                fanNicknames: channel.channel_metadata?.attributes.fanNicknames || [],
                additionalInfo: channel.channel_metadata?.attributes.additionalInfo || [],
            }
        }
    });

    // 채널 데이터가 변경되면 폼 리셋 (재검색 시)
    useEffect(() => {
        form.reset({
            channelName: channel.channel_name,
            isCollectionEnabled: channel.is_collection_enabled,
            vodExposureDelayHours: String(channel.vod_exposure_delay_hours),
            vodDetailExposureDelayHours: String(channel.vod_detail_exposure_delay_hours),
            metadata: {
                streamerNicknames: channel.channel_metadata?.attributes.streamerNicknames || [],
                streamerSex: (channel.channel_metadata?.attributes.streamerSex as any) || "남성",
                fanNicknames: channel.channel_metadata?.attributes.fanNicknames || [],
                additionalInfo: channel.channel_metadata?.attributes.additionalInfo || [],
            }
        });
    }, [channel, form]);

    const { mutate, isPending } = useMutation({
        mutationFn: (values: EditFormValues) => updateChannelGeneral(channel.id, values),
        onSuccess: () => {
            toast.success("채널 정보가 수정되었습니다.");
            onSuccess();
        },
        onError: (err: any) => toast.error(`수정 실패: ${err.response?.data?.error || err.message}`)
    });

    return (
        <Card>
            <CardHeader>
                <CardTitle>채널 정보 및 메타데이터</CardTitle>
                <CardDescription>기본 정보와 AI 분석 설정을 수정합니다.</CardDescription>
            </CardHeader>
            <Form {...form}>
                <form onSubmit={form.handleSubmit((data) => mutate(data))}>
                    <CardContent className="space-y-6">
                        {/* 기본 설정 */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <FormField
                                control={form.control}
                                name="channelName"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>채널명</FormLabel>
                                        <FormControl><Input {...field} /></FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="isCollectionEnabled"
                                render={({ field }) => (
                                    <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3 shadow-sm">
                                        <div className="space-y-0.5">
                                            <FormLabel>데이터 수집 활성화</FormLabel>
                                            <FormDescription>비활성화 시 VOD 수집이 중단됩니다.</FormDescription>
                                        </div>
                                        <FormControl>
                                            <Switch checked={field.value} onCheckedChange={field.onChange} />
                                        </FormControl>
                                    </FormItem>
                                )}
                            />
                        </div>

                        <Separator />

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <FormField
                                control={form.control}
                                name="vodExposureDelayHours"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>요약 노출 지연 시간</FormLabel>
                                        <Select onValueChange={field.onChange} value={String(field.value)}>
                                            <FormControl>
                                                <SelectTrigger>
                                                    <SelectValue placeholder="선택하세요" />
                                                </SelectTrigger>
                                            </FormControl>
                                            <SelectContent>
                                                {DELAY_OPTIONS.map(opt => (
                                                    <SelectItem key={`summary-${opt.value}`} value={opt.value}>
                                                        {opt.label}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                        <FormDescription>VOD 요약본이 사용자에게 공개되기까지의 대기 시간입니다.</FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="vodDetailExposureDelayHours"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>상세 분석 노출 지연 시간</FormLabel>
                                        <Select onValueChange={field.onChange} value={String(field.value)}>
                                            <FormControl>
                                                <SelectTrigger>
                                                    <SelectValue placeholder="선택하세요" />
                                                </SelectTrigger>
                                            </FormControl>
                                            <SelectContent>
                                                {DELAY_OPTIONS.map(opt => (
                                                    <SelectItem key={`detail-${opt.value}`} value={opt.value}>
                                                        {opt.label}
                                                    </SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                        <FormDescription>상세 분석 데이터의 공개 대기 시간입니다.</FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        </div>

                        <Separator />

                        {/* 메타데이터 (StringListInput 재사용) */}
                        <div className="space-y-6">
                            <FormField
                                control={form.control}
                                name="metadata.streamerSex"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>스트리머 성별</FormLabel>
                                        <Select onValueChange={field.onChange} value={field.value}>
                                            <FormControl><SelectTrigger><SelectValue /></SelectTrigger></FormControl>
                                            <SelectContent>
                                                <SelectItem value="남성">남성</SelectItem>
                                                <SelectItem value="여성">여성</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </FormItem>
                                )}
                            />
                            <Controller
                                control={form.control}
                                name="metadata.streamerNicknames"
                                render={({ field }) => (
                                    <StringListInput
                                        label="스트리머 호칭"
                                        items={field.value || []}
                                        onChange={field.onChange}
                                    />
                                )}
                            />
                            <Controller
                                control={form.control}
                                name="metadata.fanNicknames"
                                render={({ field }) => (
                                    <StringListInput
                                        label="팬 호칭"
                                        items={field.value || []}
                                        onChange={field.onChange}
                                    />
                                )}
                            />
                            <Controller
                                control={form.control}
                                name="metadata.additionalInfo"
                                render={({ field }) => (
                                    <StringListInput
                                        label="배경 지식 및 컨셉"
                                        items={field.value || []}
                                        onChange={field.onChange}
                                    />
                                )}
                            />
                        </div>
                    </CardContent>
                    <CardFooter className="justify-end border-t pt-4 bg-muted/10">
                        <Button type="submit" disabled={isPending}>
                            {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            변경사항 저장
                        </Button>
                    </CardFooter>
                </form>
            </Form>
        </Card>
    );
}

// ------------------------------------------------------------------
// 하위 컴포넌트 2: 소유권 관리 (Danger Zone)
// ------------------------------------------------------------------
function OwnershipManager({ channel, onSuccess }: { channel: AdminChannelDetail, onSuccess: () => void }) {
    const [targetUser, setTargetUser] = useState("");

    const { mutate, isPending } = useMutation({
        mutationFn: (userName: string) => transferOwnership(channel.id, userName),
        onSuccess: (_data) => {
            toast.success("소유권이 성공적으로 이전되었습니다.");
            setTargetUser("");
            onSuccess(); // 데이터 리패치
        },
        onError: (err: any) => toast.error(`이전 실패: ${err.response?.data?.error || err.message}`)
    });

    const currentOwner = channel.owner?.user_name;

    const handleTransfer = () => {
        if (!targetUser) return;
        if (targetUser === currentOwner) {
            toast.warning("이미 현재 소유자입니다.");
            return;
        }
        if (!confirm(`[경고] 정말로 소유권을 변경하시겠습니까?\n\n현재 소유자: ${currentOwner || '없음'}\n새 소유자: ${targetUser}\n\n기존 소유자는 USER로 강등되며, 새 소유자는 OWNER로 승격됩니다.`)) return;

        mutate(targetUser);
    };

    return (
        <Card className="border-destructive/50 shadow-sm overflow-hidden">
            <CardHeader className="bg-destructive/5 border-b border-destructive/10">
                <CardTitle className="text-destructive flex items-center gap-2 text-lg">
                    <AlertTriangle className="h-5 w-5" /> 소유권 관리
                </CardTitle>
                <CardDescription>
                    채널의 소유자를 변경합니다. 이 작업은 즉시 반영되며 사용자 권한을 변경합니다.
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6 pt-6">
                {/* 현재 상태 */}
                <div className="flex flex-col gap-2">
                    <span className="text-sm font-medium text-muted-foreground">현재 소유자</span>
                    <div>
                        {currentOwner ? (
                            <Badge variant="outline" className="text-base py-1.5 px-3 gap-2 font-medium">
                                <UserCheck className="w-4 h-4 text-green-600" />
                                {currentOwner}
                            </Badge>
                        ) : (
                            <Badge variant="secondary" className="text-base py-1.5 px-3 text-muted-foreground bg-muted">
                                소유자 없음 (미매핑)
                            </Badge>
                        )}
                    </div>
                </div>

                <Separator />

                {/* 변경 입력 */}
                <div className="space-y-3">
                    <label className="text-sm font-medium">새 소유자 아이디 (User Name)</label>
                    <div className="flex gap-2">
                        <Input
                            value={targetUser}
                            onChange={(e) => setTargetUser(e.target.value)}
                            placeholder="연결할 스트리머의 ID(user_name) 입력"
                            className="font-mono"
                        />
                    </div>
                    <Alert className="bg-muted border-none text-xs text-muted-foreground py-2">
                        <AlertDescription>
                            대상 유저는 <strong>USER 권한</strong>이어야 하며, 다른 채널을 소유하고 있지 않아야 합니다.
                        </AlertDescription>
                    </Alert>
                </div>
            </CardContent>
            <CardFooter className="bg-destructive/5 border-t border-destructive/10 pt-4">
                <Button
                    variant="destructive"
                    className="w-full font-bold"
                    onClick={handleTransfer}
                    disabled={!targetUser || isPending}
                >
                    {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
                    소유권 이전 실행
                </Button>
            </CardFooter>
        </Card>
    );
}
