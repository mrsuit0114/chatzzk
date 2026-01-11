import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
	plugins: [
		react(),
	],
	resolve: {
		alias: {
			"@": path.resolve(__dirname, "src/react-app"),
			"@shared": path.resolve(__dirname, "src/shared"),
		}
	},
	// ✅ Proxy 설정 추가 (API 요청만 백엔드로 토스)
	server: {
		proxy: {
			'/api': {
				target: 'http://127.0.0.1:8787', // 백엔드 주소 (Wrangler 기본 포트)
				changeOrigin: true,
				secure: false,
			}
		}
	},
	build: {
		outDir: 'dist',
		emptyOutDir: true,
	}
});
