import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import Setting from '@/models/Setting';
import Job from '@/models/Job';

export async function POST() {
    try {
        await connectDB();
        // Enable the Scheduler
        await Setting.findOneAndUpdate(
            { key: 'dispatcher:active' },
            { value: 'true' }, // Keeping as string 'true' to match previous logic logic if needed, or boolean true
            { upsert: true }
        );

        const job = await Job.create({
            type: 'start-agent',
            data: {
                timestamp: new Date().toISOString(),
                triggeredBy: 'user'
            },
            status: 'pending'
        });

        return NextResponse.json({
            success: true,
            message: 'Agent start command queued',
            jobId: job._id
        });
    } catch (error) {
        return NextResponse.json({ error: 'Failed to queue start command' }, { status: 500 });
    }
}
