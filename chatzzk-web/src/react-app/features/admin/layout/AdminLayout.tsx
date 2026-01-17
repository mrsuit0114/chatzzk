import { Outlet } from "react-router-dom";

export function AdminLayout() {

    return (
        <div className="min-h-screen flex bg-gray-100">
            {/* 사이드바 (간단 버전) */}
            <aside className="w-64 bg-white border-r p-6 space-y-4">
                <h1 className="text-xl font-bold text-primary mb-6">Admin Console</h1>
                <nav className="flex flex-col space-y-2">
                    <a href="/admin/provision" className="p-2 hover:bg-gray-100 rounded font-medium">
                        🆕 채널/유저 등록
                    </a>
                    {/* 추후 추가될 메뉴들 */}
                    <a href="/admin/channels" className="p-2 hover:bg-gray-100 rounded text-gray-500">
                        📋 채널 목록 (준비중)
                    </a>
                    <a href="/admin/vods" className="p-2 hover:bg-gray-100 rounded text-gray-500">
                        📺 VOD 관리 (준비중)
                    </a>
                </nav>
            </aside>

            {/* 메인 컨텐츠 */}
            <main className="flex-1 p-8 overflow-y-auto">
                <div className="max-w-4xl mx-auto bg-white p-8 rounded-lg shadow-sm">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
