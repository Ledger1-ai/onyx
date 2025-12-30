import { NextResponse } from 'next/server';
import { redisConnection } from '@/lib/queue';

export const dynamic = 'force-dynamic';

export async function GET() {
    let dbStatus = false;
    let workerStatus = false;
    let activeMode = 'standard';

    try {
        // Check Redis
        const pong = await redisConnection.ping();
        if (pong === 'PONG') {
            dbStatus = true;

            // Check Worker Heartbeat
            const lastHeartbeat = await redisConnection.get('worker:heartbeat');
            if (lastHeartbeat) {
                const diff = Date.now() - parseInt(lastHeartbeat);
                if (diff < 30000) {
                    workerStatus = true;
                }
            }

            // Check Afterlife Mode
            const afterlifeEnabled = await redisConnection.get('afterlife:mode');
            if (afterlifeEnabled === 'true') {
                activeMode = 'afterlife';
            }
        }
    } catch (e) {
        console.error('Status check failed:', e);
    }

    return NextResponse.json({
        database: dbStatus,
        worker: workerStatus,
        active_mode: activeMode,
        daily_progress: 0.45, // Placeholder metric
        completed_activities: 12,
        total_activities: 45
    });
}
