import { NextResponse } from 'next/server';
import { redisConnection } from '@/lib/queue';

export async function POST() {
    try {
        // Disable the Scheduler
        await redisConnection.set('dispatcher:active', 'false');

        return NextResponse.json({
            success: true,
            message: 'Agent stopped and dispatcher paused'
        });
    } catch (error) {
        return NextResponse.json({ error: 'Failed to stop agent' }, { status: 500 });
    }
}
