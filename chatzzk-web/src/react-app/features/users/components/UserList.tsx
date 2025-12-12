import { useEffect, useState } from 'react';
import { User } from '@/features/users/types';
import { Card } from '@/components/ui/card';
import { getUsers } from '@/features/users/api/getUser';

export const UserList = () => {
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        getUsers().then((data) => {
            setUsers(data);
            setLoading(false);
        });
    }, []);

    if (loading) {
        return (
            <div className="flex justify-center items-center py-10">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    return (
        <div className="max-w-2xl mx-auto">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-800">사용자 목록</h2>
                <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                    총 {users.length}명
                </span>
            </div>

            <div className="grid gap-4">
                {users.map((user) => (
                    <Card key={user.id}>
                        <div className="flex justify-between items-center">
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900">{user.name}</h3>
                                <p className="text-gray-500 text-sm">{user.email}</p>
                            </div>

                            {/* 역할에 따라 색상이 다른 뱃지 */}
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${user.role === 'admin'
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-green-100 text-green-800'
                                }`}>
                                {user.role === 'admin' ? '관리자' : '일반 유저'}
                            </span>
                        </div>
                    </Card>
                ))}
            </div>
        </div>
    );
};
