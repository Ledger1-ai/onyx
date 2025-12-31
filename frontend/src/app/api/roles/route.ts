
import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import Role, { PERMISSIONS } from '@/models/Role';

// Auto-seed default roles if they don't exist
async function ensureDefaultRoles() {
    const count = await Role.countDocuments();
    if (count === 0) {
        console.log('Seeding default roles...');

        await Role.create({
            name: 'Partner Super Admin',
            description: 'Full system access with global data visibility.',
            permissions: Object.values(PERMISSIONS), // All permissions including SYSTEM_ACCESS_ALL
            isSystem: true
        });

        await Role.create({
            name: 'Admin',
            description: 'Can manage team resources but limited to own scope.',
            permissions: [
                PERMISSIONS.USERS_READ, PERMISSIONS.USERS_CREATE, PERMISSIONS.USERS_EDIT, PERMISSIONS.USERS_DELETE,
                PERMISSIONS.TEAMS_READ, PERMISSIONS.TEAMS_CREATE, PERMISSIONS.TEAMS_EDIT, PERMISSIONS.TEAMS_DELETE
                // No SYSTEM_ACCESS_ALL, No ROLES_MANAGE by default (can be added)
            ],
            isSystem: true
        });

        await Role.create({
            name: 'User',
            description: 'Standard access.',
            permissions: [
                PERMISSIONS.USERS_READ, // Can view directory
                PERMISSIONS.TEAMS_READ
            ],
            isSystem: true
        });
    }
}

export async function GET() {
    try {
        await connectDB();
        await ensureDefaultRoles();

        const roles = await Role.find({}).sort({ createdAt: 1 });
        return NextResponse.json({ success: true, roles, permissions: PERMISSIONS });
    } catch (error: any) {
        return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
}

export async function POST(req: Request) {
    try {
        await connectDB();
        const body = await req.json();

        // Prevent duplicate names
        const exists = await Role.findOne({ name: body.name });
        if (exists) return NextResponse.json({ success: false, error: 'Role name already exists' }, { status: 400 });

        const newRole = await Role.create({
            name: body.name,
            description: body.description,
            permissions: body.permissions || [],
            isSystem: false
        });

        return NextResponse.json({ success: true, role: newRole });
    } catch (error: any) {
        return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
}

export async function PUT(req: Request) {
    try {
        await connectDB();
        const body = await req.json();
        const { id, name, description, permissions } = body;

        const role = await Role.findById(id);
        if (!role) return NextResponse.json({ success: false, error: 'Role not found' }, { status: 404 });

        // If system role, prevent changing name (optional, but good for consistency)
        // But allow changing permissions as requested by user ("manage the permissions of what the roles can do")

        role.name = name; // Allow rename if needed, or restrict
        role.description = description;
        role.permissions = permissions;
        await role.save();

        return NextResponse.json({ success: true, role });
    } catch (error: any) {
        return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
}

export async function DELETE(req: Request) {
    try {
        await connectDB();
        const { searchParams } = new URL(req.url);
        const id = searchParams.get('id');

        const role = await Role.findById(id);
        if (!role) return NextResponse.json({ success: false, error: 'Role not found' }, { status: 404 });

        if (role.isSystem) {
            return NextResponse.json({ success: false, error: 'Cannot delete system roles' }, { status: 403 });
        }

        await Role.findByIdAndDelete(id);
        return NextResponse.json({ success: true, message: 'Role deleted' });
    } catch (error: any) {
        return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
}
