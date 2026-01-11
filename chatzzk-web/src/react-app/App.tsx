import { useEffect } from "react";
import { AppRoutes } from "./app/routes";
import { supabase } from "./lib/supabase";
import { useAuthStore } from "./stores";


function App() {
	// 1. Store에서 필요한 함수와 상태를 가져옵니다.
	const { setSession, isInitialized } = useAuthStore();

	useEffect(() => {
		// 2. [앱 시작 시 1회] 현재 세션이 있는지 확인 (새로고침 대응)
		supabase.auth.getSession().then(({ data: { session } }) => {
			setSession(session);
		});

		// 3. [실시간 감지] 로그인/로그아웃 이벤트가 발생하면 즉시 Store 업데이트
		const {
			data: { subscription },
		} = supabase.auth.onAuthStateChange((_event, session) => {
			setSession(session);
		});

		// 4. [청소] 앱이 꺼질 때 감지기 해제 (메모리 누수 방지)
		return () => subscription.unsubscribe();
	}, [setSession]);

	// 5. [로딩 처리] 아직 Supabase 확인이 안 끝났으면, 하얀 화면이나 로딩바를 보여줌
	// (이게 없으면 로그인 상태인데 로그인 페이지가 번쩍! 하고 보이는 현상이 생김)
	if (!isInitialized) {
		return (
			<div className="flex h-screen w-full items-center justify-center">
				<div className="text-xl font-bold animate-pulse">Loading...</div>
			</div>
		);
	}

	// 6. 초기화가 끝나면 실제 라우터 렌더링
	return (
		<>
			<AppRoutes />
		</>
	);
}

export default App;
