
import { cookies } from 'next/headers';
import User from '@/models/User';
import Role, { PERMISSIONS } from '@/models/Role';
import { connectDB } from '@/lib/db';

export async function getCurrentUser() {
    try {
        await connectDB();
        const cookieStore = await cookies();
        const token = cookieStore.get('auth_token');

        if (!token) return null;

        const sessionPayload = JSON.parse(Buffer.from(token.value, 'base64').toString('utf-8'));

        // Fetch fresh user data with Role populated
        const user = await User.findById(sessionPayload.id);
        if (!user) return null;

        // Populate Role to get permissions
        // Note: user.role is stored as a String (ObjectId), so we fetch the Role doc manually or via populate if schema allowed ref
        const role = await Role.findById(user.role);

        return {
            ...user.toObject(),
            roleName: role ? role.name : 'Unknown',
            permissions: role ? role.permissions : []
        };
    } catch (error) {
        console.error('Auth Error:', error);
        return null;
    }
}

export function hasPermission(user: any, permission: string): boolean {
    if (!user || !user.permissions) return false;
    return user.permissions.includes(permission) || user.permissions.includes(PERMISSIONS.SYSTEM_ACCESS_ALL);
}
