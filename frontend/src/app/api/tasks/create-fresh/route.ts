import { NextResponse } from 'next/server';
import { redisConnection } from '@/lib/queue';

export async function POST(req: Request) {
    try {
        // Hard Reset
        await redisConnection.del('task:configuration');
        await redisConnection.del('schedule:daily_plan');

        return NextResponse.json({
            success: true,
            message: 'System reset to fresh state. Default configuration loaded.'
        });

    } catch (error) {
        console.error('Error resetting system:', error);
        return NextResponse.json(
            { success: false, error: 'Internal Server Error' },
            { status: 500 }
        );
    }
}
