import { useState } from 'react';
import { supabase } from '@/lib/supabase';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { AUTH_DOMAIN, CONTACT_EMAIL } from '@shared/constants/service_codes';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { EyeOff, Eye, Loader2, LogIn, Mail } from 'lucide-react';
import { Label } from '@/components/ui/label'; // Label 경로 수정 (recharts 아님)

export const LoginPage = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const from = location.state?.from?.pathname || '/';

    const [userName, setUserName] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setErrorMsg('');

        try {
            // 이메일 조합 로그인
            const { error } = await supabase.auth.signInWithPassword({
                email: `${userName.trim()}@${AUTH_DOMAIN}`,
                password,
            });

            if (error) throw error;

            // 성공 시 이동
            navigate(from);

        } catch (error: any) {
            if (error.message.includes('Invalid login credentials')) {
                setErrorMsg('아이디 또는 비밀번호가 일치하지 않습니다.');
            } else {
                setErrorMsg('로그인 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-muted/30 px-4 py-12 sm:px-6 lg:px-8 animate-in fade-in duration-500">
            {/* 1. 로고 영역 */}
            <Link to="/" className="mb-8 flex flex-col items-center gap-2 group cursor-pointer">
                <span className="text-4xl font-extrabold tracking-tighter text-foreground transition-colors group-hover:text-primary">
                    CHATZZK
                </span>
            </Link>

            {/* 2. 로그인 카드 */}
            <Card className="w-full max-w-md shadow-lg border-border/60">
                <CardHeader className="space-y-1 text-center">
                    <CardTitle className="text-2xl font-bold tracking-tight">
                        로그인
                    </CardTitle>
                    <CardDescription>
                        계정 정보를 입력하여 접속하세요.
                    </CardDescription>
                </CardHeader>

                <CardContent>
                    <form onSubmit={handleLogin} className="space-y-4">
                        {/* 아이디 입력 */}
                        <div className="space-y-2">
                            <Label>아이디</Label>
                            <Input
                                id="username"
                                type="text"
                                placeholder="아이디를 입력하세요"
                                value={userName}
                                onChange={(e) => setUserName(e.target.value)}
                                required
                                disabled={loading}
                                autoComplete="username"
                                className={cn(errorMsg ? "border-red-500 focus-visible:ring-red-500" : "")}
                            />
                        </div>

                        {/* 비밀번호 입력 */}
                        <div className="space-y-2">
                            <Label>비밀번호</Label>
                            <div className="relative">
                                <Input
                                    id="password"
                                    type={showPassword ? "text" : "password"}
                                    placeholder="비밀번호를 입력하세요"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    disabled={loading}
                                    autoComplete="current-password"
                                    className="pr-10"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                                    tabIndex={-1}
                                    aria-label={showPassword ? "비밀번호 숨기기" : "비밀번호 보기"}
                                >
                                    {showPassword ? (
                                        <EyeOff className="h-4 w-4" />
                                    ) : (
                                        <Eye className="h-4 w-4" />
                                    )}
                                </button>
                            </div>
                        </div>

                        {/* 에러 메시지 표시 */}
                        {errorMsg && (
                            <div className="text-sm font-medium text-destructive bg-destructive/10 p-3 rounded-md text-center animate-pulse flex items-center justify-center gap-2">
                                {/* 필요하다면 아이콘 추가 가능 */}
                                {errorMsg}
                            </div>
                        )}

                        {/* 로그인 버튼 */}
                        <Button type="submit" className="w-full font-semibold" disabled={loading} size="lg">
                            {loading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    로그인 중...
                                </>
                            ) : (
                                <>
                                    <LogIn className="mr-2 h-4 w-4" /> 로그인
                                </>
                            )}
                        </Button>
                    </form>
                </CardContent>

                {/* 3. 계정 문의 안내 (Footer) */}
                <CardFooter className="flex flex-col gap-4 border-t pt-6 bg-muted/20 rounded-b-xl">
                    <div className="text-center space-y-2 w-full">
                        <p className="text-sm font-medium text-foreground">
                            아직 계정이 없으신가요?
                        </p>
                        <p className="text-xs text-muted-foreground leading-relaxed px-4">
                            본 서비스는 현재 사전 협의된 스트리머와 편집자만 이용할 수 있습니다.<br />
                            이용을 원하신다면 아래 이메일로 문의해주세요.
                        </p>
                        <span className="inline-flex items-center gap-1 text-sm text-primary font-medium">
                            <Mail className="h-4 w-4" />
                            {CONTACT_EMAIL}
                        </span>
                    </div>
                </CardFooter>
            </Card>
        </div>
    );
};
