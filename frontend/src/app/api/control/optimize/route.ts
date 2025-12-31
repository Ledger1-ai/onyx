import { NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import Job from '@/models/Job';

export async function POST() {
    try {
        await connectDB();
        const job = await Job.create({
            type: 'optimize-strategy',
            data: {
                timestamp: new Date().toISOString()
            },
            status: 'pending'
        });

        return NextResponse.json({
            success: true,
            message: 'Optimization task queued',
            jobId: job._id
        });
    } catch (error) {
        return NextResponse.json({ error: 'Failed to queue optimization' }, { status: 500 });
    }
}
