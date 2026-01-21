import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { sentryVitePlugin } from "@sentry/vite-plugin";

export default defineConfig(({ mode }) => {
	// 3. 현재 모드(development/production)에 맞는 .env 파일을 강제로 읽어옵니다.
	// process.cwd()는 프로젝트 루트 경로입니다.
	const env = loadEnv(mode, process.cwd(), '');

	return {
		plugins: [
			react(),
			sentryVitePlugin({
				org: "chatzzk",
				project: "chatzzk-frontend",

				// 4. process.env 대신 위에서 로드한 env 변수를 사용합니다.
				authToken: env.SENTRY_AUTH_TOKEN,
			}),
		],
		resolve: {
			alias: {
				"@": path.resolve(__dirname, "src/react-app"),
				"@shared": path.resolve(__dirname, "src/shared"),
			}
		},
		server: {
			proxy: {
				'/api': {
					target: 'http://127.0.0.1:8787',
					changeOrigin: true,
					secure: false,
				}
			}
		},
		build: {
			outDir: 'dist',
			emptyOutDir: true,
			sourcemap: mode === 'development' ? true : 'hidden', // process.env.NODE_ENV 대신 mode 사용 가능
		}
	};
});
