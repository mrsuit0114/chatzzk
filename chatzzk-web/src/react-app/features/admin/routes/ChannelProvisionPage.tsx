import { Button } from "@/components/ui/button";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { StringListInput } from "@/features/users/components/StringListInput";
import { AUTH_DOMAIN, PasswordSchema, PLATFORM_CODE, PlatformCodeSchema, UserIdSchema } from "@shared/constants/service_codes";
import { AlertCircle, Loader2, Save } from "lucide-react";
import { Controller, useForm } from "react-hook-form";
import z from "zod";
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from "sonner";
import { useMutation } from "@tanstack/react-query";
import { provisionChannel, ProvisionRequest } from "../api/provision";

// ✅ 백엔드와 동일한 Zod 스키마 정의 (프론트용)
const formSchema = z.object({
    userId: UserIdSchema,
    password: PasswordSchema,
    platform: PlatformCodeSchema,
    channelId: z.string().min(1, "채널 ID를 입력하세요."),
    channelName: z.string().min(1, "채널명을 입력하세요."),

    // ✅ Metadata 구조를 CamelCase로 통일
    metadata: z.object({
        streamerNicknames: z.array(z.string()).default([]),
        fanNicknames: z.array(z.string()).default([]),
        streamerSex: z.enum(["남성", "여성"]),
        additionalInfo: z.array(z.string()).default([]),
    }),
});

