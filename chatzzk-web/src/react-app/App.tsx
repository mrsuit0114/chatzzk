import './index.css'; // Tailwind가 적용된 CSS 파일 import
import { UserList } from './features/users/components/UserList';

function App() {
	return (
		// min-h-screen: 화면 꽉 채우기, bg-gray-50: 아주 연한 회색 배경
		<div className="min-h-screen bg-gray-50 p-8">
			<header className="max-w-2xl mx-auto mb-8 text-center">
				<h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
					Chatzzk Admin
				</h1>
				<p className="text-gray-500 mt-2">Cloudflare + React + Tailwind 대시보드</p>
			</header>
			<main>
				<UserList />
			</main>
		</div>
	)
}

export default App
