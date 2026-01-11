import { useState } from 'react';
import { supabase } from '@/lib/supabase';
import { useNavigate, useLocation } from 'react-router-dom';
import { AUTH_DOMAIN, ID_REGEX } from '@shared/constant';

export const LoginPage = () => {
    const navigate = useNavigate();
    const location = useLocation();

    // 로그인 후 이동할 페이지 (기본값: 홈)
    const from = location.state?.from?.pathname || '/';

    // 1. 입력값 관리 (이메일, 비번)
    const [userName, setUserName] = useState('');
    const [password, setPassword] = useState('');

    // 2. 현재 모드 (true면 회원가입 화면, false면 로그인 화면)
    const [isSignUpMode, setIsSignUpMode] = useState(false);

    // 3. 에러 메시지 관리
    const [errorMsg, setErrorMsg] = useState('');
    const [loading, setLoading] = useState(false);

    // 통합 처리 함수
    const handleAuth = async (e: React.FormEvent) => {
        e.preventDefault(); // 폼 제출 시 새로고침 방지
        setLoading(true);
        setErrorMsg('');

        if (!ID_REGEX.test(userName)) {
            setErrorMsg('아이디는 영문 소문자와 숫자만 사용할 수 있습니다.');
            setLoading(false);
            return;
        }

        try {
            if (isSignUpMode) {
                const { error } = await supabase.auth.signUp({
                    email: `${userName.trim()}${AUTH_DOMAIN}`,
                    password,
                    options: {
                        data: {
                            user_name: userName.trim(),
                        },
                    },
                });
                if (error) throw error;

                alert('회원가입 성공! (이메일 확인이 필요할 수 있습니다)');
            } else {
                const { error } = await supabase.auth.signInWithPassword({
                    email: `${userName.trim()}${AUTH_DOMAIN}`,
                    password,
                });
                if (error) throw error;

                // 로그인 성공 시 페이지 이동 (App.tsx 감지기가 상태 업데이트 함)
                navigate(from, { replace: true });
            }
        } catch (error: any) {
            setErrorMsg(error.message || '오류가 발생했습니다.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50">
            <div className="w-full max-w-md bg-white p-8 rounded-lg shadow-md">
                <h2 className="text-2xl font-bold text-center mb-6">
                    {isSignUpMode ? '회원가입' : '로그인'}
                </h2>

                <form onSubmit={handleAuth} className="flex flex-col gap-4">
                    {/* 이메일 입력 */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700">아이디</label>
                        <input
                            type="text"
                            required
                            className="mt-1 w-full p-2 border rounded-md"
                            value={userName}
                            onChange={(e) => setUserName(e.target.value)}
                        />
                    </div>

                    {/* 비밀번호 입력 */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700">비밀번호</label>
                        <input
                            type="password"
                            required
                            minLength={6}
                            className="mt-1 w-full p-2 border rounded-md"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>

                    {errorMsg && <div className="text-red-500 text-sm text-center">{errorMsg}</div>}

                    {/* 제출 버튼 */}
                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
                    >
                        {loading ? '처리 중...' : (isSignUpMode ? '가입하기' : '로그인')}
                    </button>
                </form>

                {/* 모드 전환 버튼 */}
                <div className="mt-4 text-center text-sm">
                    <span className="text-gray-600">
                        {isSignUpMode ? '이미 계정이 있으신가요?' : '계정이 없으신가요?'}
                    </span>
                    <button
                        onClick={() => {
                            setIsSignUpMode(!isSignUpMode);
                            setErrorMsg('');
                        }}
                        className="ml-2 text-blue-600 hover:underline font-medium"
                    >
                        {isSignUpMode ? '로그인하기' : '회원가입하기'}
                    </button>
                </div>
            </div>
        </div>
    );
};