export function ChannelProvisionPage() {
    const { mutate: runProvision, isPending } = useMutation({
        mutationFn: provisionChannel,
        onSuccess: (result) => {
            toast.success("계정 및 채널 생성이 완료되었습니다!", {
                description: `유저 ID: ${result.data.user.userName} / 채널: ${result.data.channel.channel_name}`
            });
            form.reset(); // 성공 시 폼 초기화
        },
        onError: (error: any) => {
            // Axios Error 객체에서 메시지 추출 (구조에 따라 다를 수 있음)
            const message = error.response?.data?.error || error.message || "알 수 없는 오류가 발생했습니다.";
            toast.error("생성 중 오류가 발생했습니다.", {
                description: message
            });
        }
    });

    const form = useForm({
        resolver: zodResolver(formSchema),
        defaultValues: {
            userId: "",
            password: "",
            platform: PLATFORM_CODE.CHZZK,
            channelId: "",
            channelName: "",
            metadata: {
                streamerNicknames: [], // ✅ CamelCase
                fanNicknames: [],
                streamerSex: "남성",
                additionalInfo: [],
            }
        },
    });

    const onSubmit = (values: z.infer<typeof formSchema>) => {
        if (!confirm(`[${values.channelName}] 채널과 계정을 생성하시겠습니까?`)) return;
        runProvision(values as ProvisionRequest);
    };

    return (
        <div className="space-y-6 max-w-4xl mx-auto pb-20">
            <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tight">통합 프로비저닝</h2>
                <p className="text-muted-foreground">
                    새로운 스트리머를 위한 <strong>계정, 채널, 초기 메타데이터</strong>를 한 번에 생성합니다.
                </p>
            </div>

            <Alert variant="default" className="bg-blue-50 border-blue-200 text-blue-800">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>알림</AlertTitle>
                <AlertDescription>
                    생성 과정 중 하나라도 실패하면(예: 채널 중복) 생성된 계정도 자동으로 롤백(삭제)됩니다.
                </AlertDescription>
            </Alert>

            <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">

                    {/* 1. 유저 & 채널 정보 (Card로 묶음) */}
                    <Card>
                        <CardHeader>
                            <CardTitle>기본 정보 설정</CardTitle>
                            <CardDescription>로그인 계정과 연동될 채널 정보를 입력하세요.</CardDescription>
                        </CardHeader>
                        <CardContent className="grid gap-6">
                            {/* 유저 정보 섹션 */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <FormField
                                    control={form.control}
                                    name="userId"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel htmlFor="user-id">아이디 (User ID)</FormLabel>
                                            <FormControl>
                                                <div className="flex items-center gap-2">
                                                    <Input id="user-id" type="text" placeholder="chimchak_man" {...field} />
                                                    <span className="text-sm text-muted-foreground whitespace-nowrap">
                                                        @{AUTH_DOMAIN}
                                                    </span>
                                                </div>
                                            </FormControl>
                                            <FormDescription>
                                                영문 소문자, 숫자, 언더바(_)만 사용 가능합니다.
                                            </FormDescription>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                                <FormField
                                    control={form.control}
                                    name="password"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>비밀번호</FormLabel>
                                            <FormControl><Input type="password" {...field} /></FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            </div>

                            <Separator />

                            {/* 채널 정보 섹션 */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <FormField
                                    control={form.control}
                                    name="platform"
                                    render={({ field }) => (
                                        <FormItem>
                                            <FormLabel>플랫폼</FormLabel>
                                            <Select onValueChange={field.onChange} value={field.value}>
                                                <FormControl>
                                                    <SelectTrigger><SelectValue placeholder="플랫폼 선택" /></SelectTrigger>
                                                </FormControl>
                                                <SelectContent>
                                                    <SelectItem value={PLATFORM_CODE.CHZZK}>치지직 (CHZZK)</SelectItem>
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
                                            <FormLabel>채널 고유 ID (Hash)</FormLabel>
                                            <FormControl><Input placeholder="네이버 채널 해시값 입력" {...field} /></FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                                <FormField
                                    control={form.control}
                                    name="channelName"
                                    render={({ field }) => (
                                        <FormItem className="col-span-1 md:col-span-2">
                                            <FormLabel>채널명 (표시 이름)</FormLabel>
                                            <FormControl><Input placeholder="침착맨" {...field} /></FormControl>
                                            <FormMessage />
                                        </FormItem>
                                    )}
                                />
                            </div>
                        </CardContent>
                    </Card>

                    {/* 2. 메타데이터 섹션 (기존 StringListInput 활용) */}
                    <Card>
                        <CardHeader>
                            <CardTitle>초기 메타데이터 구성</CardTitle>
                            <CardDescription>AI 분석을 위한 기초 데이터를 설정합니다. (나중에 수정 가능)</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">

                            {/* 성별 선택 */}
                            <FormField
                                control={form.control}
                                name="metadata.streamerSex"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>스트리머 성별</FormLabel>
                                        <Select onValueChange={field.onChange} value={field.value}>
                                            <FormControl>
                                                <SelectTrigger><SelectValue /></SelectTrigger>
                                            </FormControl>
                                            <SelectContent>
                                                <SelectItem value="남성">남성</SelectItem>
                                                <SelectItem value="여성">여성</SelectItem>
                                            </SelectContent>
                                        </Select>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            {/* ✅ StringListInput 재사용 */}
                            <Controller
                                control={form.control}
                                name="metadata.streamerNicknames"
                                render={({ field }) => (
                                    <StringListInput
                                        label="스트리머 호칭 (Aliases)"
                                        description="방송에서 불리는 별명 (엔터로 추가)"
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
                                        label="팬 호칭 (Fan Aliases)"
                                        description="팬덤을 지칭하는 용어 (엔터로 추가)"
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
                                        label="추가 배경 정보"
                                        description="방송 컨셉이나 주요 배경 지식"
                                        items={field.value || []}
                                        onChange={field.onChange}
                                    />
                                )}
                            />
                        </CardContent>
                    </Card>

                    {/* Submit Button */}
                    <Button type="submit" size="lg" className="w-full text-lg font-bold" disabled={isPending}>
                        {isPending ? (
                            <>
                                <Loader2 className="mr-2 h-5 w-5 animate-spin" /> 처리중...
                            </>
                        ) : (
                            <>
                                <Save className="mr-2 h-5 w-5" /> 계정 및 채널 생성 완료
                            </>
                        )}
                    </Button>
                </form>
            </Form>
        </div>
    );
}
