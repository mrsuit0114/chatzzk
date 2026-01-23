import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Save, Loader2, UserPlus, Info } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";

import { PLATFORM_CODE, PlatformCodeSchema } from "@shared/constants/service_codes";
import { cn } from "@/lib/utils";
import { StringListInput } from "@/features/users/components/StringListInput";
import { addChannel } from "../api/channel";

const ChannelMetadataFormShape = z.object({
    streamerNicknames: z.array(z.string()).default([]),
    streamerSex: z.enum(["남성", "여성"]).default("남성"),
    fanNicknames: z.array(z.string()).default([]),
    additionalInfo: z.array(z.string()).default([]),
});

const channelAddFormSchema = z.object({
    platform: PlatformCodeSchema,
    channelId: z.string().min(1, "채널 고유 ID를 입력하세요."),
    channelName: z.string().min(1, "채널명을 입력하세요."),
    shouldLinkUser: z.boolean().default(false),
    targetUserName: z.string().optional(),
    metadata: ChannelMetadataFormShape, // transform이 없는 순수 객체 사용
}).refine((data) => {
    if (data.shouldLinkUser && !data.targetUserName) return false;
    return true;
}, {
    message: "연결할 유저의 ID를 입력해야 합니다.",
    path: ["targetUserName"],
});

type ChannelAddValues = z.infer<typeof channelAddFormSchema>

export function ChannelAddPage() {
    const [isPending, setIsPending] = useState(false);

    const form = useForm({
        resolver: zodResolver(channelAddFormSchema),
        defaultValues: {
            platform: PLATFORM_CODE.CHZZK,
            channelId: "",
            channelName: "",
            shouldLinkUser: false,
            targetUserName: "",
            metadata: {
                streamerNicknames: [],
                streamerSex: "남성",
                fanNicknames: [],
                additionalInfo: [],
            }
        }
    });

    const shouldLinkUser = form.watch("shouldLinkUser");

    // --- 2. Mutation (API 호출 시뮬레이션) ---
    const onSubmit = async (values: ChannelAddValues) => {
        if (!confirm(`[${values.channelName}] 채널을 등록하시겠습니까?`)) return;

        setIsPending(true);
        try {
            // TODO: 실제 API 연결 (e.g., await api.post('/admin/channels', values))
            await addChannel(values);
            console.log("Submitting Data:", values);
            toast.success("채널이 성공적으로 등록되었습니다.");
            form.reset();
        } catch (error: any) {
            toast.error("등록 중 오류가 발생했습니다.");
        } finally {
            setIsPending(false);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8 pb-20">
            <div className="space-y-2">
                <h1 className="text-3xl font-bold tracking-tight">새 채널 등록</h1>
                <p className="text-muted-foreground">시스템에 새로운 방송 채널과 초기 메타데이터를 추가합니다.</p>
            </div>

            <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">

                    {/* 섹션 1: 기본 정보 */}
                    <Card>
                        <CardHeader>
                            <CardTitle>채널 기본 정보</CardTitle>
                            <CardDescription>플랫폼 고유 정보와 표시 이름을 설정합니다.</CardDescription>
                        </CardHeader>
                        <CardContent className="grid md:grid-cols-2 gap-6">
                            <FormField
                                control={form.control}
                                name="platform"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>플랫폼</FormLabel>
                                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                                            <FormControl>
                                                <SelectTrigger><SelectValue /></SelectTrigger>
                                            </FormControl>
                                            <SelectContent>
                                                <SelectItem value={PLATFORM_CODE.CHZZK}>치지직</SelectItem>
                                            </SelectContent>
                                        </Select>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="channelId"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>채널 고유 ID</FormLabel>
                                        <FormControl><Input placeholder="URL의 해시값 또는 ID" {...field} /></FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <FormField
                                control={form.control}
                                name="channelName"
                                render={({ field }) => (
                                    <FormItem className="md:col-span-2">
                                        <FormLabel>채널명 (표시 이름)</FormLabel>
                                        <FormControl><Input placeholder="스트리머 활동명 입력" {...field} /></FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                        </CardContent>
                    </Card>

                    {/* 섹션 2: 유저 매핑 (수동) */}
                    <Card className={cn(shouldLinkUser && "border-blue-200 bg-blue-50/30")}>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0">
                            <div className="space-y-1">
                                <CardTitle className="flex items-center gap-2">
                                    <UserPlus className="h-5 w-5" />
                                    유저 매핑 (선택 사항)
                                </CardTitle>
                                <CardDescription>가입된 스트리머 계정과 이 채널을 즉시 연결합니다.</CardDescription>
                            </div>
                            <FormField
                                control={form.control}
                                name="shouldLinkUser"
                                render={({ field }) => (
                                    <Switch checked={field.value} onCheckedChange={field.onChange} />
                                )}
                            />
                        </CardHeader>
                        <CardContent>
                            {shouldLinkUser ? (
                                <FormField
                                    control={form.control}
                                    name="targetUserName"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>스트리머 아이디 (User Name)</FormLabel>
                                            <FormControl>
                                                <Input placeholder="스트리머가 문의 시 제공한 ID 입력" {...field} />
                                            </FormControl>
                                            <FormDescription>
                                                입력한 ID의 유저는 자동으로 <strong>OWNER</strong> 권한으로 승격됩니다.
                                            </FormDescription>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            ) : (
                                <Alert className="bg-background/50">
                                    <Info className="h-4 w-4" />
                                    <AlertDescription>
                                        유저를 연결하지 않고 채널만 등록합니다. 나중에 관리 리스트에서 매핑할 수 있습니다.
                                    </AlertDescription>
                                </Alert>
                            )}
                        </CardContent>
                    </Card>

                    {/* 섹션 3: 초기 메타데이터 */}
                    <Card>
                        <CardHeader>
                            <CardTitle>초기 메타데이터 설정</CardTitle>
                            <CardDescription>AI 분석 시 참조할 기초 데이터를 입력합니다.</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <FormField
                                control={form.control}
                                name="metadata.streamerSex"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>스트리머 성별</FormLabel>
                                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                                            <FormControl>
                                                <SelectTrigger><SelectValue /></SelectTrigger>
                                            </FormControl>
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
                        </CardContent>
                    </Card>

                    <Button type="submit" size="lg" className="w-full text-lg font-bold" disabled={isPending}>
                        {isPending ? (
                            <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> 등록 중...</>
                        ) : (
                            <><Save className="mr-2 h-5 w-5" /> 채널 등록 완료</>
                        )}
                    </Button>
                </form>
            </Form>
        </div>
    );
}
