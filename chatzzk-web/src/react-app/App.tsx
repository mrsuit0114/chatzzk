import { AppRoutes } from "./app/routes";
import { useAuthInit } from "./hooks/useAuthInit";

function App() {
	const { isInitialized } = useAuthInit();

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
