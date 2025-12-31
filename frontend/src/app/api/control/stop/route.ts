import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import Setting from '@/models/Setting';

export async function POST() {
    try {
        await connectDB();
        // Disable the Scheduler
        await Setting.findOneAndUpdate(
            { key: 'dispatcher:active' },
            { value: 'false' },
            { upsert: true }
        );

        return NextResponse.json({
            success: true,
            message: 'Agent stopped and dispatcher paused'
        });
    } catch (error) {
        return NextResponse.json({ error: 'Failed to stop agent' }, { status: 500 });
    }
}
