import { NextResponse } from 'next/server';
import { taskQueue } from '@/lib/queue';

export async function POST() {
    try {
        const job = await taskQueue.add('optimize-strategy', {
            timestamp: new Date().toISOString()
        });

        return NextResponse.json({
            success: true,
            message: 'Optimization task queued',
            jobId: job.id
        });
    } catch (error) {
        return NextResponse.json({ error: 'Failed to queue optimization' }, { status: 500 });
    }
}
