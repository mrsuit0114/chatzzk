import { useEffect } from "react";
import { AppRoutes } from "./app/routes";
import { supabase } from "./lib/supabase";
import { useAuthStore } from "./stores/auth.store"; // 경로 확인

function App() {
	// fetchUserProfile 추가
	const { setSession, fetchUserProfile, clearSession, isInitialized } = useAuthStore();

	useEffect(() => {
		const handleAuth = async (session: any) => {
			if (session) {
				setSession(session);
				await fetchUserProfile(); // ✅ 로그인 시 프로필 로드
			} else {
				clearSession();
			}
		};

		// 1. 초기 로드
		supabase.auth.getSession().then(({ data: { session } }) => {
			handleAuth(session);
		});

		// 2. 이벤트 리스너
		const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
			// 이벤트 발생 시 로직 수행
			handleAuth(session);
		});

		return () => subscription.unsubscribe();
	}, []); // ✅ 빈 배열: 마운트 시 1회만 실행 (안정성 확보)

	if (!isInitialized) {
		return (
			<div className="flex h-screen w-full items-center justify-center">
				<div className="text-xl font-bold animate-pulse">Loading...</div>
			</div>
		);
	}

	return <AppRoutes />;
}

export default App;
