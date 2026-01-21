import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { QueryClientProvider } from '@tanstack/react-query';
import App from "./App";
import { queryClient } from "./app/provider";
import "@/lib/dayjs";
import * as Sentry from "@sentry/react";

const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

Sentry.init({
	dsn: import.meta.env.VITE_SENTRY_DSN,

	// ✅ 핵심: 현재 환경이 어딘지 Sentry에게 알려줍니다.
	// npm run dev -> 'development'
	// npm run build -> 'production' 으로 자동 설정됩니다.
	environment: import.meta.env.MODE,

	integrations: [
		Sentry.browserTracingIntegration(),
		Sentry.replayIntegration(),
	],

	// ✅ (선택 사항) 로컬 개발(localhost)에서는 아예 Sentry로 에러를 보내지 않기
	// 쿼터 절약에 매우 좋습니다.
	// enabled: import.meta.env.PROD, // production 모드일 때만 true
	enabled: !isLocal,

	tracesSampleRate: import.meta.env.PROD ? 0.1 : 1.0,

	// 2. 세션 리플레이 샘플링 (녹화)
	// 개발: 100%
	// 운영: 에러가 났을 때만 100% 녹화하고, 평소에는 1%만 녹화
	replaysSessionSampleRate: import.meta.env.PROD ? 0.01 : 1.0,
	replaysOnErrorSampleRate: 1.0, // 에러가 났을 때는 100% 녹화 (필수!)
});

createRoot(document.getElementById('root')!).render(
	<StrictMode>
		<QueryClientProvider client={queryClient}>
			<App />
		</QueryClientProvider>
	</StrictMode>,
);
