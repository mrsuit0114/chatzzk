import { User } from '../types';

// 가짜 데이터 (백엔드 완성 전까지 사용)
const MOCK_USERS: User[] = [
    { id: '1', name: '김철수', email: 'kim@example.com', role: 'admin' },
    { id: '2', name: '이영희', email: 'lee@example.com', role: 'user' },
    { id: '3', name: '박민수', email: 'park@example.com', role: 'user' },
];

export const getUsers = async (): Promise<User[]> => {
    // 네트워크 지연 시간 흉내 (0.5초 대기)
    await new Promise((resolve) => setTimeout(resolve, 500));
    return MOCK_USERS;
};
