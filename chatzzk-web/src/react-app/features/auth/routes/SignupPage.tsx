import { useState } from 'react';
import { supabase } from '@/lib/supabase';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { AUTH_DOMAIN, CONTACT_EMAIL, PasswordSchema, UserIdSchema } from '@shared/constants/service_codes';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Loader2, UserPlus, AlertTriangle, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

// 유효성 검사 스키마
const signUpSchema = z.object({
    userName: UserIdSchema,
    password: PasswordSchema,
    confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
    message: "비밀번호가 일치하지 않습니다.",
    path: ["confirmPassword"],
});

type SignUpValues = z.infer<typeof signUpSchema>;

export const SignUpPage = () => {
    const navigate = useNavigate();
    const [isPending, setIsPending] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    const form = useForm<SignUpValues>({
        resolver: zodResolver(signUpSchema),
        defaultValues: {
            userName: "",
            password: "",
            confirmPassword: ""
        }
    });

    const onSubmit = async (values: SignUpValues) => {
        setIsPending(true);
        try {
            // 1. Supabase 회원가입 요청
            const { data, error } = await supabase.auth.signUp({
                email: `${values.userName}@${AUTH_DOMAIN}`,
                password: values.password,
            });

            if (error) throw error;

            if (data.user) {
                toast.success("계정이 생성되었습니다!");
                navigate('/');
            }
        } catch (error: any) {
            console.error(error);
            toast.error("회원가입 실패", {
                description: error.message || "이미 사용 중인 아이디이거나 오류가 발생했습니다."
            });
        } finally {
            setIsPending(false);
        }
    };

    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-muted/30 px-4 py-12 sm:px-6 lg:px-8 animate-in fade-in duration-500">
            <Link to="/" className="mb-8 flex flex-col items-center gap-2 group cursor-pointer">
                <span className="text-4xl font-extrabold tracking-tighter text-foreground transition-colors group-hover:text-primary">
                    CHATZZK
                </span>
            </Link>

            <Card className="w-full max-w-md shadow-lg border-border/60">
                <CardHeader className="text-center space-y-2">
                    <CardTitle className="text-2xl font-bold tracking-tight">
                        스트리머 회원가입
                    </CardTitle>
                    <CardDescription>
                        채널 분석 서비스를 이용하기 위한 계정을 생성합니다.
                    </CardDescription>
                </CardHeader>

                <CardContent className="space-y-6">
                    {/* 경고/안내 문구 */}
                    <Alert className="bg-yellow-50 text-yellow-900 border-yellow-200">
                        <AlertTriangle className="h-4 w-4 text-yellow-700" />
                        <AlertTitle className="font-bold">일반 시청자 가입 제한</AlertTitle>
                        <AlertDescription className="text-xs mt-1 leading-relaxed">
                            이 서비스는 <strong>사전 협의 된 스트리머 전용</strong>입니다.<br />
                            일반 사용자의 가입 시 사전 통보 없이 계정이 삭제될 수 있습니다.<br />
                            서비스 사용을 희망하는 스트리머는 이메일로 문의해 주세요.<br />
                            문의: {CONTACT_EMAIL}
                        </AlertDescription>
                    </Alert>

                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                            <FormField
                                control={form.control}
                                name="userName"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>아이디</FormLabel>
                                        <FormControl>
                                            <div className="flex items-center gap-2">
                                                <Input placeholder="영문 소문자, 숫자 4자 이상 입력" {...field} />
                                                <span className="text-xs text-muted-foreground whitespace-nowrap"></span>
                                            </div>
                                        </FormControl>
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
                                        <FormControl>
                                            <div className="relative">
                                                <Input
                                                    type={showPassword ? "text" : "password"} // ✅ 상태에 따라 type 변경
                                                    placeholder="8자 이상 입력"
                                                    className="pr-10" // ✅ 아이콘 공간 확보
                                                    {...field}
                                                />
                                                <button
                                                    type="button" // ✅ submit 방지 필수
                                                    onClick={() => setShowPassword(!showPassword)}
                                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                                                    tabIndex={-1}
                                                >
                                                    {showPassword ? (
                                                        <EyeOff className="h-4 w-4" />
                                                    ) : (
                                                        <Eye className="h-4 w-4" />
                                                    )}
                                                </button>
                                            </div>
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <FormField
                                control={form.control}
                                name="confirmPassword"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>비밀번호 확인</FormLabel>
                                        <FormControl>
                                            <Input type="password" placeholder="비밀번호 재입력" {...field} />
                                        </FormControl>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />

                            <Button type="submit" className="w-full font-bold mt-2" size="lg" disabled={isPending}>
                                {isPending ? (
                                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> 가입 중...</>
                                ) : (
                                    <><UserPlus className="mr-2 h-4 w-4" /> 계정 생성하기</>
                                )}
                            </Button>
                        </form>
                    </Form>
                </CardContent>

                <CardFooter className="flex justify-center border-t pt-6 bg-muted/20 rounded-b-xl">
                    <p className="text-sm text-muted-foreground">
                        이미 계정이 있으신가요?{" "}
                        <Link to="/login" className="font-semibold text-primary hover:underline">
                            로그인하기
                        </Link>
                    </p>
                </CardFooter>
            </Card>
        </div>
    );
};
