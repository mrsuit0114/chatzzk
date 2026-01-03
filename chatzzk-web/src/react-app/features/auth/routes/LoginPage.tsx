import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, LogIn } from "lucide-react";
import { useAuthStore } from "@/lib/stores";
import { PLATFORM_CODE, UserRole } from "@/types";

export function LoginPage() {
    const navigate = useNavigate();
    const login = useAuthStore((state) => state.login); // Store 액션 가져오기

    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // 이메일 -> 아이디(username)으로 변경
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            await new Promise((resolve) => setTimeout(resolve, 800));

            // ✅ [테스트 로직] 아이디가 'editor'로 시작하면 편집자로 간주
            const role: UserRole = username.startsWith("editor")
                ? "editor"
                : "owner";

            // 스토어 업데이트
            login({
                id: username,
                role: role,
                channelName: "테스트 채널", // 테스트용 빈 문자열
                platform: PLATFORM_CODE.CHZZK, // 기본 플랫폼 설정
                platformChannelUrl: "#", // 테스트용 빈 문자열
            });

            // 메인으로 이동
            navigate("/");
        } catch (err) {
            setError("아이디 또는 비밀번호가 일치하지 않습니다.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-muted/40 px-4">
            <Card className="w-full max-w-sm border-none shadow-lg">
                <CardHeader className="space-y-1 text-center">
                    <CardTitle className="text-2xl font-bold">로그인</CardTitle>
                    <CardDescription>
                        테스트 팁: 'editor'로 시작하는 ID를 입력하면 편집자 권한으로 로그인됩니다.
                    </CardDescription>
                </CardHeader>

                <form onSubmit={handleLogin}>
                    <CardContent className="grid gap-4">
                        {error && (
                            <div className="text-sm text-red-500 bg-red-50 p-2 rounded text-center">
                                {error}
                            </div>
                        )}

                        {/* ✅ 아이디 입력 필드로 변경 */}
                        <div className="grid gap-2">
                            <Label htmlFor="username">아이디</Label>
                            <Input
                                id="username"
                                type="text"
                                placeholder="아이디를 입력하세요"
                                required
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                disabled={isLoading}
                            />
                        </div>

                        <div className="grid gap-2">
                            <Label htmlFor="password">비밀번호</Label>
                            <Input
                                id="password"
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                disabled={isLoading}
                            />
                        </div>
                    </CardContent>

                    <CardFooter className="flex flex-col gap-4">
                        <Button className="w-full" type="submit" disabled={isLoading}>
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    로그인 중...
                                </>
                            ) : (
                                <>
                                    <LogIn className="mr-2 h-4 w-4" />
                                    로그인
                                </>
                            )}
                        </Button>

                        <div className="text-center text-sm text-muted-foreground">
                            <Link to="/" className="hover:text-primary underline underline-offset-4">
                                메인으로 돌아가기
                            </Link>
                        </div>
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
}
