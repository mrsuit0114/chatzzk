// src/react-app/features/users/types/index.ts
export interface User {
    id: string;
    name: string;
    email: string;
    role: 'admin' | 'user';
}
