import { useState } from 'react';
import { supabase } from '@/lib/supabase';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { AUTH_DOMAIN, ID_REGEX, PASSWORD_MIN_LENGTH } from '@shared/constants/service_codes';

export const LoginPage = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const from = location.state?.from?.pathname || '/';

    const [userName, setUserName] = useState('');
    const [password, setPassword] = useState('');
    const [isSignUpMode, setIsSignUpMode] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');
    const [loading, setLoading] = useState(false);

    // 통합 처리 함수
    const handleAuth = async (e: React.FormEvent) => {
        e.preventDefault(); // 폼 제출 시 새로고침 방지
        setLoading(true);
        setErrorMsg('');

        if (!ID_REGEX.test(userName)) {
            setErrorMsg('아이디는 4~20자의 영문 소문자와 숫자만 사용할 수 있습니다.');
            setLoading(false);
            return;
        }

        // 비밀번호 검사 (회원가입 시 필수, 로그인 시에는 서버가 알아서 체크하므로 길이만 가볍게 확인)
        if (password.length < PASSWORD_MIN_LENGTH) {
            setErrorMsg(`비밀번호는 최소 ${PASSWORD_MIN_LENGTH}자 이상이어야 합니다.`);
            setLoading(false);
            return;
        }

        try {
            if (isSignUpMode) {
                const { data, error } = await supabase.auth.signUp({
                    email: `${userName.trim()}${AUTH_DOMAIN}`,
                    password,
                    options: {
                        data: {
                            user_name: userName.trim(),
                        },
                    },
                });
                if (error) throw error;

                if (data.session) {
                    alert('회원가입 및 로그인이 완료되었습니다!');
                    navigate(from, { replace: true });
                } else {
                    // 이메일 인증이 켜져있다면 세션이 없으므로 알림 표시
                    alert('회원가입 성공! 이메일 인증 후 로그인해주세요.');
                    setIsSignUpMode(false); // 로그인 모드로 전환
                }

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
            // Supabase가 주는 에러 메시지를 한글로 순화
            if (error.message.includes('Password should be')) {
                setErrorMsg('비밀번호 보안 수준이 낮습니다.');
            } else if (error.message.includes('Invalid login credentials')) {
                setErrorMsg('아이디 또는 비밀번호가 일치하지 않습니다.');
            } else if (error.message.includes('User already registered')) {
                setErrorMsg('이미 사용 중인 아이디입니다.');
            } else {
                setErrorMsg(error.message || '오류가 발생했습니다.');
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 p-4">
            <Link to="/" className="mb-8 flex flex-col items-center gap-2 group">
                <span className="text-4xl font-extrabold tracking-tighter text-gray-900 transition-colors group-hover:text-blue-600">
                    CHATZZK
                </span>
                <span className="text-sm text-gray-500">스트리머 데이터 분석 플랫폼</span>
            </Link>
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
                        {isSignUpMode && (
                            <p className="text-xs text-gray-500 mt-1">
                                * 영문 소문자와 숫자 조합, 4~20자
                            </p>
                        )}
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
