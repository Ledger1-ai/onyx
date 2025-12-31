
import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import User from '@/models/User';

// Helper for temporary "hashing" (identity function for now, replace with bcrypt later)
const hashPassword = (pwd: string) => pwd;

import { getCurrentUser, hasPermission } from '@/lib/auth';
import { PERMISSIONS } from '@/models/Role';

export async function GET() {
    try {
        await connectDB();

        const currentUser = await getCurrentUser();
        if (!currentUser) {
            return NextResponse.json({ success: false, error: 'Unauthorized' }, { status: 401 });
        }

        let query = {};
        // If user does NOT have global access, restrict to their team
        if (!hasPermission(currentUser, PERMISSIONS.SYSTEM_ACCESS_ALL)) {
            if (!currentUser.teamId) {
                // If user has no team and no global access, they see nothing (or just themselves?)
                // Let's assume they see nothing or just themselves. Safest is empty list or their own profile.
                // For now, let's allow them to see themselves at minimum.
                query = { _id: currentUser._id };
            } else {
                query = { teamId: currentUser.teamId };
            }
        }

        const users = await User.find(query, { passwordHash: 0 }).sort({ createdAt: -1 });
        return NextResponse.json({ success: true, users });
    } catch (error) {
        console.error(error);
        return NextResponse.json({ success: false, error: 'Failed to fetch users' }, { status: 500 });
    }
}

export async function POST(req: Request) {
    try {
        await connectDB();
        const body = await req.json();
        const { email, password, name, role, teamId } = body;

        if (!email || !password || !name) {
            return NextResponse.json({ success: false, error: 'Missing fields' }, { status: 400 });
        }

        const existing = await User.findOne({ email });
        if (existing) {
            return NextResponse.json({ success: false, error: 'User already exists' }, { status: 400 });
        }

        const newUser = await User.create({
            email,
            passwordHash: await hashPassword(password),
            name,
            role: role || 'user',
            teamId: teamId || null
        });

        return NextResponse.json({ success: true, user: { id: newUser._id, email: newUser.email, name: newUser.name, role: newUser.role, teamId: newUser.teamId } });

    } catch (error: any) {
        return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
}

export async function PUT(req: Request) {
    try {
        await connectDB();
        const body = await req.json();
        const { id, email, password, name, role, teamId } = body;

        if (!id) {
            return NextResponse.json({ success: false, error: 'User ID required' }, { status: 400 });
        }

        const currentUser = await getCurrentUser();
        if (!currentUser) return NextResponse.json({ success: false, error: 'Unauthorized' }, { status: 401 });

        // Check Permissions:
        // 1. Has 'users:edit' permission?
        // 2. OR is editing their own profile?
        const canEditOthers = hasPermission(currentUser, PERMISSIONS.USERS_EDIT);
        const isSelf = currentUser._id.toString() === id;

        if (!canEditOthers && !isSelf) {
            return NextResponse.json({ success: false, error: 'Insufficient permissions' }, { status: 403 });
        }

        // If self-edit (and not admin), restrict what can be changed?
        // For now, we trust the UI to send correct fields, but backend should ideally prevent changing Role/Team if not admin.
        // Let's implement that restriction:
        // If !canEditOthers, prevent changing Role or Team
        if (!canEditOthers) {
            if (role && role !== currentUser.role) { // Note: currentUser.role is ObjectId string, body.role is Role ID
                // Ideally check if actually changing. For now just ignore it or error.
                return NextResponse.json({ success: false, error: 'Cannot change own role' }, { status: 403 });
            }
            if (teamId && teamId !== currentUser.teamId) {
                return NextResponse.json({ success: false, error: 'Cannot change own team' }, { status: 403 });
            }
        }

        const updateData: any = { name, email, role, teamId: teamId || null };
        if (password) {
            updateData.passwordHash = await hashPassword(password);
        }

        const updatedUser = await User.findByIdAndUpdate(
            id,
            updateData,
            { new: true }
        );

        if (!updatedUser) {
            return NextResponse.json({ success: false, error: 'User not found' }, { status: 404 });
        }

        return NextResponse.json({ success: true, user: updatedUser });

    } catch (error: any) {
        return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
}

export async function DELETE(req: Request) {
    try {
        await connectDB();
        const { searchParams } = new URL(req.url);
        const id = searchParams.get('id');

        if (!id) {
            return NextResponse.json({ success: false, error: 'User ID required' }, { status: 400 });
        }

        const deletedUser = await User.findByIdAndDelete(id);

        if (!deletedUser) {
            return NextResponse.json({ success: false, error: 'User not found' }, { status: 404 });
        }

        return NextResponse.json({ success: true, message: 'User deleted' });

    } catch (error: any) {
        return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
}
