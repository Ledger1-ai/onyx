import { NextResponse } from 'next/server';
import { taskQueue, redisConnection } from '@/lib/queue';

export async function POST() {
    try {
        // Enable the Scheduler
        await redisConnection.set('dispatcher:active', 'true');

        const job = await taskQueue.add('start-agent', {
            timestamp: new Date().toISOString(),
            triggeredBy: 'user'
        });

        return NextResponse.json({
            success: true,
            message: 'Agent start command queued',
            jobId: job.id
        });
    } catch (error) {
        return NextResponse.json({ error: 'Failed to queue start command' }, { status: 500 });
    }
}
