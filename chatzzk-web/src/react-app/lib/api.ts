// src/react-app/lib/api.ts
import axios from 'axios';
import { supabase } from './supabase';

// 1. Axios 인스턴스 생성 (기본 설정)
export const api = axios.create({
    baseURL: '/api', // Vite Proxy를 타기 위해 앞에 '/api'를 붙임
    headers: {
        'Content-Type': 'application/json',
    },
});

// 2. 요청 인터셉터 (Request Interceptor) 설정
// 요청이 서버로 날아가기 "직전"에 가로채서 로직을 수행합니다.
api.interceptors.request.use(async (config) => {
    // Supabase에서 현재 세션(토큰)을 가져옵니다.
    const { data: { session } } = await supabase.auth.getSession();
    const token = session?.access_token;

    // 토큰이 있다면 헤더에 자동으로 붙여줍니다.
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
}, (error) => {
    return Promise.reject(error);
});

// 3. 응답 인터셉터 (Response Interceptor) 설정
// 서버에서 응답이 온 "직후"에 가로챕니다.
api.interceptors.response.use(
    (response) => {
        // 성공 시 데이터만 반환 (response.data)
        return response;
    },
    (error) => {
        return Promise.reject(error);
    }
);
