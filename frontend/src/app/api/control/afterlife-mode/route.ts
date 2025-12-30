import { NextResponse } from 'next/server';
import { redisConnection } from '@/lib/queue';

const REDIS_KEY = 'afterlife:mode';

export async function GET() {
    try {
        const isEnabled = await redisConnection.get(REDIS_KEY);
        return NextResponse.json({
            status: 'success',
            enabled: isEnabled === 'true'
        });
    } catch (error) {
        return NextResponse.json({ error: 'Failed to fetch status' }, { status: 500 });
    }
}

export async function POST() {
    try {
        // Toggle the value directly in Redis
        const currentValue = await redisConnection.get(REDIS_KEY);
        const newValue = currentValue === 'true' ? 'false' : 'true';

        await redisConnection.set(REDIS_KEY, newValue);

        // Optional: If enabling afterlife mode actually starts a heavy process,
        // we might still want to queue a 'start-afterlife-loop' job here.
        // But for the "toggle switch" UI, immediate feedback is better.

        return NextResponse.json({
            success: true,
            message: `Afterlife mode ${newValue === 'true' ? 'enabled' : 'disabled'}`,
            enabled: newValue === 'true'
        });
    } catch (error) {
        return NextResponse.json({ error: 'Failed to toggle afterlife mode' }, { status: 500 });
    }
}
