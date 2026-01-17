import { useEffect } from "react";
import { AppRoutes } from "./app/routes";
import { supabase } from "./lib/supabase";
import { useAuthStore } from "./stores/auth.store"; // 경로 확인

function App() {
	const { setSession, clearSession, isInitialized } = useAuthStore();

	useEffect(() => {
		const handleAuth = async (session: any, event: string) => {
			if (session) {
				// ✅ [핵심 해결책] 중복 방지 로직
				// 현재 스토어에 있는 유저 ID와 방금 들어온 세션의 유저 ID가 같다면
				// 이미 처리가 끝난 상태이므로 프로필 Fetch를 수행하지 않습니다.
				// (useAuthStore.getState()를 사용하면 의존성 배열 문제 없이 최신 상태 조회 가능)
				const currentUser = useAuthStore.getState().user;

				if (currentUser?.id === session.user.id) {
					return;
				}

				setSession(session);
			} else {
				clearSession();
			}
		};

		const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
			// 이벤트 타입도 함께 넘겨서 디버깅 및 처리
			handleAuth(session, event);
		});

		return () => subscription.unsubscribe();
	}, []); // 빈 배열: 마운트 시 1회만 구독 설정

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
