import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";


// 2. 기능별 페이지(Routes) 가져오기
// (export const UserPage = ... 로 정의했다고 가정)
import UserPage from "@/features/users/routes/UserPage";
import MainPage from "@/features/main/routes/MainPage";

export const AppRoutes = () => {
    return (
        <BrowserRouter>
            <Routes>
                {/* MainLayout으로 감싸진 라우트 그룹
           이 안에 있는 모든 페이지는 헤더를 공유합니다.
        */}

                {/* 기본 경로(/)로 오면 /users로 리다이렉트 */}
                <Route path="/" element={<MainPage />} />

                {/* ✨ /users 경로에 UserPage 연결 */}
                <Route path="/users" element={<UserPage />} />

                {/* 나중에 채팅 기능이 추가된다면? */}
                {/* <Route path="/chat" element={<ChatPage />} /> */}

                {/* 레이아웃이 없는 페이지 (예: 로그인) */}
                {/* <Route path="/login" element={<LoginPage />} /> */}

            </Routes>
        </BrowserRouter>
    );
};
