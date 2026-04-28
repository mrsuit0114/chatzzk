import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { cloudflare } from "@cloudflare/vite-plugin";
import path from "path";
import { sentryVitePlugin } from "@sentry/vite-plugin";
import { visualizer } from "rollup-plugin-visualizer";

export default defineConfig(({ mode }) => {
	const env = loadEnv(mode, process.cwd(), '');
	const isDev = mode === 'development';

	return {
		plugins: [
			react(),
			// dev 전용: Vite + Worker 통합 실행. 빌드에서는 제외 (배포 구조 충돌 방지)
			...(isDev ? [cloudflare()] : []),
			// Sentry 소스맵은 프로덕션 빌드에서만 업로드
			...(!isDev ? [sentryVitePlugin({
				org: "chatzzk",
				project: "chatzzk-frontend",
				authToken: env.SENTRY_AUTH_TOKEN,
			})] : []),
			// 번들 분석은 빌드 시에만 실행
			...(!isDev ? [visualizer({
				filename: './dist/stats.html',
				open: false,
				gzipSize: true,
				brotliSize: true,
			})] : []),
		],
		resolve: {
			alias: {
				"@": path.resolve(__dirname, "src/react-app"),
				"@shared": path.resolve(__dirname, "src/shared"),
			}
		},
		build: {
			outDir: 'dist',
			emptyOutDir: true,
			sourcemap: isDev ? true : 'hidden',
		}
	};
});
