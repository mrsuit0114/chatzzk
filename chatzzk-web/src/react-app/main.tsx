import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { QueryClientProvider } from '@tanstack/react-query';
import App from "./App";
import { queryClient } from "./app/provider";


createRoot(document.getElementById('root')!).render(
	// <React.StrictMode> // (이중 요청 방지를 위해 개발 중엔 꺼두셔도 됩니다)
	<QueryClientProvider client={queryClient}>
		<App />
	</QueryClientProvider>
	// </React.StrictMode>,
);
