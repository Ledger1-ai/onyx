
import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import Team from '@/models/Team';

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
        if (!hasPermission(currentUser, PERMISSIONS.SYSTEM_ACCESS_ALL)) {
            if (!currentUser.teamId) {
                return NextResponse.json({ success: true, teams: [] }); // No team, no visibility
            } else {
                query = { _id: currentUser.teamId }; // Only see their own team
            }
        }

        const teams = await Team.find(query).sort({ name: 1 });
        return NextResponse.json({ success: true, teams });
    } catch (error) {
        return NextResponse.json({ success: false, error: 'Failed to fetch teams' }, { status: 500 });
    }
}

export async function POST(req: Request) {
    try {
        await connectDB();
        const body = await req.json();
        const { name, description } = body;

        if (!name) {
            return NextResponse.json({ success: false, error: 'Team name is required' }, { status: 400 });
        }

        const existing = await Team.findOne({ name });
        if (existing) {
            return NextResponse.json({ success: false, error: 'Team name taken' }, { status: 400 });
        }

        const newTeam = await Team.create({ name, description });

        return NextResponse.json({ success: true, team: newTeam });

    } catch (error: any) {
        return NextResponse.json({ success: false, error: error.message }, { status: 500 });
    }
}
